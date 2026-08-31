import random
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional
from app.models.models import PaymentToken

# In-memory OTP store: {transaction_id: {otp, expires_at}}
_otp_store: dict = {}


class AcquirerSimulator:
    """Simulates a bank acquirer / card network for testing."""

    @staticmethod
    def authorize(token: PaymentToken, amount_paise: int) -> dict:
        """
        Simulate bank authorization.
        Returns: {success, bank_ref, acquirer_code, message}

        Outcomes (weighted random):
        - 90%: success (APPROVED)
        - 5%: insufficient_funds (DECLINED)
        - 5%: bank_timeout (ERROR)

        Special test BINs:
        - BIN starting with '411111': always APPROVED (test ALLOW card)
        - BIN starting with '400000': depends on last4 (0002=needs 3DS, 0069=blocked upstream)
        """
        bin6 = token.bin6 or ''
        last4 = token.last4 or ''

        # Test card overrides
        if bin6 == '411111':
            return {
                'success': True,
                'bank_ref': f'BNK-{str(uuid.uuid4())[:8].upper()}',
                'acquirer_code': 'APPROVED',
                'message': 'Transaction approved'
            }
        if bin6 == '400000' and last4 == '0069':
            return {
                'success': False,
                'bank_ref': None,
                'acquirer_code': 'FRAUD_BLOCKED',
                'message': 'Card flagged by issuer fraud system'
            }

        # Standard random outcome
        roll = random.random()
        if roll < 0.90:
            return {
                'success': True,
                'bank_ref': f'BNK-{str(uuid.uuid4())[:8].upper()}',
                'acquirer_code': 'APPROVED',
                'message': 'Transaction approved'
            }
        elif roll < 0.95:
            return {
                'success': False,
                'bank_ref': None,
                'acquirer_code': 'INSUFFICIENT_FUNDS',
                'message': 'Insufficient funds in account'
            }
        else:
            return {
                'success': False,
                'bank_ref': None,
                'acquirer_code': 'BANK_TIMEOUT',
                'message': 'Bank gateway timeout, please retry'
            }

    @staticmethod
    def generate_3ds_otp(transaction_id: str) -> str:
        """
        Generate and store a 6-digit OTP for 3D-Secure verification.
        OTP expires in 5 minutes.
        Returns the OTP string (in production, bank sends this via SMS).
        """
        otp = str(random.randint(100000, 999999))
        _otp_store[transaction_id] = {
            'otp': otp,
            'expires_at': datetime.utcnow() + timedelta(minutes=5)
        }
        return otp

    @staticmethod
    def verify_3ds_otp(transaction_id: str, otp: str) -> bool:
        """
        Verify a 3DS OTP for a given transaction.
        Returns True if valid and not expired, False otherwise.
        Cleans up used OTPs.
        """
        entry = _otp_store.get(transaction_id)
        if not entry:
            return False
        if datetime.utcnow() > entry['expires_at']:
            del _otp_store[transaction_id]
            return False
        if entry['otp'] == str(otp):
            del _otp_store[transaction_id]  # One-time use
            return True
        return False

    @staticmethod
    def get_pending_otp(transaction_id: str) -> Optional[str]:
        """For testing: retrieve the OTP without consuming it."""
        entry = _otp_store.get(transaction_id)
        return entry['otp'] if entry else None