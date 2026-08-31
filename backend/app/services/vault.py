import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.security import CardVault
from app.models.models import PaymentToken


class TokenizationService:
    """Handles card tokenization and retrieval."""

    @staticmethod
    def tokenize_card(
        order_id: str,
        card_number: str,
        expiry: str,
        db: Session
    ) -> PaymentToken:
        """
        Encrypt and store card data. Returns the PaymentToken ORM object.
        card_number: raw PAN (digits only, spaces stripped internally)
        expiry: MM/YY or MM/YYYY
        """
        token_data = CardVault.generate_payment_token(card_number, expiry)
        payment_token = PaymentToken(
            id=str(uuid.uuid4()),
            order_id=order_id,
            encrypted_pan=token_data['encrypted_pan'],
            card_brand=token_data['card_brand'],
            last4=token_data['last4'],
            bin6=token_data['bin6'],
            expiry_masked=token_data['expiry_masked'],
            created_at=datetime.utcnow()
        )
        try:
            db.add(payment_token)
            db.commit()
            db.refresh(payment_token)
            return payment_token
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_token(token_id: str, db: Session) -> PaymentToken:
        """Retrieve a PaymentToken by its ID."""
        token = db.query(PaymentToken).filter(PaymentToken.id == token_id).first()
        if not token:
            raise ValueError(f"PaymentToken {token_id} not found")
        return token