import json
import uuid
from datetime import datetime, date
from typing import List
from sqlalchemy.orm import Session

from app.models.models import Transaction, Order, ReconciliationReport


class ReconciliationEngine:
    """Automated End-of-Day bank settlement reconciliation engine."""

    @staticmethod
    def run_eod_reconciliation(
        settlement_date: str,  # YYYY-MM-DD
        bank_rows: List[dict],  # [{bank_ref, amount_paise, date}]
        db: Session
    ) -> dict:
        """
        Compare bank settlement file against CAPTURED transactions in DB.
        
        Bank rows: list of {bank_ref, amount_paise, date}
        DB transactions: CAPTURED transactions where bank_ref is not null
        
        Discrepancy types:
        - MATCHED: bank_ref exists in both, amounts match
        - AMOUNT_MISMATCH: bank_ref matches but amounts differ  
        - MISSING_IN_BANK: transaction in DB but not in bank file
        - EXTRA_IN_BANK: bank row has no matching DB transaction
        
        Returns full reconciliation report dict.
        """
        # Build lookup from bank file
        bank_lookup = {row['bank_ref']: row for row in bank_rows if row.get('bank_ref')}
        
        # Get all CAPTURED transactions for this date
        db_transactions = db.query(Transaction).join(Order).filter(
            Transaction.status == 'CAPTURED',
            Transaction.bank_ref != None
        ).all()
        
        # Filter by date
        if settlement_date:
            db_transactions = [
                t for t in db_transactions
                if t.captured_at and t.captured_at.strftime('%Y-%m-%d') == settlement_date
            ]
        
        db_lookup = {t.bank_ref: t for t in db_transactions}
        
        matched = []
        discrepancies = []
        
        # Check DB transactions against bank file
        for bank_ref, txn in db_lookup.items():
            order = db.query(Order).filter(Order.id == txn.order_id).first()
            db_amount = order.amount_paise if order else 0
            
            if bank_ref in bank_lookup:
                bank_amount = bank_lookup[bank_ref].get('amount_paise', 0)
                if db_amount == bank_amount:
                    matched.append({
                        'bank_ref': bank_ref,
                        'transaction_id': txn.id,
                        'amount_paise': db_amount,
                        'status': 'MATCHED'
                    })
                else:
                    discrepancies.append({
                        'type': 'AMOUNT_MISMATCH',
                        'bank_ref': bank_ref,
                        'transaction_id': txn.id,
                        'db_amount_paise': db_amount,
                        'bank_amount_paise': bank_amount,
                        'gap_paise': abs(db_amount - bank_amount)
                    })
            else:
                discrepancies.append({
                    'type': 'MISSING_IN_BANK',
                    'bank_ref': bank_ref,
                    'transaction_id': txn.id,
                    'db_amount_paise': db_amount,
                    'bank_amount_paise': 0,
                    'gap_paise': db_amount
                })
        
        # Check bank file for extra rows not in DB
        for bank_ref, row in bank_lookup.items():
            if bank_ref not in db_lookup:
                discrepancies.append({
                    'type': 'EXTRA_IN_BANK',
                    'bank_ref': bank_ref,
                    'transaction_id': None,
                    'db_amount_paise': 0,
                    'bank_amount_paise': row.get('amount_paise', 0),
                    'gap_paise': row.get('amount_paise', 0)
                })
        
        report_data = {
            'settlement_date': settlement_date,
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_db_transactions': len(db_lookup),
                'total_bank_rows': len(bank_lookup),
                'matched': len(matched),
                'discrepancies': len(discrepancies)
            },
            'matched': matched,
            'discrepancies': discrepancies
        }
        
        # Save to DB
        report = ReconciliationReport(
            id=str(uuid.uuid4()),
            batch_date=settlement_date,
            total_transactions=len(db_lookup),
            total_matched=len(matched),
            total_discrepancies=len(discrepancies),
            total_missing=sum(1 for d in discrepancies if d['type'] == 'MISSING_IN_BANK'),
            report_json=json.dumps(report_data),
            created_at=datetime.utcnow()
        )
        try:
            db.add(report)
            db.commit()
            db.refresh(report)
        except Exception:
            db.rollback()
            raise
        
        return {
            'id': report.id,
            'batch_date': report.batch_date,
            'total_transactions': report.total_transactions,
            'total_matched': report.total_matched,
            'total_discrepancies': report.total_discrepancies,
            'total_missing': report.total_missing,
            'report': report_data
        }

    @staticmethod
    def get_report(report_id: str, db: Session) -> dict:
        """Retrieve a reconciliation report by ID."""
        report = db.query(ReconciliationReport).filter(ReconciliationReport.id == report_id).first()
        if not report:
            raise ValueError(f'ReconciliationReport {report_id} not found')
        return {
            'id': report.id,
            'batch_date': report.batch_date,
            'total_transactions': report.total_transactions,
            'total_matched': report.total_matched,
            'total_discrepancies': report.total_discrepancies,
            'total_missing': report.total_missing,
            'report': json.loads(report.report_json),
            'created_at': report.created_at.isoformat() + 'Z'
        }

    @staticmethod
    def list_reports(db: Session, limit: int = 20) -> list:
        """List all reconciliation reports, newest first."""
        reports = db.query(ReconciliationReport).order_by(
            ReconciliationReport.created_at.desc()
        ).limit(limit).all()
        return [{
            'id': r.id,
            'batch_date': r.batch_date,
            'total_transactions': r.total_transactions,
            'total_matched': r.total_matched,
            'total_discrepancies': r.total_discrepancies,
            'total_missing': r.total_missing,
            'created_at': r.created_at.isoformat() + 'Z'
        } for r in reports]
