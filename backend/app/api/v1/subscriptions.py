from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import SubscriptionPlan, Subscription
from app.models.schemas import SubscriptionPlanCreate, SubscriptionCreate
from app.services.subscription_engine import SubscriptionEngine

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & AutoPay"])

@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    """List all recurring billing subscription plans."""
    SubscriptionEngine.seed_default_plans(db)
    plans = db.query(SubscriptionPlan).all()
    return [{
        "id": p.id,
        "name": p.name,
        "interval": p.interval,
        "amount_paise": p.amount_paise,
        "amount_inr": round(p.amount_paise / 100, 2),
        "currency": p.currency
    } for p in plans]

@router.get("/")
def list_subscriptions(db: Session = Depends(get_db)):
    """List active recurring customer subscriptions."""
    subs = db.query(Subscription).all()
    return [{
        "id": s.id,
        "customer_email": s.customer_email,
        "plan_name": s.plan.name if s.plan else "Standard",
        "amount_inr": round(s.plan.amount_paise / 100, 2) if s.plan else 0,
        "status": s.status,
        "next_billing_at": s.next_billing_at.isoformat() + "Z"
    } for s in subs]

@router.post("/")
def create_subscription(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    """Register customer to a recurring mandate."""
    try:
        sub = SubscriptionEngine.create_subscription(payload.plan_id, payload.customer_email, db)
        return {"status": "ACTIVE", "subscription_id": sub.id, "customer_email": sub.customer_email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/trigger-billing-cron")
def trigger_billing_cron(db: Session = Depends(get_db)):
    """Manually trigger recurring billing cycle run."""
    return SubscriptionEngine.charge_due_subscriptions(db)
