import uuid
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.models import LedgerEntry, Transaction
from app.core.config import settings


class LedgerService:
    """Double-entry bookkeeping ledger for payment transactions."""

    @staticmethod
    def _create_entry(
        transaction_id: str,
        entry_type: str,  # 'DEBIT' or 'CREDIT'
        account_code: str,
        amount_paise: int,
        description: str,
        db: Session
    ) -> LedgerEntry:
        """Create a single ledger entry row."""
        entry = LedgerEntry(
            id=str(uuid.uuid4()),
            transaction_id=transaction_id,
            entry_type=entry_type,
            account_code=account_code,
            amount_paise=amount_paise,
            description=description,
            created_at=datetime.utcnow()
        )
        db.add(entry)
        return entry

    @staticmethod
    def post_capture(transaction_id: str, amount_paise: int, db: Session) -> List[LedgerEntry]:
        """
        Post double-entry journal for a successful CAPTURE.
        DEBIT  ACQUIRER_CLEARING    amount
        CREDIT MERCHANT_PAYABLE     amount - fee
        CREDIT GATEWAY_FEE_REVENUE  fee
        """
        fee = int(amount_paise * settings.GATEWAY_FEE_PERCENT / 100)
        merchant_net = amount_paise - fee
        
        entries = []
        try:
            entries.append(LedgerService._create_entry(
                transaction_id, 'DEBIT', 'ACQUIRER_CLEARING', amount_paise,
                f'Bank acquirer settlement for txn {transaction_id}', db
            ))
            entries.append(LedgerService._create_entry(
                transaction_id, 'CREDIT', 'MERCHANT_PAYABLE', merchant_net,
                f'Net payable to merchant after {settings.GATEWAY_FEE_PERCENT}% fee', db
            ))
            entries.append(LedgerService._create_entry(
                transaction_id, 'CREDIT', 'GATEWAY_FEE_REVENUE', fee,
                f'Shurokkha processing fee {settings.GATEWAY_FEE_PERCENT}% on {amount_paise} paise', db
            ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        return entries

    @staticmethod
    def post_refund(transaction_id: str, amount_paise: int, db: Session) -> List[LedgerEntry]:
        """
        Post double-entry reversal journal for a REFUND.
        CREDIT ACQUIRER_CLEARING    amount          (money returns to bank)
        DEBIT  MERCHANT_PAYABLE     amount - fee    (reduce merchant payable)
        DEBIT  GATEWAY_FEE_REVENUE  fee             (refund our fee too)
        """
        fee = int(amount_paise * settings.GATEWAY_FEE_PERCENT / 100)
        merchant_net = amount_paise - fee
        
        entries = []
        try:
            entries.append(LedgerService._create_entry(
                transaction_id, 'CREDIT', 'ACQUIRER_CLEARING', amount_paise,
                f'Refund settlement reversal for txn {transaction_id}', db
            ))
            entries.append(LedgerService._create_entry(
                transaction_id, 'DEBIT', 'MERCHANT_PAYABLE', merchant_net,
                f'Reversal of merchant payable for refund', db
            ))
            entries.append(LedgerService._create_entry(
                transaction_id, 'DEBIT', 'GATEWAY_FEE_REVENUE', fee,
                f'Fee refund on returned transaction', db
            ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        return entries

    @staticmethod
    def post_fraud_hold(transaction_id: str, amount_paise: int, db: Session) -> List[LedgerEntry]:
        """
        Post fraud hold journal entries.
        DEBIT  ACQUIRER_CLEARING  amount
        CREDIT FRAUD_HOLD         amount
        """
        entries = []
        try:
            entries.append(LedgerService._create_entry(
                transaction_id, 'DEBIT', 'ACQUIRER_CLEARING', amount_paise,
                f'Fraud hold — funds escrowed pending investigation', db
            ))
            entries.append(LedgerService._create_entry(
                transaction_id, 'CREDIT', 'FRAUD_HOLD', amount_paise,
                f'Fraud hold reserve for txn {transaction_id}', db
            ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        return entries

    @staticmethod
    def assert_balance(transaction_id: str, db: Session) -> bool:
        """
        Verify double-entry integrity for a transaction:
        sum(DEBIT entries) == sum(CREDIT entries)
        Raises ValueError if unbalanced.
        Returns True if balanced.
        """
        entries = db.query(LedgerEntry).filter(
            LedgerEntry.transaction_id == transaction_id
        ).all()
        
        if not entries:
            raise ValueError(f'No ledger entries found for transaction {transaction_id}')
        
        total_debit = sum(e.amount_paise for e in entries if e.entry_type == 'DEBIT')
        total_credit = sum(e.amount_paise for e in entries if e.entry_type == 'CREDIT')
        
        if total_debit != total_credit:
            raise ValueError(
                f'Ledger UNBALANCED for txn {transaction_id}: '
                f'DEBIT={total_debit} paise != CREDIT={total_credit} paise. '
                f'Difference: {abs(total_debit - total_credit)} paise'
            )
        return True

    @staticmethod
    def get_balance_sheet(db: Session) -> dict:
        """
        Aggregate all ledger entries by account code.
        Returns: {account_code: {debit_total, credit_total, net_paise}}
        """
        entries = db.query(LedgerEntry).all()
        accounts = {}
        
        for entry in entries:
            code = entry.account_code
            if code not in accounts:
                accounts[code] = {'debit_total': 0, 'credit_total': 0, 'net_paise': 0}
            if entry.entry_type == 'DEBIT':
                accounts[code]['debit_total'] += entry.amount_paise
            else:
                accounts[code]['credit_total'] += entry.amount_paise
        
        for code, data in accounts.items():
            data['net_paise'] = data['debit_total'] - data['credit_total']
        
        total_debit = sum(a['debit_total'] for a in accounts.values())
        total_credit = sum(a['credit_total'] for a in accounts.values())
        
        return {
            'accounts': accounts,
            'is_balanced': total_debit == total_credit,
            'total_debit_paise': total_debit,
            'total_credit_paise': total_credit
        }

    @staticmethod
    def get_entries_for_transaction(transaction_id: str, db: Session) -> list:
        """Get all ledger entries for a specific transaction."""
        entries = db.query(LedgerEntry).filter(
            LedgerEntry.transaction_id == transaction_id
        ).order_by(LedgerEntry.created_at).all()
        return [{
            'id': e.id,
            'entry_type': e.entry_type,
            'account_code': e.account_code,
            'amount_paise': e.amount_paise,
            'description': e.description,
            'created_at': e.created_at.isoformat() + 'Z'
        } for e in entries]
