import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import Order, Transaction, Merchant
from app.models.schemas import OrderCreate, PaymentInitiateRequest, CaptureRequest, RefundRequest
from app.services.idempotency import IdempotencyGuard
from app.services.vault import TokenizationService
from app.services.bank_simulator import AcquirerSimulator

# NOTE: fraud_engine and ledger_service and webhook_dispatcher are imported lazily
# inside methods to avoid circular imports


class PaymentEngine:
    """Core payment orchestration engine."""

    # ── ORDER ────────────────────────────────────────────────────────────────

    @staticmethod
    def create_order(
        merchant_id: str,
        payload: OrderCreate,
        idempotency_key: str,
        db: Session
    ) -> dict:
        """
        Create a new payment order.
        Checks idempotency first — if key was used before, returns cached response.
        """
        # Idempotency check
        cached = IdempotencyGuard.check_existing(idempotency_key, db)
        if cached:
            return cached['response']

        # Validate merchant
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        order = Order(
            id=str(uuid.uuid4()),
            merchant_id=merchant_id,
            amount_paise=payload.amount_paise,
            currency=payload.currency,
            status='CREATED',
            customer_email=payload.customer_email,
            idempotency_key=idempotency_key,
            metadata_json=json.dumps(payload.metadata) if payload.metadata else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        try:
            db.add(order)
            db.commit()
            db.refresh(order)
        except Exception:
            db.rollback()
            raise

        response = {
            'id': order.id,
            'merchant_id': order.merchant_id,
            'amount_paise': order.amount_paise,
            'currency': order.currency,
            'status': order.status,
            'customer_email': order.customer_email,
            'created_at': order.created_at.isoformat() + 'Z'
        }
        IdempotencyGuard.store_response(idempotency_key, response, 201, db)
        return response

    # ── INITIATE PAYMENT ─────────────────────────────────────────────────────

    @staticmethod
    def initiate_payment(
        payload: PaymentInitiateRequest,
        db: Session
    ) -> dict:
        """
        Tokenize card, run fraud engine, determine if 3DS is needed.
        Returns: {transaction_id, risk_score, risk_tier, otp_required, otp_code (test only), message}
        """
        from app.services.fraud_engine import SentinelFraudEngine

        order = db.query(Order).filter(Order.id == payload.order_id).first()
        if not order:
            raise ValueError(f"Order {payload.order_id} not found")
        if order.status not in ('CREATED', 'PROCESSING'):
            raise ValueError(f"Order is in non-payable status: {order.status}")

        # Update order status to PROCESSING
        order.status = 'PROCESSING'
        order.updated_at = datetime.utcnow()
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        # Tokenize card
        card_number = '4111111111111111'  # default fallback for non-card methods
        expiry = '12/2027'
        if payload.payment_method == 'card' and payload.card:
            card_number = payload.card.card_number
            expiry = payload.card.card_expiry

        token = TokenizationService.tokenize_card(order.id, card_number, expiry, db)

        # Create transaction record
        txn = Transaction(
            id=str(uuid.uuid4()),
            order_id=order.id,
            status='PROCESSING',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        try:
            db.add(txn)
            db.commit()
            db.refresh(txn)
        except Exception:
            db.rollback()
            raise

        # Run fraud engine
        risk = SentinelFraudEngine.assess(
            transaction_id=txn.id,
            card_token=token,
            ip_address=payload.ip_address or '127.0.0.1',
            order=order,
            db=db
        )

        # Update transaction with risk result
        txn.risk_score = risk['total_score']
        txn.risk_tier = risk['tier']
        txn.risk_details_json = json.dumps(risk)

        if risk['tier'] == 'BLOCK':
            txn.status = 'BLOCKED'
            order.status = 'BLOCKED'
            order.updated_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            return {
                'transaction_id': txn.id,
                'order_id': order.id,
                'risk_score': risk['total_score'],
                'risk_tier': 'BLOCK',
                'otp_required': False,
                'otp_code': None,
                'message': 'Transaction blocked by fraud detection system'
            }

        elif risk['tier'] == 'CHALLENGE':
            txn.status = '3DS_PENDING'
            order.status = '3DS_PENDING'
            order.updated_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            # Generate OTP
            otp = AcquirerSimulator.generate_3ds_otp(txn.id)
            return {
                'transaction_id': txn.id,
                'order_id': order.id,
                'risk_score': risk['total_score'],
                'risk_tier': 'CHALLENGE',
                'otp_required': True,
                'otp_code': otp,  # Test mode: returned directly. Production: sent via SMS
                'message': 'OTP sent to registered mobile number. Please verify to proceed.'
            }

        else:  # ALLOW
            txn.status = 'AUTHORIZED'
            order.status = 'AUTHORIZED'
            order.updated_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            return {
                'transaction_id': txn.id,
                'order_id': order.id,
                'risk_score': risk['total_score'],
                'risk_tier': 'ALLOW',
                'otp_required': False,
                'otp_code': None,
                'message': 'Payment authorized. Call /capture to complete.'
            }

    # ── CAPTURE ───────────────────────────────────────────────────────────────

    @staticmethod
    def capture_payment(transaction_id: str, otp_code: Optional[str], db: Session) -> dict:
        """
        Capture an authorized or 3DS-pending transaction.
        If 3DS pending, validates OTP first.
        Triggers ledger posting and webhook dispatch.
        """
        from app.services.ledger_service import LedgerService
        from app.services.webhook_dispatcher import WebhookDispatcher

        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            raise ValueError(f"Transaction {transaction_id} not found")

        order = db.query(Order).filter(Order.id == txn.order_id).first()
        merchant = db.query(Merchant).filter(Merchant.id == order.merchant_id).first()

        if txn.status == '3DS_PENDING':
            if not otp_code:
                raise ValueError('OTP required for 3DS challenge transactions')
            if not AcquirerSimulator.verify_3ds_otp(transaction_id, otp_code):
                raise ValueError('Invalid or expired OTP')
            txn.status = 'AUTHORIZED'

        if txn.status != 'AUTHORIZED':
            raise ValueError(f"Cannot capture transaction in status: {txn.status}")

        # Call acquirer via Smart Multi-Acquirer Router (with Auto-Cascade fallback)
        from app.services.smart_router import SmartRoutingEngine
        token = db.query(__import__('app.models.models', fromlist=['PaymentToken']).PaymentToken).filter_by(order_id=order.id).first()
        acquirer_result = SmartRoutingEngine.execute_with_auto_cascade(token, order.amount_paise, None, db)

        if not acquirer_result['success']:
            txn.status = 'FAILED'
            txn.acquirer_gateway = acquirer_result.get('routed_gateway', 'HDFC')
            txn.acquirer_response_json = json.dumps(acquirer_result)
            order.status = 'FAILED'
            order.updated_at = datetime.utcnow()
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
            return {'status': 'FAILED', 'message': acquirer_result['message'], 'transaction_id': txn.id}

        # Capture succeeded
        txn.status = 'CAPTURED'
        txn.bank_ref = acquirer_result['bank_ref']
        txn.acquirer_gateway = acquirer_result.get('routed_gateway', 'HDFC')
        txn.acquirer_response_json = json.dumps(acquirer_result)
        txn.captured_at = datetime.utcnow()
        txn.updated_at = datetime.utcnow()
        order.status = 'CAPTURED'
        order.updated_at = datetime.utcnow()

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        # Post to ledger
        LedgerService.post_capture(txn.id, order.amount_paise, db)
        LedgerService.assert_balance(txn.id, db)

        # Enqueue webhook
        webhook_payload = {
            'event': 'payment.captured',
            'transaction_id': txn.id,
            'order_id': order.id,
            'amount_paise': order.amount_paise,
            'bank_ref': txn.bank_ref,
            'captured_at': txn.captured_at.isoformat() + 'Z'
        }
        WebhookDispatcher.enqueue(merchant.id, 'payment.captured', webhook_payload, db)

        return {
            'status': 'CAPTURED',
            'transaction_id': txn.id,
            'order_id': order.id,
            'bank_ref': txn.bank_ref,
            'amount_paise': order.amount_paise,
            'captured_at': txn.captured_at.isoformat() + 'Z',
            'message': 'Payment captured successfully'
        }

    # ── REFUND ────────────────────────────────────────────────────────────────

    @staticmethod
    def refund_payment(transaction_id: str, amount_paise: int, reason: str, db: Session) -> dict:
        """
        Refund a captured transaction (full or partial).
        Creates reversal ledger entries and fires webhook.
        """
        from app.services.ledger_service import LedgerService
        from app.services.webhook_dispatcher import WebhookDispatcher

        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            raise ValueError(f"Transaction {transaction_id} not found")
        if txn.status != 'CAPTURED':
            raise ValueError(f"Can only refund CAPTURED transactions, got: {txn.status}")

        order = db.query(Order).filter(Order.id == txn.order_id).first()
        merchant = db.query(Merchant).filter(Merchant.id == order.merchant_id).first()

        if amount_paise > order.amount_paise:
            raise ValueError(f"Refund amount {amount_paise} exceeds original {order.amount_paise}")

        txn.status = 'REFUNDED'
        txn.refunded_at = datetime.utcnow()
        txn.updated_at = datetime.utcnow()
        order.status = 'REFUNDED'
        order.updated_at = datetime.utcnow()

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        # Post reversal ledger entries
        LedgerService.post_refund(txn.id, amount_paise, db)
        LedgerService.assert_balance(txn.id, db)

        # Enqueue webhook
        webhook_payload = {
            'event': 'payment.refunded',
            'transaction_id': txn.id,
            'order_id': order.id,
            'refund_amount_paise': amount_paise,
            'reason': reason,
            'refunded_at': txn.refunded_at.isoformat() + 'Z'
        }
        WebhookDispatcher.enqueue(merchant.id, 'payment.refunded', webhook_payload, db)

        return {
            'status': 'REFUNDED',
            'transaction_id': txn.id,
            'refund_amount_paise': amount_paise,
            'reason': reason,
            'refunded_at': txn.refunded_at.isoformat() + 'Z',
            'message': 'Refund processed successfully'
        }

    # ── HELPERS ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_transaction(transaction_id: str, db: Session) -> dict:
        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            raise ValueError(f"Transaction {transaction_id} not found")
        return {
            'id': txn.id,
            'order_id': txn.order_id,
            'status': txn.status,
            'risk_score': txn.risk_score,
            'risk_tier': txn.risk_tier,
            'bank_ref': txn.bank_ref,
            'captured_at': txn.captured_at.isoformat() + 'Z' if txn.captured_at else None,
            'refunded_at': txn.refunded_at.isoformat() + 'Z' if txn.refunded_at else None,
            'created_at': txn.created_at.isoformat() + 'Z'
        }

    @staticmethod
    def get_order(order_id: str, db: Session) -> dict:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        txns = db.query(Transaction).filter(Transaction.order_id == order_id).all()
        return {
            'id': order.id,
            'merchant_id': order.merchant_id,
            'amount_paise': order.amount_paise,
            'currency': order.currency,
            'status': order.status,
            'customer_email': order.customer_email,
            'created_at': order.created_at.isoformat() + 'Z',
            'transactions': [{
                'id': t.id, 'status': t.status, 'risk_score': t.risk_score,
                'risk_tier': t.risk_tier, 'bank_ref': t.bank_ref
            } for t in txns]
        }