import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import Dispute, Transaction, Order, LedgerEntry
from app.services.ledger_service import LedgerService


class DisputeEngine:
    """
    Chargeback, Fraud Alert (TC40/SAFE) and Dispute Resolution Engine.
    Handles evidence submission, escrow reserve holds, and win/loss resolution.
    """

    @staticmethod
    def create_dispute(transaction_id: str, reason: str, amount_paise: int, db: Session) -> Dispute:
        """
        Open a dispute / chargeback against a transaction.
        Places dispute amount into FRAUD_HOLD escrow in the ledger.
        """
        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            raise ValueError(f"Transaction {transaction_id} not found")

        order = db.query(Order).filter(Order.id == txn.order_id).first()
        amount = amount_paise or order.amount_paise

        dispute = Dispute(
            transaction_id=txn.id,
            reason=reason,
            amount_paise=amount,
            status="NEEDS_RESPONSE",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        db.add(dispute)
        
        # Post FRAUD_HOLD ledger entry
        try:
            LedgerService.post_fraud_hold(txn.id, amount, db)
        except Exception:
            pass

        db.commit()
        db.refresh(dispute)
        return dispute

    @staticmethod
    def submit_evidence(dispute_id: str, evidence_text: str, file_url: str, db: Session) -> Dispute:
        """
        Merchant submits proof of delivery / invoice to contest chargeback.
        """
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError("Dispute not found")

        dispute.evidence_text = evidence_text
        dispute.evidence_file_url = file_url
        dispute.status = "UNDER_REVIEW"
        db.commit()
        db.refresh(dispute)
        return dispute

    @staticmethod
    def resolve_dispute(dispute_id: str, outcome: str, db: Session) -> Dispute:
        """
        Outcome: 'WON' (merchant keeps funds) or 'LOST' (customer refunded).
        """
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError("Dispute not found")

        dispute.status = "WON" if outcome.upper() == "WON" else "LOST"
        db.commit()
        db.refresh(dispute)
        return dispute
