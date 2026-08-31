# ⚡ RazorFlow Enterprise — Real-Time Payment Gateway & Sentinel AI Fraud Radar

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Machine Learning](https://img.shields.io/badge/ML%20Engine-GradientBoosting%20Classifier-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Security](https://img.shields.io/badge/Security-AES--256--GCM%20%2B%20HMAC--SHA256-blue.svg)](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
[![Accounting](https://img.shields.io/badge/Ledger-Double--Entry%20ACID-success.svg)](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **RazorFlow Enterprise** is an end-to-end, production-grade FinTech Payment Gateway engine inspired by **Stripe, Razorpay, and Juspay Hyperswitch**. It combines multi-acquirer smart routing, auto-cascade failover, AI-driven fraud prevention, double-entry ledger bookkeeping, marketplace split payouts, recurring subscriptions, dispute defense, transactional outbox webhooks, and automated bank reconciliation.

---

## 🏛 System Architecture & Workflow

```
                          ┌────────────────────────┐
                          │   Client / Merchant    │
                          │   (Checkout SDK / API) │
                          └───────────┬────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │       Idempotency Guard & Card Vault             │
             │     (AES-256-GCM Tokenization & Hash Key)        │
             └────────────────────────┬─────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │            Sentinel AI Fraud Radar               │
             │   ┌──────────────────────┬───────────────────┐   │
             │   │ 7 Heuristic Rules    │ ML Gradient Boost │   │
             │   │ (Velocity & Anomaly) │ (Risk Prob 0-100) │   │
             │   └──────────────────────┴───────────────────┘   │
             │          Decision Matrix: 60% Rule + 40% ML      │
             └──────┬─────────────────┬───────────────────┬─────┘
                    │                 │                   │
         [Score < 30]    [Score 30-69]    [Score >= 70]
              ALLOW         CHALLENGE             BLOCK
                    │                 │                   │
                    │        ┌────────▼────────┐          ▼
                    │        │ 3DS 2.0 OTP Hub │   [Transaction Blocked]
                    │        └────────┬────────┘
                    ▼                 ▼
             ┌──────────────────────────────────────────────────┐
             │      Smart Multi-Acquirer Routing Switch         │
             │  (Dynamic Cost & Health Routing with Cascade)   │
             │                                                  │
             │   ┌────────┐    ┌────────┐    ┌────────┐    ┌─── │
             │   │  HDFC  │ ──►│ ICICI  │ ──►│ STRIPE │ ──►│ ...│
             │   └────────┘    └────────┘    └────────┘    └─── │
             └────────────────────────┬─────────────────────────┘
                                      │
                         [Bank Capture & Settlement]
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
   ┌─────────────────────────────────┐ ┌─────────────────────────────────┐
   │    Double-Entry Ledger Engine   │ │   Transactional Outbox Webhook  │
   │   (Strict Σ Dr == Σ Cr ACID)    │ │   (HMAC-SHA256 & DLQ Worker)    │
   └─────────────────────────────────┘ └─────────────────────────────────┘
```

---

## 🚀 10 Enterprise FinTech Modules

### 1. 💳 Core Payment Orchestration Engine
- Full payment state machine (`CREATED` ➔ `PROCESSING` ➔ `RISK_EVALUATED` ➔ `3DS_PENDING` / `AUTHORIZED` ➔ `CAPTURED` ➔ `REFUNDED` / `BLOCKED`).
- Card Vault with **AES-256-GCM** encryption for PANs, masking (`411111######1111`), BIN extraction, and brand detection (Visa, Mastercard, Amex, Rupay).
- Instant **Dynamic UPI QR** generator with ISO standard string parsing.

### 2. ⚡ Smart Multi-Acquirer Router & Auto-Cascade Switch (Juspay Hyperswitch)
- Dynamic traffic routing across **HDFC SmartGateway, ICICI Bank Core, Stripe Global, and Chase Paymentech**.
- **Auto-Cascade Fallback**: When an acquirer encounters latency spikes or `BANK_TIMEOUT`, the engine automatically re-routes the transaction to a healthy secondary bank without dropping the customer.

### 3. 🛡 Sentinel AI Fraud Radar
- **7 Real-Time Heuristic Rules**:
  1. `velocity_1min`: Max transactions per minute from IP (>3)
  2. `velocity_1hr`: Max transactions per hour from card BIN (>10)
  3. `amount_spike`: Amount spike multiplier vs 30-day average (>5x)
  4. `impossible_travel`: Distance >= 500 km under 30 minutes
  5. `high_risk_bin`: Stolen / leaked card registry match
  6. `proxy_ip`: Known VPN/Proxy/Tor exit node match
  7. `odd_hour`: High-risk time window (2am–4am UTC)
- **Trained Machine Learning Classifier**: Scikit-Learn `GradientBoostingClassifier` evaluated on multi-dimensional feature vectors.
- **Dynamic Decision Matrix**:
  - `ALLOW` (Score < 30): Zero-latency direct authorization.
  - `CHALLENGE` (Score 30-69): Step-up 3D-Secure 2.0 biometric/OTP verification.
  - `BLOCK` (Score >= 70): Auto-rejection preventing stolen card fraud.

### 4. 🌍 Global Real-Time Geo-Fraud Heatmap & Telemetry
- Animated HTML5 canvas radar rendering transaction origin nodes (Dhaka, London, New York, Singapore, Proxy nodes).
- Live intercept stream displaying IP, latency, geographic coordinates, and risk tier.

### 5. 🏪 Marketplace Split Payments & Instant Payouts (Stripe Connect / Razorpay Route)
- Dynamic checkout splitting across multiple sub-merchants / vendors.
- Automated platform commission fee deduction.
- Instant merchant wallet payouts to virtual bank accounts.

### 6. 🔄 Recurring Subscriptions & UPI AutoPay Engine
- Monthly and annual recurring billing tiers with e-Mandate registration.
- Automated billing cycle advancement and pre-debit notifications.
- Dunning retry manager for failed subscription renewals.

### 7. ⚖️ Disputes, Chargebacks & TC40/SAFE Defense Center
- Visa/Mastercard chargeback alerts and issuer fraud notifications.
- Automatic escrow hold placing disputed funds in `FRAUD_HOLD`.
- Evidence submission portal (proof of delivery, invoice tracking) to win chargeback representments.

### 8. 📒 Double-Entry Bookkeeping Ledger
- Strict immutable T-account journal:
  - `ACQUIRER_CLEARING` (Asset)
  - `MERCHANT_PAYABLE` (Liability)
  - `GATEWAY_FEE_REVENUE` (Revenue - 2%)
  - `FRAUD_HOLD` (Escrow Liability)
- Automated verification asserting that `Sum(Debits) == Sum(Credits)` on every transaction.

### 9. 🔔 Transactional Outbox Webhook Dispatcher
- Cryptographically signed with **HMAC-SHA256** (`t={timestamp},v1={hash}`).
- Anti-replay attack timestamp window defense (300s).
- Autonomous background worker thread with exponential backoff retries (`5s`, `30s`, `2m`, `10m`), Dead Letter Queue (DLQ), and manual replay endpoints.

### 10. 🔍 Automated End-of-Day Bank Reconciliation
- Ingests bank clearing settlement batches (JSON / CSV).
- Automated 4-way matching against gateway ledger.
- Classifies records into: `MATCHED`, `AMOUNT_MISMATCH`, `MISSING_IN_BANK`, and `EXTRA_IN_BANK`.

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python REST API |
| **Database & ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) + SQLite WAL | Synchronous ACID transactions with Write-Ahead Logging |
| **Machine Learning** | [Scikit-Learn](https://scikit-learn.org/) + [Joblib](https://joblib.readthedocs.io/) | GradientBoosting fraud probability model |
| **Cryptography** | [Cryptography (AESGCM)](https://cryptography.io/) + `hmac` | AES-256-GCM card tokenization & HMAC-SHA256 signatures |
| **Frontend UI** | Modern Vanilla JS + [Tailwind CSS](https://tailwindcss.com/) + [Chart.js](https://www.chartjs.org/) + [QRCode.js](https://davidshimjs.github.io/qrcodejs/) | Clean SaaS Light Mode Dashboard (No build tool needed) |

---

## ⚡ Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/rakibdipu/razorflow-gateway.git
cd razorflow-gateway
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

### 3. Run the Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Access Dashboard & API Docs
- 🖥 **Unified Web Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 📖 **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health Endpoint:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Interactive Test Presets & Cards

| Card Preset | Card Number | Expiry | CVV | Risk Tier | Behavior |
|---|---|---|---|---|---|
| **ALLOW Card** | `4111 1111 1111 1111` | `12/27` | `123` | `ALLOW` (Risk < 30) | Instant Straight-Through Capture |
| **3DS Challenge** | `4000 0000 0000 0002` | `12/27` | `123` | `CHALLENGE` (Risk 30–69) | Requires 6-Digit 3DS OTP verification |
| **BLOCK Card** | `4000 0000 0000 0069` | `12/27` | `123` | `BLOCK` (Risk >= 70) | Rejected immediately by Fraud Radar |

---

## 📁 Repository Structure

```
razorflow-gateway/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── orders.py           # Order creation & idempotency
│   │   │   ├── payments.py         # Initiation, 3DS & capture
│   │   │   ├── fraud.py            # Fraud radar & heuristic stats
│   │   │   ├── router_api.py       # Smart routing & failover switch
│   │   │   ├── marketplace.py      # Marketplace splits & payouts
│   │   │   ├── subscriptions.py    # Subscriptions & AutoPay engine
│   │   │   ├── disputes.py         # Chargebacks & evidence defense
│   │   │   ├── ledger.py           # Double-entry balance sheet
│   │   │   ├── webhooks.py         # Webhook outbox & DLQ replay
│   │   │   └── reconciliation.py   # EOD bank statement matcher
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic v2 settings & thresholds
│   │   │   ├── database.py         # SQLAlchemy engine with SQLite WAL
│   │   │   └── security.py         # CardVault (AES-256-GCM) & HMACSigner
│   │   ├── ml/
│   │   │   ├── train_model.py      # GBM model trainer & inference
│   │   │   └── fraud_model.pkl     # Serialized classifier pipeline
│   │   ├── models/
│   │   │   ├── models.py           # 14 SQLAlchemy ORM tables
│   │   │   └── schemas.py          # Pydantic v2 DTOs & response models
│   │   ├── services/
│   │   │   ├── payment_engine.py   # Master payment orchestrator
│   │   │   ├── smart_router.py     # Multi-acquirer auto-cascade switch
│   │   │   ├── fraud_engine.py     # Sentinel heuristic & ML radar
│   │   │   ├── split_engine.py     # Multi-vendor split calculations
│   │   │   ├── subscription_engine.py # Recurring billing scheduler
│   │   │   ├── dispute_engine.py   # Chargebacks & escrow manager
│   │   │   ├── ledger_service.py   # Double-entry journal builder
│   │   │   ├── webhook_dispatcher.py # Outbox worker & DLQ manager
│   │   │   └── recon_service.py    # Bank CSV settlement matcher
│   │   └── main.py                 # FastAPI application & startup lifespan
│   └── requirements.txt            # Pinned dependencies
├── frontend/
│   └── index.html                  # Single-page Light Mode SaaS Dashboard
├── .gitignore                      # Git ignore rules
└── README.md                       # Comprehensive documentation
```

---

## 🔒 Security & Compliance Principles
- **PCI-DSS Level 1 Principles**: Raw PANs are never stored in plaintext. PANs are encrypted using authenticated **AES-256-GCM** with a unique 12-byte initialization vector (nonce) per entry.
- **HMAC Signatures & Anti-Replay**: Outgoing webhooks are signed using SHA-256 HMAC with timestamps. Receivers verify timestamps within a strict 300-second window to prevent replay attacks.
- **Double-Entry Balance Guarantee**: Every financial transfer is posted across matching Debit and Credit T-accounts, enforcing strict mathematical conservation of money.

---

## 📄 License
Distributed under the **MIT License**.
