import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import IdempotencyKey


class IdempotencyGuard:
    """Prevents duplicate payment processing using idempotency keys."""

    @staticmethod
    def check_existing(key: str, db: Session) -> Optional[dict]:
        """
        Check if this key was already used.
        Returns the cached response dict if exists, else None.
        """
        record = db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
        if record:
            return {
                'cached': True,
                'response': json.loads(record.response_json),
                'status_code': record.status_code
            }
        return None

    @staticmethod
    def store_response(key: str, response: dict, status_code: int, db: Session) -> None:
        """
        Store the final response against this idempotency key.
        If key already exists, silently skip (do not update).
        """
        existing = db.query(IdempotencyKey).filter(IdempotencyKey.key == key).first()
        if existing:
            return
        record = IdempotencyKey(
            key=key,
            response_json=json.dumps(response),
            status_code=status_code,
            created_at=datetime.utcnow()
        )
        try:
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise