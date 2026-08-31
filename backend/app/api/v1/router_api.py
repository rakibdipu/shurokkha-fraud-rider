from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import AcquirerGateway
from app.models.schemas import AcquirerStatusUpdate
from app.services.smart_router import SmartRoutingEngine

router = APIRouter(prefix="/routing", tags=["Smart Routing"])

@router.get("/gateways")
def list_acquirer_gateways(db: Session = Depends(get_db)):
    """List all connected acquirer gateways and live success rates."""
    SmartRoutingEngine.initialize_gateways(db)
    gateways = db.query(AcquirerGateway).all()
    return [{
        "code": g.code,
        "name": g.name,
        "priority": g.priority,
        "fee_percent": g.fee_percent,
        "success_rate": g.success_rate,
        "avg_latency_ms": g.avg_latency_ms,
        "health_status": g.health_status,
        "is_active": g.is_active
    } for g in gateways]

@router.post("/simulate-failover")
def simulate_failover(payload: AcquirerStatusUpdate, db: Session = Depends(get_db)):
    """Simulate bank gateway degradation / outage to test Auto-Cascade."""
    gw = db.query(AcquirerGateway).filter(AcquirerGateway.code == payload.gateway_code.upper()).first()
    if not gw:
        raise HTTPException(status_code=404, detail="Gateway not found")
    gw.health_status = payload.health_status
    if payload.is_active is not None:
        gw.is_active = payload.is_active
    db.commit()
    return {"status": "updated", "gateway": gw.code, "health_status": gw.health_status}
