from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.schemas import OrderCreate, OrderResponse
from app.services.payment_engine import PaymentEngine

router = APIRouter(prefix='/orders', tags=['Orders'])

@router.post('/', status_code=201)
def create_order(
    payload: OrderCreate,
    idempotency_key: Optional[str] = Header(None, alias='Idempotency-Key'),
    db: Session = Depends(get_db)
):
    """
    Create a new payment order.
    Requires Idempotency-Key header to prevent duplicates.
    If the same key is sent twice, returns the cached first response.
    """
    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())  # Auto-generate if not provided
    
    # Use first merchant for demo (in production, extract from API key auth)
    from app.models.models import Merchant
    merchant = db.query(Merchant).first()
    if not merchant:
        raise HTTPException(status_code=503, detail='No merchants configured. Run seed_data.py first.')
    
    try:
        result = PaymentEngine.create_order(merchant.id, payload, idempotency_key, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Order creation failed: {str(e)}')

@router.get('/{order_id}')
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get order details with all linked transactions."""
    try:
        return PaymentEngine.get_order(order_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
