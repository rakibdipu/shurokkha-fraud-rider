from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.models import LedgerEntry, Transaction
from app.services.ledger_service import LedgerService

router = APIRouter(prefix='/ledger', tags=['Ledger'])

@router.get('/entries')
def get_ledger_entries(
    transaction_id: Optional[str] = None,
    account_code: Optional[str] = None,
    entry_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Paginated ledger entries with optional filters."""
    query = db.query(LedgerEntry)
    if transaction_id:
        query = query.filter(LedgerEntry.transaction_id == transaction_id)
    if account_code:
        query = query.filter(LedgerEntry.account_code == account_code)
    if entry_type:
        query = query.filter(LedgerEntry.entry_type == entry_type)
    
    entries = query.order_by(LedgerEntry.created_at.desc()).limit(limit).all()
    return [{
        'id': e.id,
        'transaction_id': e.transaction_id,
        'entry_type': e.entry_type,
        'account_code': e.account_code,
        'amount_paise': e.amount_paise,
        'amount_inr': round(e.amount_paise / 100, 2),
        'description': e.description,
        'created_at': e.created_at.isoformat() + 'Z'
    } for e in entries]

@router.get('/balance-sheet')
def get_balance_sheet(db: Session = Depends(get_db)):
    """Aggregated balance sheet by account code. Verifies double-entry integrity."""
    result = LedgerService.get_balance_sheet(db)
    # Add INR conversion
    for code, data in result['accounts'].items():
        data['debit_total_inr'] = round(data['debit_total'] / 100, 2)
        data['credit_total_inr'] = round(data['credit_total'] / 100, 2)
        data['net_inr'] = round(data['net_paise'] / 100, 2)
    return result

@router.get('/assertions')
def run_balance_assertions(db: Session = Depends(get_db)):
    """
    Run double-entry integrity checks on ALL transactions with ledger entries.
    Returns per-transaction balance status.
    """
    from app.models.models import LedgerEntry
    from sqlalchemy import distinct
    
    # Get all unique transaction IDs that have ledger entries
    txn_ids = [row[0] for row in db.query(distinct(LedgerEntry.transaction_id)).all()]
    
    results = []
    for txn_id in txn_ids:
        try:
            LedgerService.assert_balance(txn_id, db)
            results.append({'transaction_id': txn_id, 'balanced': True, 'error': None})
        except ValueError as e:
            results.append({'transaction_id': txn_id, 'balanced': False, 'error': str(e)})
    
    total = len(results)
    balanced = sum(1 for r in results if r['balanced'])
    return {
        'total_checked': total,
        'balanced': balanced,
        'unbalanced': total - balanced,
        'integrity': 'PASS' if balanced == total else 'FAIL',
        'details': results
    }
