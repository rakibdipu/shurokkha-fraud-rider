from typing import List
import os

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        APP_NAME: str = "Shurokkha Fraud Rider"
        APP_VERSION: str = "1.0.0"
        DEBUG: bool = True
        
        # Security
        SECRET_KEY: str = "shurokkha-aes-key-32-bytes-secret"  # Must be 32 bytes for AES-256
        HMAC_SECRET: str = "shurokkha-hmac-webhook-secret-key"
        API_KEY_HEADER: str = "X-Shurokkha-API-Key"
        
        # Database
        DB_URL: str = "sqlite:///./shurokkha.db"
        
        # Fraud Engine Thresholds
        FRAUD_VELOCITY_MAX_PER_MINUTE: int = 3
        FRAUD_VELOCITY_MAX_PER_HOUR: int = 10
        FRAUD_AMOUNT_SPIKE_MULTIPLIER: float = 5.0
        FRAUD_ALLOW_THRESHOLD: int = 30
        FRAUD_BLOCK_THRESHOLD: int = 70
        FRAUD_IMPOSSIBLE_TRAVEL_MINUTES: int = 30
        
        # Webhook
        WEBHOOK_RETRY_DELAYS: List[int] = [5, 30, 120, 600]
        WEBHOOK_REPLAY_WINDOW_SECONDS: int = 300
        WEBHOOK_TIMEOUT_SECONDS: int = 10
        
        # Gateway Fee
        GATEWAY_FEE_PERCENT: float = 2.0  # 2% of transaction amount
        
        # Test Cards
        TEST_CARD_ALLOW: str = "4111111111111111"
        TEST_CARD_CHALLENGE: str = "4000000000000002"
        TEST_CARD_BLOCK: str = "4000000000000069"
        
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"

except ImportError:
    class Settings:
        APP_NAME: str = "Shurokkha Fraud Rider"
        APP_VERSION: str = "1.0.0"
        DEBUG: bool = True
        
        # Security
        SECRET_KEY: str = "shurokkha-aes-key-32-bytes-secret"  # Must be 32 bytes for AES-256
        HMAC_SECRET: str = "shurokkha-hmac-webhook-secret-key"
        API_KEY_HEADER: str = "X-Shurokkha-API-Key"
        
        # Database
        DB_URL: str = "sqlite:///./shurokkha.db"
        
        # Fraud Engine Thresholds
        FRAUD_VELOCITY_MAX_PER_MINUTE: int = 3
        FRAUD_VELOCITY_MAX_PER_HOUR: int = 10
        FRAUD_AMOUNT_SPIKE_MULTIPLIER: float = 5.0
        FRAUD_ALLOW_THRESHOLD: int = 30
        FRAUD_BLOCK_THRESHOLD: int = 70
        FRAUD_IMPOSSIBLE_TRAVEL_MINUTES: int = 30
        
        # Webhook
        WEBHOOK_RETRY_DELAYS: List[int] = [5, 30, 120, 600]
        WEBHOOK_REPLAY_WINDOW_SECONDS: int = 300
        WEBHOOK_TIMEOUT_SECONDS: int = 10
        
        # Gateway Fee
        GATEWAY_FEE_PERCENT: float = 2.0  # 2% of transaction amount
        
        # Test Cards
        TEST_CARD_ALLOW: str = "4111111111111111"
        TEST_CARD_CHALLENGE: str = "4000000000000002"
        TEST_CARD_BLOCK: str = "4000000000000069"

settings = Settings()
