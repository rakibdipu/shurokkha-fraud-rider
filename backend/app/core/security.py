import base64
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


class CardVault:
    """AES-256-GCM encryption for PAN data with tokenization utilities."""
    
    @staticmethod
    def _get_key() -> bytes:
        """Derive a 32-byte AES key from SECRET_KEY."""
        key = settings.SECRET_KEY.encode('utf-8')
        # Pad or hash to exactly 32 bytes
        return hashlib.sha256(key).digest()
    
    @staticmethod
    def encrypt_pan(pan: str) -> str:
        """Encrypt PAN with AES-256-GCM. Returns base64 encoded: nonce(12) + ciphertext."""
        key = CardVault._get_key()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        pan_bytes = pan.strip().replace(" ", "").encode()
        ciphertext = aesgcm.encrypt(nonce, pan_bytes, None)
        combined = nonce + ciphertext
        return base64.b64encode(combined).decode()
    
    @staticmethod
    def decrypt_pan(token: str) -> str:
        """Decrypt base64 token back to plaintext PAN."""
        key = CardVault._get_key()
        aesgcm = AESGCM(key)
        combined = base64.b64decode(token.encode())
        nonce = combined[:12]
        ciphertext = combined[12:]
        pan_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return pan_bytes.decode()
    
    @staticmethod
    def mask_pan(pan: str) -> str:
        """Return masked PAN. First 6 + last 4 visible, rest as *.
        E.g.: 4111111111111111 → 411111######1111"""
        pan = pan.strip().replace(" ", "")
        if len(pan) < 10:
            return pan
        return pan[:6] + '#' * (len(pan) - 10) + pan[-4:]
    
    @staticmethod
    def extract_bin(pan: str) -> str:
        """Extract first 6 digits (Bank Identification Number)."""
        pan = pan.strip().replace(" ", "")
        return pan[:6]
    
    @staticmethod
    def get_last4(pan: str) -> str:
        pan = pan.strip().replace(" ", "")
        return pan[-4:]
    
    @staticmethod
    def get_card_brand(pan: str) -> str:
        """Detect card brand from PAN prefix."""
        pan = pan.strip().replace(" ", "")
        if pan.startswith('4'):
            return 'Visa'
        elif pan[:2] in ['51','52','53','54','55'] or (len(pan) >= 4 and pan[:4].isdigit() and 2221 <= int(pan[:4]) <= 2720):
            return 'Mastercard'
        elif pan[:2] in ['34','37']:
            return 'Amex'
        elif pan[:4] in ['6011'] or pan[:2] == '65':
            return 'Discover'
        elif pan[:4] in ['5018','5020','5038']:
            return 'Maestro'
        elif pan[:4] in ['6069','6070','6071','6072','6073','6074','6075','6076','6077','6078','6079']:
            return 'Rupay'
        else:
            return 'Unknown'
    
    @staticmethod
    def generate_payment_token(pan: str, expiry: str) -> dict:
        """Full tokenization: encrypt PAN, extract metadata.
        Returns: {encrypted_pan, bin6, last4, card_brand, expiry_masked}"""
        pan_clean = pan.strip().replace(" ", "")
        return {
            'encrypted_pan': CardVault.encrypt_pan(pan_clean),
            'bin6': CardVault.extract_bin(pan_clean),
            'last4': CardVault.get_last4(pan_clean),
            'card_brand': CardVault.get_card_brand(pan_clean),
            'expiry_masked': expiry,
        }


class HMACSigner:
    """HMAC-SHA256 webhook signing and verification."""
    
    @staticmethod
    def sign_payload(secret: str, payload: str) -> str:
        """Sign a webhook payload.
        Returns header value in format: t={timestamp},v1={hmac_hex}
        """
        timestamp = str(int(time.time()))
        signed_string = f"{timestamp}.{payload}"
        mac = hmac.new(secret.encode(), signed_string.encode(), hashlib.sha256)
        return f"t={timestamp},v1={mac.hexdigest()}"
    
    @staticmethod
    def verify_signature(secret: str, payload: str, header: str) -> bool:
        """Verify a webhook signature header.
        Returns False if invalid or expired.
        """
        try:
            parts = dict(item.split('=', 1) for item in header.split(','))
            timestamp = parts.get('t', '')
            received_sig = parts.get('v1', '')
            signed_string = f"{timestamp}.{payload}"
            expected = hmac.new(secret.encode(), signed_string.encode(), hashlib.sha256).hexdigest()
            # Timing-safe comparison
            return hmac.compare_digest(expected, received_sig)
        except Exception:
            return False
    
    @staticmethod
    def is_replay_attack(header: str, window_seconds: int = None) -> bool:
        """Check if the timestamp in the header is too old (replay attack protection)."""
        if window_seconds is None:
            window_seconds = settings.WEBHOOK_REPLAY_WINDOW_SECONDS
        try:
            parts = dict(item.split('=', 1) for item in header.split(','))
            timestamp = int(parts.get('t', 0))
            age = int(time.time()) - timestamp
            return age > window_seconds
        except Exception:
            return True  # Treat malformed headers as replay attacks
