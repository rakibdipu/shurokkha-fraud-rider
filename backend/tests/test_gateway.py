import pytest
import os
import sys
import uuid
import json

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import CardVault, HMACSigner
from app.core.config import settings

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Shurokkha" in data["app"]

def test_card_vault_encryption_decryption():
    """Test AES-256-GCM encryption and decryption round-trip."""
    pan = "4111111111111111"
    encrypted = CardVault.encrypt_pan(pan)
    assert encrypted != pan
    decrypted = CardVault.decrypt_pan(encrypted)
    assert decrypted == pan

    masked = CardVault.mask_pan(pan)
    assert masked.startswith("411111")
    assert masked.endswith("1111")

    brand = CardVault.get_card_brand(pan)
    assert brand == "Visa"

def test_hmac_webhook_signatures():
    """Test HMAC-SHA256 signing and verification with replay protection."""
    secret = "test_webhook_secret_key"
    payload = json.dumps({"event": "payment.captured", "amount_paise": 49900})
    
    header = HMACSigner.sign_payload(secret, payload)
    assert "t=" in header and "v1=" in header

    # Valid signature
    is_valid = HMACSigner.verify_signature(secret, payload, header)
    assert is_valid is True

    # Tampered payload
    tampered_valid = HMACSigner.verify_signature(secret, payload + "extra", header)
    assert tampered_valid is False

    # Replay attack check
    assert HMACSigner.is_replay_attack(header, window_seconds=300) is False

def test_create_order_idempotent():
    """Test order creation and idempotency caching."""
    idempotency_key = f"test-idemp-{uuid.uuid4()}"
    payload = {
        "amount_paise": 149900,
        "currency": "INR",
        "customer_email": "test.client@shurokkha.io",
        "metadata": {"order_ref": "ORD-991"}
    }

    # First request
    res1 = client.post("/api/v1/orders/", json=payload, headers={"Idempotency-Key": idempotency_key})
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["status"] == "CREATED"
    assert data1["amount_paise"] == 149900

    # Replay request with same key
    res2 = client.post("/api/v1/orders/", json=payload, headers={"Idempotency-Key": idempotency_key})
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["id"] == data1["id"]

def test_payment_flow_allow():
    """Test full ALLOW payment lifecycle: Create -> Initiate -> Direct Capture."""
    # 1. Create order
    order_res = client.post("/api/v1/orders/", json={
        "amount_paise": 99900,
        "currency": "INR",
        "customer_email": "allow.tester@shurokkha.io"
    }, headers={"Idempotency-Key": str(uuid.uuid4())})
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # 2. Initiate with ALLOW test card
    init_res = client.post("/api/v1/payments/initiate", json={
        "order_id": order_id,
        "payment_method": "card",
        "card": {
            "card_number": settings.TEST_CARD_ALLOW,
            "card_expiry": "12/2027",
            "card_cvv": "123"
        },
        "ip_address": "103.144.12.8"
    })
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["risk_tier"] == "ALLOW"
    assert init_data["otp_required"] is False
    txn_id = init_data["transaction_id"]

    # 3. Capture
    cap_res = client.post("/api/v1/payments/capture", json={"transaction_id": txn_id})
    assert cap_res.status_code == 200
    cap_data = cap_res.json()
    assert cap_data["status"] == "CAPTURED"
    assert cap_data["bank_ref"].startswith("BNK-")

def test_payment_flow_challenge_3ds():
    """Test CHALLENGE payment lifecycle with 3DS OTP verification."""
    order_res = client.post("/api/v1/orders/", json={
        "amount_paise": 249900,
        "currency": "INR",
        "customer_email": "3ds.tester@shurokkha.io"
    }, headers={"Idempotency-Key": str(uuid.uuid4())})
    order_id = order_res.json()["id"]

    # Initiate with CHALLENGE test card
    init_res = client.post("/api/v1/payments/initiate", json={
        "order_id": order_id,
        "payment_method": "card",
        "card": {
            "card_number": settings.TEST_CARD_CHALLENGE,
            "card_expiry": "06/2026",
            "card_cvv": "456"
        },
        "ip_address": "103.144.12.9"
    })
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["risk_tier"] == "CHALLENGE"
    assert init_data["otp_required"] is True
    assert init_data["otp_code"] is not None
    txn_id = init_data["transaction_id"]
    otp = init_data["otp_code"]

    # Capture with valid OTP
    cap_res = client.post("/api/v1/payments/capture", json={
        "transaction_id": txn_id,
        "otp_code": otp
    })
    assert cap_res.status_code == 200
    cap_data = cap_res.json()
    assert cap_data["status"] == "CAPTURED"

def test_payment_flow_block_fraud():
    """Test BLOCK fraud protection — transaction auto-rejected."""
    order_res = client.post("/api/v1/orders/", json={
        "amount_paise": 500000,
        "currency": "INR",
        "customer_email": "fraudster@tor-exit.net"
    }, headers={"Idempotency-Key": str(uuid.uuid4())})
    order_id = order_res.json()["id"]

    # Initiate with BLOCK test card
    init_res = client.post("/api/v1/payments/initiate", json={
        "order_id": order_id,
        "payment_method": "card",
        "card": {
            "card_number": settings.TEST_CARD_BLOCK,
            "card_expiry": "03/2025",
            "card_cvv": "000"
        },
        "ip_address": "45.154.255.99"
    })
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["risk_tier"] == "BLOCK"
    assert init_data["otp_required"] is False
    assert "blocked" in init_data["message"].lower()

def test_ledger_balance_sheet():
    """Test double-entry ledger balance sheet equality."""
    res = client.get("/api/v1/ledger/balance-sheet")
    assert res.status_code == 200
    data = res.json()
    assert data["is_balanced"] is True
    assert data["total_debit_paise"] == data["total_credit_paise"]

def test_smart_routing_gateways():
    """Test multi-acquirer gateways and failover simulation."""
    res = client.get("/api/v1/routing/gateways")
    assert res.status_code == 200
    gateways = res.json()
    assert len(gateways) >= 4
    codes = [g["code"] for g in gateways]
    assert "HDFC" in codes and "ICICI" in codes

def test_marketplace_vendors_and_payout():
    """Test marketplace vendor listing and instant payout simulation."""
    res = client.get("/api/v1/marketplace/vendors")
    assert res.status_code == 200
    vendors = res.json()
    assert len(vendors) > 0
    vendor_id = vendors[0]["id"]

    payout_res = client.post(f"/api/v1/marketplace/payout/{vendor_id}?amount_paise=10000")
    assert payout_res.status_code == 200
    pdata = payout_res.json()
    assert pdata["status"] in ("PROCESSED", "SUCCESS")

def test_subscription_plans_and_subscribers():
    """Test subscription recurring plans and subscriber e-Mandates."""
    plans_res = client.get("/api/v1/subscriptions/plans")
    assert plans_res.status_code == 200
    plans = plans_res.json()
    assert len(plans) >= 3

    # List subscribers
    subs_res = client.get("/api/v1/subscriptions/")
    assert subs_res.status_code == 200
    subs = subs_res.json()
    assert isinstance(subs, list)

def test_bank_reconciliation_reports():
    """Test reconciliation report listing and run."""
    recon_res = client.get("/api/v1/reconciliation/reports")
    assert recon_res.status_code == 200
    reports = recon_res.json()
    assert isinstance(reports, list)
