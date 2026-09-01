from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.core.database import get_db
from app.models.schemas import WebhookTestRequest
from app.services.webhook_dispatcher import WebhookDispatcher
from app.core.security import HMACSigner
from app.core.config import settings

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])

# In-memory store for test webhook receipts
_received_webhooks = []

@router.post('/simulate-dispatch')
def simulate_dispatch(db: Session = Depends(get_db)):
    """
    Manually trigger webhook dispatch for all PENDING/FAILED events.
    Returns count of sent, failed, and DLQ'd events.
    """
    result = WebhookDispatcher.dispatch_pending(db)
    return {'status': 'dispatch_complete', 'result': result}

@router.get('/events')
def list_webhook_events(
    merchant_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List webhook events with optional filters."""
    return WebhookDispatcher.get_events(db, merchant_id=merchant_id, status=status, limit=limit)

@router.post('/events/{event_id}/replay')
def replay_dlq_event(event_id: str, db: Session = Depends(get_db)):
    """
    Manually replay a Dead Letter Queue (DLQ) webhook event.
    Resets it to PENDING for next dispatch cycle.
    """
    try:
        event = WebhookDispatcher.replay_dlq_event(event_id, db)
        return {'status': 'reset_to_pending', 'event_id': event.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/test-receiver')
async def test_webhook_receiver(request: Request):
    """
    Mock merchant webhook endpoint for testing.
    Logs received webhooks and verifies HMAC signature.
    """
    body = await request.body()
    body_str = body.decode('utf-8')
    signature_header = request.headers.get('X-Shurokkha-Signature') or request.headers.get('X-Shurokkha-Signature', '')
    
    is_valid = HMACSigner.verify_signature(settings.HMAC_SECRET, body_str, signature_header)
    is_replay = HMACSigner.is_replay_attack(signature_header) if signature_header else True
    
    receipt = {
        'received_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'signature_valid': is_valid,
        'is_replay_attack': is_replay,
        'event_type': request.headers.get('X-Shurokkha-Event') or request.headers.get('X-Shurokkha-Event', 'unknown'),
        'payload': json.loads(body_str) if body_str else {}
    }
    _received_webhooks.append(receipt)
    
    return {'status': 'received', 'signature_valid': is_valid, 'is_replay': is_replay}

@router.get('/test-receiver/history')
def get_webhook_receiver_history():
    """View webhooks received by the test receiver endpoint."""
    return {'count': len(_received_webhooks), 'events': _received_webhooks[-20:]}

@router.post('/verify-signature')
async def verify_webhook_signature(request: Request):
    """
    Verify a webhook signature. Pass raw body and X-Shurokkha-Signature header.
    """
    body = await request.body()
    body_str = body.decode('utf-8')
    sig = request.headers.get('X-Shurokkha-Signature') or request.headers.get('X-Shurokkha-Signature', '')
    secret = request.headers.get('X-Webhook-Secret', settings.HMAC_SECRET)
    
    is_valid = HMACSigner.verify_signature(secret, body_str, sig)
    is_replay = HMACSigner.is_replay_attack(sig)
    
    return {
        'signature_valid': is_valid,
        'is_replay_attack': is_replay,
        'verdict': 'ACCEPT' if (is_valid and not is_replay) else 'REJECT'
    }
