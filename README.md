<div align="center">

# 🛡 Shurokkha — Fraud Rider
### Real-Time Payment Gateway & Sentinel AI Fraud Radar

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Scikit-Learn](https://img.shields.io/badge/Sentinel_AI_ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](#)
[![AES-256](https://img.shields.io/badge/AES--256--GCM_Vault-06B6D4?style=for-the-badge&logo=protonmail&logoColor=white)](#)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_ACID-CC2927?style=for-the-badge&logo=database&logoColor=white)](#)
[![License MIT](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](LICENSE)

**Built by [Rakib](https://github.com/rakibdipu)**

</div>

---

## 📌 Project Overview

**Shurokkha** is a full-scale, production-grade **FinTech Payment Gateway** built entirely from scratch — covering every layer of how a real payment system works, from card tokenization to bank settlement.

Inspired by how **Stripe**, **Razorpay**, and **Juspay Hyperswitch** work internally.  
Every module below is live, tested end-to-end, and verified against a running FastAPI server.

---

## ✅ What's Built — 10 Core Modules

### 1. 💳 Checkout Engine & Payment Lifecycle
- Full multi-state payment lifecycle: `CREATED` → `PROCESSING` → `RISK_EVALUATED` → `3DS_PENDING` → `AUTHORIZED` → `CAPTURED` → `REFUNDED`
- Card tokenization with **AES-256-GCM encryption** — PAN is never stored in plaintext
- Real-time Sentinel AI risk scoring before every capture decision
- UPI QR code generation via `qrcodejs`

### 2. 🛡 Sentinel AI Fraud Radar
- **7 heuristic velocity & anomaly rules**: impossible travel speed, Tor/Proxy IP detection, BIN country mismatch, transaction velocity (>5 in 60s), high-risk merchant categories, large amount anomaly, card-not-present risk
- **ML Model**: `GradientBoostingClassifier` trained on 2,000 synthetic fraud vectors — produces a 0–100 risk score
- Combined score: **60% rules + 40% ML** → 3-tier decision:
  - `ALLOW` (score < 30) → Instant capture
  - `CHALLENGE` (score 30–69) → 3DS OTP step-up required
  - `BLOCK` (score ≥ 70) → Auto-rejected, funds go to `FRAUD_HOLD` ledger account
- Full risk breakdown returned with triggered rules + ML feature weights

### 3. ⚡ Smart Multi-Acquirer Router (Juspay Hyperswitch-style)
- Dynamic routing across **4 acquirers**: HDFC, ICICI, Stripe, Chase
- Routes based on live success rate, fees, and merchant category
- **Auto-Cascade Fallback**: if primary acquirer is DOWN, automatically retries through backup — zero customer drop
- Verified: HDFC DOWN → auto-cascaded to ICICI in the same request

### 4. 🏪 Marketplace Split Payments & Instant Payouts
- Stripe Connect-style **multi-vendor order splitting**
- Per-vendor commission deduction at the gateway level
- Instant disbursement to virtual bank accounts
- Single API call handles multi-party settlements

### 5. 🔄 Recurring Subscriptions & UPI AutoPay (e-Mandate)
- Monthly and annual **e-Mandate registration**
- Automated recurring billing cron scheduler
- **Dunning logic**: failed renewals retried with configurable backoff

### 6. ⚖️ Chargeback & Dispute Defense
- TC40 / SAFE fraud alert ingestion
- Disputed funds auto-locked in `FRAUD_HOLD` ledger account (escrow hold)
- Merchant evidence and delivery proof submission API
- Full dispute lifecycle tracking

### 7. 📒 Double-Entry Bookkeeping Ledger (ACID Integrity)
- Every transaction creates **balanced ledger entries** across 4 T-accounts:
  - `ACQUIRER_CLEARING`
  - `MERCHANT_PAYABLE`
  - `GATEWAY_FEE_REVENUE`
  - `FRAUD_HOLD`
- Mathematically enforced: **Σ Debits = Σ Credits** on every single transaction
- Balance sheet API with full account drill-down
- Verified: total ledger balanced at ₹3,17,352.00 across all test transactions

### 8. 🔔 Webhook Outbox & Dead Letter Queue
- **Transactional Outbox pattern** — webhooks written atomically with payment records
- **HMAC-SHA256 signed payloads** — merchant can verify authenticity
- Timestamp **anti-replay defense** — 300 second window
- Exponential backoff retry schedule: `5s → 30s → 2m → 10m`
- Failed events move to **DLQ** with manual replay API
- Events fired: `payment.captured`, `payment.failed`, `payment.refunded`, `fraud.blocked`

### 9. 🔍 Automated Bank Reconciliation
- Ingests bank clearing **settlement CSV batches**
- Classifies every record as: `MATCHED` / `AMOUNT_MISMATCH` / `MISSING_IN_BANK` / `EXTRA_IN_BANK`
- Generates structured reconciliation report stored in DB

### 10. 🔐 Security Layer
- **AES-256-GCM** with unique 12-byte nonce per card token
- **HMAC-SHA256** webhook signatures
- UUID-keyed **Idempotency Guard** — safe for mobile network retries
- Request deduplication at the API layer

---

## 📸 UI Screenshots

| Module | Preview |
|---|---|
| 💳 Checkout Simulator | ![](docs/assets/01_checkout_simulator.png) |
| ⚡ Smart Multi-Acquirer Router | ![](docs/assets/02_smart_routing_switch.png) |
| 🛡 Sentinel AI Fraud Radar | ![](docs/assets/03_sentinel_fraud_radar.png) |
| 🌍 Geo-Fraud Heatmap | ![](docs/assets/04_geo_heatmap.png) |
| 🏪 Marketplace Split Payments | ![](docs/assets/05_marketplace_splits.png) |
| 🔄 Subscriptions & UPI AutoPay | ![](docs/assets/06_subscriptions_autopay.png) |
| 📒 Double-Entry Ledger | ![](docs/assets/07_double_entry_ledger.png) |
| 🔔 Webhook Dispatcher | ![](docs/assets/08_webhook_dispatcher.png) |
| 🔍 Bank Reconciliation | ![](docs/assets/09_bank_reconciliation.png) |
| 📖 Swagger API Docs | ![](docs/assets/10_swagger_api_docs.png) |

---

## 🏛 System Architecture

```
  Merchant / Client
        │
        ▼
  Idempotency Guard ──► (duplicate? return cached response)
        │
        ▼
  AES-256-GCM Card Vault (tokenize PAN)
        │
        ▼
  ┌─── Sentinel AI Fraud Radar ───────────────────────┐
  │   7 Heuristic Rules + GradientBoosting ML Model   │
  │   Score: 0–100                                    │
  └────────────┬───────────────┬──────────────────────┘
               │               │              │
           ALLOW          CHALLENGE        BLOCK
               │            3DS OTP          │
               │               │         FRAUD_HOLD
               └───────────────┘
                       │
        Smart Multi-Acquirer Router
        HDFC → ICICI → Stripe → Chase
        (Auto-Cascade on Outage)
                       │
        ┌──────────────┴──────────────┐
        │                            │
  Double-Entry Ledger        Webhook Outbox
  (Σ Dr = Σ Cr enforced)     (HMAC-SHA256 + DLQ)
```

---

## 🧪 End-to-End Test Results

All 12 steps verified against a live running server:

| # | Test | Result |
|---|---|---|
| 1 | Server health & lifespan | ✅ `healthy` |
| 2 | Idempotent order creation & replay match | ✅ Same response returned |
| 3 | Direct capture — AES-256 Vault + Sentinel AI | ✅ Risk score 5/100, `ALLOW` |
| 4 | 3DS Step-Up Challenge — OTP generated & verified | ✅ `AUTHORIZED` after OTP |
| 5 | Sentinel Fraud Auto-Block | ✅ Risk score 90/100, `BLOCK`, zero merchant loss |
| 6 | Multi-Acquirer Auto-Cascade | ✅ HDFC DOWN → cascaded to ICICI |
| 7 | Marketplace Multi-Vendor Split Payments | ✅ 3 vendors + platform fee settled |
| 8 | Recurring Subscriptions & UPI e-Mandate | ✅ Plan created, billing triggered |
| 9 | Chargeback TC40 Alert & Dispute Defense | ✅ Funds escrowed in FRAUD_HOLD |
| 10 | Double-Entry Ledger Balance | ✅ Σ Dr = Σ Cr = ₹3,17,352.00 |
| 11 | Webhook Engine + HMAC Signature | ✅ Signed, retried, DLQ verified |
| 12 | Bank Settlement Reconciliation | ✅ MATCHED / MISMATCH classified |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI + Uvicorn |
| Database | SQLAlchemy 2.0 + SQLite (WAL mode, ACID) |
| ML Fraud Engine | Scikit-Learn `GradientBoostingClassifier` |
| Cryptography | `cryptography` (AES-GCM) + Python `hmac` |
| Frontend | Vanilla JS + Tailwind CSS + Chart.js + QRCode.js |

---

## ⚡ Quick Start

```bash
git clone https://github.com/rakibdipu/shurokkha-fraud-rider.git
cd shurokkha-fraud-rider

python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate        # Linux/macOS

pip install -r backend/requirements.txt

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Dashboard** → http://127.0.0.1:8000/
- **Swagger API Docs** → http://127.0.0.1:8000/docs

---

## 🧪 Test Cards

| Scenario | Card Number | CVV | Outcome |
|---|---|---|---|
| ✅ Instant Capture | `4111 1111 1111 1111` | `123` | Risk < 30 → `ALLOW` |
| ⚠️ 3DS OTP Step-Up | `4000 0000 0000 0002` | `111` | Risk 30–69 → OTP required |
| 🚫 AI Fraud Block | `4000 0000 0000 0069` | `000` | Risk ≥ 70 → `BLOCK` |

---

## 📁 Project Structure

```
shurokkha-fraud-rider/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # 10 REST API controllers
│   │   ├── core/             # AES-256 vault, HMAC signer, config
│   │   ├── ml/               # Fraud model training & inference
│   │   ├── models/           # SQLAlchemy ORM + Pydantic schemas
│   │   ├── services/         # Payment, fraud, split, ledger, webhook engines
│   │   └── main.py           # App startup & router setup
│   └── requirements.txt
├── frontend/
│   └── index.html            # Full SaaS dashboard (single-file SPA)
├── docs/assets/              # UI screenshots
└── README.md
```

---

<div align="center">
<br/>

**Built by [Rakib](https://github.com/rakibdipu)**

</div>
