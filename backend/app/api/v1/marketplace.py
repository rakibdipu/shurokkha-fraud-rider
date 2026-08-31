from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Vendor, PaymentSplit
from app.models.schemas import VendorCreate, SplitPaymentRequest
from app.services.split_engine import MarketplaceSplitEngine

router = APIRouter(prefix="/marketplace", tags=["Marketplace Splits"])

@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)):
    """List all registered marketplace vendors with current wallet balances."""
    MarketplaceSplitEngine.seed_default_vendors(db)
    vendors = db.query(Vendor).all()
    return [{
        "id": v.id,
        "name": v.name,
        "email": v.email,
        "bank_account": v.bank_account,
        "balance_paise": v.balance_paise,
        "balance_inr": round(v.balance_paise / 100, 2),
        "commission_rate": v.commission_rate
    } for v in vendors]

@router.post("/split")
def execute_split(payload: SplitPaymentRequest, db: Session = Depends(get_db)):
    """Split captured transaction funds across marketplace vendors."""
    try:
        return MarketplaceSplitEngine.process_split_payment(payload.order_id, [s.model_dump() for s in payload.splits], db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payout/{vendor_id}")
def trigger_payout(vendor_id: str, amount_paise: int, db: Session = Depends(get_db)):
    """Trigger instant vendor payout to virtual bank account."""
    try:
        return MarketplaceSplitEngine.trigger_vendor_payout(vendor_id, amount_paise, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
