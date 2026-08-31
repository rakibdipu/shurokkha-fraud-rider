from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ─── REQUEST SCHEMAS ──────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    amount_paise: int = Field(..., ge=100, description="Minimum 1 INR = 100 paise")
    currency: str = "INR"
    customer_email: Optional[str] = None
    metadata: Optional[dict] = None


class CardDetails(BaseModel):
    card_number: str
    card_expiry: str
    card_cvv: str


class PaymentInitiateRequest(BaseModel):
    order_id: str
    payment_method: str
    card: Optional[CardDetails] = None
    upi_vpa: Optional[str] = None
    ip_address: Optional[str] = "127.0.0.1"
    user_agent: Optional[str] = "RazorFlow-SDK/1.0"
    preferred_gateway: Optional[str] = None


class CaptureRequest(BaseModel):
    transaction_id: str
    otp_code: Optional[str] = None


class RefundRequest(BaseModel):
    transaction_id: str
    amount_paise: int
    reason: Optional[str] = "customer_request"


class WebhookTestRequest(BaseModel):
    merchant_id: str
    event_type: str = "payment.captured"


class ReconciliationRunRequest(BaseModel):
    settlement_date: str
    bank_rows: list[dict]


class FraudRuleUpdateRequest(BaseModel):
    rule_name: str
    new_threshold: int


class AcquirerStatusUpdate(BaseModel):
    gateway_code: str
    health_status: str
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class VendorCreate(BaseModel):
    name: str
    email: str
    bank_account: str
    commission_rate: float = 10.0


class SplitItem(BaseModel):
    vendor_id: str
    percentage: Optional[float] = None
    amount_paise: Optional[int] = None


class SplitPaymentRequest(BaseModel):
    order_id: str
    splits: List[SplitItem]


class SubscriptionPlanCreate(BaseModel):
    name: str
    interval: str = "monthly"
    amount_paise: int
    currency: str = "INR"


class SubscriptionCreate(BaseModel):
    plan_id: str
    customer_email: str


class DisputeCreate(BaseModel):
    transaction_id: str
    reason: str = "FRAUDULENT_CARD_USE"
    amount_paise: Optional[int] = None


class DisputeEvidenceSubmit(BaseModel):
    dispute_id: str
    evidence_text: str
    evidence_file_url: Optional[str] = None


# ─── RESPONSE SCHEMAS ─────────────────────────────────────────────────────────

class OrderResponse(BaseResponse):
    id: str
    merchant_id: str
    amount_paise: int
    currency: str
    status: str
    customer_email: Optional[str]
    created_at: str


class PaymentInitiateResponse(BaseResponse):
    transaction_id: str
    order_id: str
    risk_score: int
    risk_tier: str
    otp_required: bool
    otp_hint: Optional[str]
    message: str


class TransactionResponse(BaseResponse):
    id: str
    order_id: str
    status: str
    risk_score: Optional[int]
    risk_tier: Optional[str]
    bank_ref: Optional[str]
    captured_at: Optional[str]
    refunded_at: Optional[str]


class RiskAssessmentResponse(BaseResponse):
    transaction_id: str
    total_score: int
    tier: str
    triggered_rules: list[dict]
    ml_score: int
    ml_top_features: list[str]
    decision_reason: str


class LedgerEntryResponse(BaseResponse):
    id: str
    transaction_id: str
    entry_type: str
    account_code: str
    amount_paise: int
    description: Optional[str]
    created_at: str


class BalanceSheetResponse(BaseResponse):
    accounts: dict
    is_balanced: bool
    total_debit_paise: int
    total_credit_paise: int


class WebhookEventResponse(BaseResponse):
    id: str
    merchant_id: str
    event_type: str
    status: str
    attempts: int
    next_retry_at: Optional[str]
    created_at: str


class ReconciliationResponse(BaseResponse):
    id: str
    batch_date: str
    total_transactions: int
    total_matched: int
    total_discrepancies: int
    total_missing: int
    report: dict
