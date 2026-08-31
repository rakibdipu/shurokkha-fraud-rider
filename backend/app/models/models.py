import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    api_key = Column(String(64), nullable=False)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")
    webhook_events = relationship("WebhookEvent", back_populates="merchant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Merchant(id='{self.id}', name='{self.name}', email='{self.email}')>"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    status = Column(String(30), default="CREATED", nullable=False)
    customer_email = Column(String(200), nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order", cascade="all, delete-orphan")
    payment_tokens = relationship("PaymentToken", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order(id='{self.id}', amount_paise={self.amount_paise}, status='{self.status}')>"


class PaymentToken(Base):
    __tablename__ = "payment_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    encrypted_pan = Column(Text, nullable=False)
    card_brand = Column(String(20), nullable=True)
    last4 = Column(String(4), nullable=True)
    bin6 = Column(String(6), nullable=True)
    expiry_masked = Column(String(7), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="payment_tokens")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    status = Column(String(30), default="PROCESSING", nullable=False)
    risk_score = Column(Integer, nullable=True)
    risk_tier = Column(String(15), nullable=True)
    risk_details_json = Column(Text, nullable=True)
    bank_ref = Column(String(64), nullable=True)
    acquirer_gateway = Column(String(30), default="HDFC", nullable=True)
    acquirer_response_json = Column(Text, nullable=True)
    captured_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="transactions")
    ledger_entries = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan")
    splits = relationship("PaymentSplit", back_populates="transaction", cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="transaction", cascade="all, delete-orphan")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    entry_type = Column(String(10), nullable=False)  # DEBIT or CREDIT
    account_code = Column(String(50), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="ledger_entries")


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(15), default="PENDING", nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    merchant = relationship("Merchant", back_populates="webhook_events")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String(128), primary_key=True)
    response_json = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReconciliationReport(Base):
    __tablename__ = "reconciliation_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_date = Column(String(10), nullable=False)
    total_transactions = Column(Integer, default=0, nullable=False)
    total_matched = Column(Integer, default=0, nullable=False)
    total_discrepancies = Column(Integer, default=0, nullable=False)
    total_missing = Column(Integer, default=0, nullable=False)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ==========================================
# 🚀 5 ADVANCED ENTERPRISE EXPANSION MODELS
# ==========================================

class AcquirerGateway(Base):
    """Multi-acquirer gateway configurations with live health & routing priorities."""
    __tablename__ = "acquirer_gateways"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(20), unique=True, nullable=False)  # HDFC, ICICI, STRIPE, CHASE
    name = Column(String(100), nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    fee_percent = Column(Float, default=1.8, nullable=False)
    success_rate = Column(Float, default=96.5, nullable=False)
    avg_latency_ms = Column(Integer, default=110, nullable=False)
    health_status = Column(String(20), default="HEALTHY", nullable=False)  # HEALTHY / DEGRADED / DOWN
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Vendor(Base):
    """Marketplace sub-merchants / sellers for split payments (Stripe Connect)."""
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    bank_account = Column(String(50), nullable=False)
    balance_paise = Column(Integer, default=0, nullable=False)
    commission_rate = Column(Float, default=10.0, nullable=False)  # 10% default platform cut
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    splits = relationship("PaymentSplit", back_populates="vendor")


class PaymentSplit(Base):
    """Individual splits of a transaction to marketplace vendors."""
    __tablename__ = "payment_splits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    platform_fee_paise = Column(Integer, nullable=False)
    vendor_net_paise = Column(Integer, nullable=False)
    status = Column(String(20), default="SETTLED", nullable=False)  # SETTLED / PAYOUT_PENDING / PAID_OUT
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="splits")
    vendor = relationship("Vendor", back_populates="splits")


class SubscriptionPlan(Base):
    """Recurring billing plans (Daily / Weekly / Monthly / Yearly)."""
    __tablename__ = "subscription_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    interval = Column(String(20), default="monthly", nullable=False)  # monthly, yearly
    amount_paise = Column(Integer, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")


class Subscription(Base):
    """Active customer recurring mandates & subscription billing cycles."""
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    customer_email = Column(String(200), nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE / PAST_DUE / CANCELLED
    current_period_start = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    next_billing_at = Column(DateTime, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class Dispute(Base):
    """Chargeback, fraud alerts (TC40/SAFE), and customer disputes."""
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    reason = Column(String(100), nullable=False)
    amount_paise = Column(Integer, nullable=False)
    status = Column(String(25), default="NEEDS_RESPONSE", nullable=False)  # NEEDS_RESPONSE / UNDER_REVIEW / WON / LOST / ACCEPTED
    evidence_text = Column(Text, nullable=True)
    evidence_file_url = Column(String(500), nullable=True)
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transaction = relationship("Transaction", back_populates="disputes")
