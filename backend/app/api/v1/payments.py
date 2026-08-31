from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.schemas import PaymentInitiateRequest, CaptureRequest, RefundRequest
from app.services.payment_engine import PaymentEngine

router = APIRouter(prefix='/payments', tags=['Payments'])

@router.post('/initiate')
def initiate_payment(
    payload: PaymentInitiateRequest,
    db: Session = Depends(get_db)
):
    """
    Tokenize card, run Sentinel fraud engine, determine if 3DS is needed.
    Returns risk_tier: ALLOW (proceed to capture) | CHALLENGE (OTP required) | BLOCK (rejected)
    
    Test Cards:
    - 4111111111111111 -> ALLOW (risk < 30)
    - 4000000000000002 -> CHALLENGE (3DS OTP required)
    - 4000000000000069 -> BLOCK (fraud rejected)
    """
    try:
        return PaymentEngine.initiate_payment(payload, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Payment initiation failed: {str(e)}')

@router.post('/capture')
def capture_payment(
    payload: CaptureRequest,
    db: Session = Depends(get_db)
):
    """
    Capture an authorized payment.
    If 3DS challenge was required, provide otp_code here.
    On success: posts double-entry ledger entries and enqueues webhook.
    """
    try:
        return PaymentEngine.capture_payment(payload.transaction_id, payload.otp_code, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Capture failed: {str(e)}')

@router.post('/refund')
def refund_payment(
    payload: RefundRequest,
    db: Session = Depends(get_db)
):
    """
    Refund a captured payment (full or partial).
    Posts reversal ledger entries and fires refund webhook.
    """
    try:
        return PaymentEngine.refund_payment(
            payload.transaction_id,
            payload.amount_paise,
            payload.reason or 'customer_request',
            db
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Refund failed: {str(e)}')

@router.get('/{transaction_id}')
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get transaction details by ID."""
    try:
        return PaymentEngine.get_transaction(transaction_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
