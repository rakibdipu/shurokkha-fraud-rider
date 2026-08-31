from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Dispute
from app.models.schemas import DisputeCreate, DisputeEvidenceSubmit
from app.services.dispute_engine import DisputeEngine

router = APIRouter(prefix="/disputes", tags=["Disputes & Chargebacks"])

@router.get("/")
def list_disputes(db: Session = Depends(get_db)):
    """List all open chargebacks and fraud alerts."""
    disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    return [{
        "id": d.id,
        "transaction_id": d.transaction_id,
        "reason": d.reason,
        "amount_paise": d.amount_paise,
        "amount_inr": round(d.amount_paise / 100, 2),
        "status": d.status,
        "evidence_text": d.evidence_text,
        "due_date": d.due_date.isoformat() + "Z",
        "created_at": d.created_at.isoformat() + "Z"
    } for d in disputes]

@router.post("/")
def create_dispute(payload: DisputeCreate, db: Session = Depends(get_db)):
    """Simulate card network / issuer chargeback dispute."""
    try:
        d = DisputeEngine.create_dispute(payload.transaction_id, payload.reason, payload.amount_paise, db)
        return {"status": "OPEN", "dispute_id": d.id, "amount_inr": round(d.amount_paise / 100, 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/evidence")
def submit_evidence(payload: DisputeEvidenceSubmit, db: Session = Depends(get_db)):
    """Submit proof/evidence to challenge dispute."""
    try:
        d = DisputeEngine.submit_evidence(payload.dispute_id, payload.evidence_text, payload.evidence_file_url, db)
        return {"status": d.status, "dispute_id": d.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dispute_id}/resolve")
def resolve_dispute(dispute_id: str, outcome: str = "WON", db: Session = Depends(get_db)):
    """Resolve dispute (WON or LOST)."""
    try:
        d = DisputeEngine.resolve_dispute(dispute_id, outcome, db)
        return {"status": d.status, "dispute_id": d.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
