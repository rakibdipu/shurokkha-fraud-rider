from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import ReconciliationRunRequest
from app.services.recon_service import ReconciliationEngine

router = APIRouter(prefix='/reconciliation', tags=['Reconciliation'])

@router.post('/run')
def run_reconciliation(
    payload: ReconciliationRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run End-of-Day bank reconciliation.
    Upload bank settlement rows and compare against DB transactions.
    
    Example bank_rows: [{"bank_ref": "BNK-ABC123", "amount_paise": 50000, "date": "2026-09-01"}]
    """
    try:
        return ReconciliationEngine.run_eod_reconciliation(
            payload.settlement_date,
            payload.bank_rows,
            db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Reconciliation failed: {str(e)}')

@router.get('/reports')
def list_reports(limit: int = 20, db: Session = Depends(get_db)):
    """List past reconciliation reports."""
    return ReconciliationEngine.list_reports(db, limit=limit)

@router.get('/reports/{report_id}')
def get_report(report_id: str, db: Session = Depends(get_db)):
    """Get full reconciliation report with discrepancies."""
    try:
        return ReconciliationEngine.get_report(report_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
