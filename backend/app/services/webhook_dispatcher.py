import json
import uuid
import requests
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.models.models import WebhookEvent, Merchant
from app.core.security import HMACSigner
from app.core.config import settings


class WebhookDispatcher:
    """HMAC-signed webhook delivery with Outbox Pattern and retry/DLQ logic."""

    @staticmethod
    def enqueue(
        merchant_id: str,
        event_type: str,
        payload: dict,
        db: Session
    ) -> WebhookEvent:
        """
        Create a WebhookEvent row (PENDING status) in the same DB transaction.
        This implements the Transactional Outbox Pattern:
        the event is written atomically with the payment capture.
        """
        event = WebhookEvent(
            id=str(uuid.uuid4()),
            merchant_id=merchant_id,
            event_type=event_type,
            payload_json=json.dumps(payload),
            status='PENDING',
            attempts=0,
            created_at=datetime.utcnow()
        )
        try:
            db.add(event)
            db.commit()
            db.refresh(event)
        except Exception:
            db.rollback()
            raise
        return event

    @staticmethod
    def build_signed_request(merchant: Merchant, payload: dict) -> tuple:
        """
        Build the signed HTTP request for a webhook delivery.
        Returns (headers: dict, body: str)
        """
        body = json.dumps(payload, separators=(',', ':'))
        signature = HMACSigner.sign_payload(merchant.webhook_secret or settings.HMAC_SECRET, body)
        headers = {
            'Content-Type': 'application/json',
            'X-Shurokkha-Signature': signature,
            'X-Shurokkha-Event': payload.get('event', 'unknown'),
            'User-Agent': f'Shurokkha-Webhook/1.0 ({settings.APP_VERSION})'
        }
        return headers, body

    @staticmethod
    def _send_webhook(event: WebhookEvent, merchant: Merchant) -> tuple:
        """
        Attempt to POST the webhook to the merchant's endpoint.
        Returns (success: bool, response_code: int)
        """
        if not merchant.webhook_url:
            return False, 0
        
        payload = json.loads(event.payload_json)
        headers, body = WebhookDispatcher.build_signed_request(merchant, payload)
        
        try:
            response = requests.post(
                merchant.webhook_url,
                data=body,
                headers=headers,
                timeout=settings.WEBHOOK_TIMEOUT_SECONDS
            )
            success = 200 <= response.status_code < 300
            return success, response.status_code
        except requests.exceptions.Timeout:
            return False, 408
        except requests.exceptions.ConnectionError:
            return False, 503
        except Exception:
            return False, 500

    @staticmethod
    def dispatch_pending(db: Session) -> dict:
        """
        Process all PENDING or retry-due FAILED webhook events.
        Uses exponential backoff retry schedule from settings.WEBHOOK_RETRY_DELAYS.
        Events exceeding all retries go to DLQ status.
        Returns summary: {sent, failed, dlq, skipped}
        """
        now = datetime.utcnow()
        
        # Fetch events that are PENDING or FAILED and due for retry
        events = db.query(WebhookEvent).filter(
            WebhookEvent.status.in_(['PENDING', 'FAILED']),
        ).filter(
            (WebhookEvent.next_retry_at == None) | (WebhookEvent.next_retry_at <= now)
        ).all()
        
        results = {'sent': 0, 'failed': 0, 'dlq': 0, 'skipped': 0}
        
        for event in events:
            merchant = db.query(Merchant).filter(Merchant.id == event.merchant_id).first()
            if not merchant or not merchant.webhook_url:
                results['skipped'] += 1
                continue
            
            success, response_code = WebhookDispatcher._send_webhook(event, merchant)
            
            event.attempts += 1
            event.last_attempt_at = now
            event.response_code = response_code
            
            if success:
                event.status = 'SENT'
                results['sent'] += 1
            else:
                retry_delays = settings.WEBHOOK_RETRY_DELAYS
                if event.attempts >= len(retry_delays):
                    # All retries exhausted → DLQ
                    event.status = 'DLQ'
                    event.next_retry_at = None
                    results['dlq'] += 1
                else:
                    delay_seconds = retry_delays[event.attempts - 1]
                    event.status = 'FAILED'
                    event.next_retry_at = now + timedelta(seconds=delay_seconds)
                    results['failed'] += 1
            
            try:
                db.commit()
            except Exception:
                db.rollback()
        
        return results

    @staticmethod
    def replay_dlq_event(event_id: str, db: Session) -> WebhookEvent:
        """
        Manually replay a Dead Letter Queue event.
        Resets status to PENDING and clears retry count.
        """
        event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        if not event:
            raise ValueError(f'WebhookEvent {event_id} not found')
        if event.status != 'DLQ':
            raise ValueError(f'Event {event_id} is not in DLQ status (current: {event.status})')
        
        event.status = 'PENDING'
        event.attempts = 0
        event.next_retry_at = None
        
        try:
            db.commit()
            db.refresh(event)
        except Exception:
            db.rollback()
            raise
        return event

    @staticmethod
    def get_events(
        db: Session,
        merchant_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """List webhook events with optional filters."""
        query = db.query(WebhookEvent)
        if merchant_id:
            query = query.filter(WebhookEvent.merchant_id == merchant_id)
        if status:
            query = query.filter(WebhookEvent.status == status)
        events = query.order_by(WebhookEvent.created_at.desc()).limit(limit).all()
        return [{
            'id': e.id,
            'merchant_id': e.merchant_id,
            'event_type': e.event_type,
            'status': e.status,
            'attempts': e.attempts,
            'response_code': e.response_code,
            'next_retry_at': e.next_retry_at.isoformat() + 'Z' if e.next_retry_at else None,
            'created_at': e.created_at.isoformat() + 'Z',
            'payload': json.loads(e.payload_json)
        } for e in events]
