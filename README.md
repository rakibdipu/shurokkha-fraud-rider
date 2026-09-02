<div align="center">

# 🛡️ Shurokkha — Fraud Rider
### Real-Time Payment Gateway & Sentinel AI Fraud Radar

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Scikit-Learn](https://img.shields.io/badge/Sentinel_AI_ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](#)
[![AES-256](https://img.shields.io/badge/AES--256--GCM_Vault-06B6D4?style=for-the-badge&logo=protonmail&logoColor=white)](#)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_ACID-CC2927?style=for-the-badge&logo=database&logoColor=white)](#)
[![License MIT](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)](LICENSE)

**Architected and Built by [Rakib](https://github.com/rakibdipu)**

[Live Dashboard](http://127.0.0.1:8000/) • [Interactive Swagger Docs](http://127.0.0.1:8000/docs) • [Architecture](#-system-architecture) • [How to Run](#-complete-how-to-run-guide)

</div>

---

## 📌 Executive Summary

**Shurokkha Fraud Rider** is a production-grade, full-scale **FinTech Payment Gateway & AI Fraud Defense System** engineered from first principles in Python and modern web standards. 

Designed following the internal enterprise architectures of **Stripe**, **Razorpay**, and **Juspay Hyperswitch**, Shurokkha encapsulates the entire payment lifecycle:
- **Zero-knowledge PCI-DSS tokenization** via hardware-grade AES-256-GCM.
- **Sub-50ms Sentinel AI risk scoring** using a hybrid blend of 7 heuristic velocity interceptors and a Gradient Boosting Machine (GBM) classifier.
- **Smart multi-acquirer routing** with automated zero-drop cascading failover.
- **Mathematically balanced double-entry ledger** guaranteeing strict ACID financial parity ($\sum 	ext{Dr} = \sum 	ext{Cr}$).
- **Transactional Outbox webhook dispatcher** with cryptographically signed HMAC-SHA256 headers and Dead Letter Queue (DLQ) replay protection.

---

## 🚀 Complete "How to Run" Guide

Follow these step-by-step instructions to clone, configure, seed, and launch the entire gateway locally in under 60 seconds.

### 📋 Prerequisites
- **Python 3.10, 3.11, 3.12, or 3.13** installed ([python.org](https://www.python.org/downloads/))
- **Git** installed ([git-scm.com](https://git-scm.com/))
- Modern Web Browser (Chrome, Edge, Firefox, Brave, Safari)

---

### ⚡ Step 1: Clone the Repository
```bash
git clone https://github.com/rakibdipu/shurokkha-fraud-rider.git
cd shurokkha-fraud-rider
```

---

### 📦 Step 2: Set Up Virtual Environment & Dependencies

#### On Windows (PowerShell / CMD):
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.env\Scripts\Activate.ps1
# (If using CMD: .env\Scriptsctivate.bat)

# Upgrade pip & install all required dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

> **Note for Windows PowerShell:** If script execution is restricted, run:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

#### On Linux / macOS:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 🧠 Step 3: Train the Sentinel AI Fraud Detection Model (Optional / Auto)
The system includes a pre-trained ML model (`backend/app/ml/fraud_model.pkl`). If you wish to retrain or generate fresh synthetic fraud training data:
```bash
python backend/app/ml/train_model.py
```
*Outputs: 2,000 synthetic transaction vectors, 80/20 train-test split, GradientBoosting classification report, and serialized model artifact.*

---

### 🌱 Step 4: Seed Realistic FinTech Demo Data
Seed rich historical transactions, active subscription e-Mandates, marketplace vendor accounts, disputes, and reconciliation batches:
```bash
python scripts/seed_data.py
```
*Outputs: 200+ balanced transactions, 3 merchants, 4 acquirer switches, 3 subscription tiers, 5 active e-mandates, and verified double-entry balances.*

---

### ▶️ Step 5: Start the Backend Gateway Server

#### Quick Command:
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

You will see:
```text
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### 🌐 Step 6: Access the Dashboard & API Documentation
Open your browser and navigate to:

| Interface | URL | Purpose |
|---|---|---|
| **🎨 Shurokkha SaaS Dashboard** | **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** | Full 10-module single-page app with living mesh canvas, live charts, EMV card simulator & telemetry stream |
| **📖 Interactive OpenAPI Docs** | **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** | Live Swagger UI for executing and testing all REST API endpoints interactively |
| **📑 ReDoc Specifications** | **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)** | Clean structural API documentation |
| **💚 Health Check Probe** | **[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)** | Cluster health, uptime, and app version |

---

### 🧪 Step 7: Run the Automated 12-Card Live Test Bench
To execute the comprehensive automated test suite across 12 diverse payment cards (Visa, Mastercard, Amex, RuPay, Discover) against the running server:
```bash
python scratch/test_12_cards.py
```

---

## 💳 Test Card Credentials & Behavior Matrix

The platform includes built-in test cards and heuristic triggers:

| Scenario | Card Brand | Card Number (PAN) | Expiry | CVV | Sentinel AI Score | Decision Tier | Gateway Action |
|---|---|---|---|---|:---:|:---:|---|
| **Instant Domestic Capture** | Visa Classic | `4111 1111 1111 1111` | `12/2027` | `123` | **5 / 100** | `ALLOW` | Direct 1-click capture, 0ms hold |
| **Commercial Line** | Visa Infinite | `4242 4242 4242 4242` | `09/2028` | `321` | **0 / 100** | `ALLOW` | Direct authorization & capture |
| **Verified Purchase** | Mastercard Gold | `5555 5555 5555 4444` | `11/2026` | `555` | **0 / 100** | `ALLOW` | Captured via domestic switch |
| **High-Value Corporate** | Amex Centurion | `3782 8224 6310 005` | `08/2027` | `1005` | **0 / 100** | `ALLOW` | Premium corporate line authorized |
| **National Payment Switch** | RuPay Debit | `6070 1234 5678 9012` | `01/2030` | `912` | **0 / 100** | `ALLOW` | Routed to ICICI core switch |
| **3DS Step-Up Challenge** | Visa 3DS Test | `4000 0000 0000 0002` | `06/2026` | `456` | **50 / 100** | `CHALLENGE` | 3DS OTP generated; verified & captured |
| **Velocity Spike Challenge** | Mastercard 3DS | `5200 8282 0192 3819` | `03/2028` | `282` | **35 / 100** | `CHALLENGE` | Multi-attempt challenge triggered |
| **Stolen Blacklist Card** | Visa Flagged | `4000 0000 0000 0069` | `03/2025` | `000` | **90 / 100** | `BLOCK` | **Auto-Rejected**; 0 chargeback loss |

---

## 🏛️ System Architecture

```
   ┌──────────────────────────────────────────────────────────────┐
   │                  Merchant / Client Request                   │
   └──────────────────────────────┬───────────────────────────────┘
                                  │ (HTTP POST / API Key)
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                   UUID Idempotency Guard                     │
   │  - Checks existing keys to prevent double-charging on replay │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                 AES-256-GCM Card Vault                       │
   │  - Generates 12-byte nonce; encrypts PAN; extracts BIN & L4  │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
   ┌──────────────────────────────────────────────────────────────┐
   │                Sentinel AI Hybrid Fraud Radar                │
   │  ├─ Tier 1: 7 Real-Time Heuristic Rule Interceptors          │
   │  │   • Velocity/min • Velocity/hr • Geo Distance Anomaly     │
   │  │   • Amount Spike • Proxy/Tor IP • Odd Hours • Card BIN    │
   │  ├─ Tier 2: Gradient Boosting Classifier (0-100 ML Score)    │
   │  └─ Tier 3: Decision Matrix (60% Heuristic + 40% ML)         │
   └──────────────┬───────────────┬──────────────────────┬────────┘
                  │               │                      │
             Score < 30      Score 30-69            Score ≥ 70
                  │               │                      │
                  ▼               ▼                      ▼
             [ ALLOW ]      [ CHALLENGE ]            [ BLOCK ]
           Direct Capture   3DS 2.0 Biometric/OTP   Auto-Rejected
                  │          Authentication         Funds to Escrow
                  │               │
                  └───────┬───────┘
                          │
                          ▼
   ┌──────────────────────────────────────────────────────────────┐
   │             Smart Multi-Acquirer Router & Switch             │
   │   HDFC SmartGateway ──► ICICI Direct ──► Stripe ──► Chase    │
   │   (Live Uptime & Success Rate Routing + Auto-Cascade)        │
   └──────────────────────┬───────────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
 ┌─────────────────────┐     ┌──────────────────────────────────┐
 │ Double-Entry Ledger │     │  Transactional Outbox Webhooks   │
 │ • ACQUIRER_CLEARING │     │  • HMAC-SHA256 Payload Signature │
 │ • MERCHANT_PAYABLE  │     │  • 300s Anti-Replay Timestamp    │
 │ • GATEWAY_FEE (2%)  │     │  • Exponential Backoff Retries   │
 │ • FRAUD_HOLD        │     │  • Dead Letter Queue (DLQ)       │
 │   Σ Dr == Σ Cr      │     └──────────────────────────────────┘
 └─────────────────────┘
```

---

## 🧩 The 10 Core Architectural Modules

### 1. 💳 Checkout Engine & Payment Lifecycle
- Full state-machine orchestrator: `CREATED` $ightarrow$ `PROCESSING` $ightarrow$ `RISK_EVALUATED` $ightarrow$ `3DS_PENDING` $ightarrow$ `AUTHORIZED` $ightarrow$ `CAPTURED` $ightarrow$ `REFUNDED`.
- Hardware-grade **AES-256-GCM** encryption with unique 12-byte initialization vectors per token. Plaintext PAN is never written to disk or database.
- Dynamic UPI QR Code generator (`qrcodejs`) for seamless mobile app intent payments.

### 2. 🛡️ Sentinel AI Hybrid Fraud Radar
- **Heuristic Rule Interceptors**:
  1. `velocity_1min`: Flags $>3$ transactions per minute from the same IP address (+40 pts).
  2. `velocity_1hr`: Flags $>10$ transactions per hour from the same card BIN (+25 pts).
  3. `amount_spike`: Detects $>5	imes$ deviations against the customer's 30-day moving average (+30 pts).
  4. `impossible_travel`: Flags multi-location authorization attempts faster than aircraft travel speed (+50 pts).
  5. `high_risk_bin`: Flags blacklisted or compromised BIN ranges (+35 pts).
  6. `proxy_ip`: Detects known proxy, VPN, and Tor exit nodes (+20 pts).
  7. `odd_hour`: Evaluates 02:00–04:00 UTC high-risk time windows (+10 pts).
- **Gradient Boosting Machine (GBM)**: Scikit-Learn pipeline extracting feature weights in real time.

### 3. ⚡ Smart Multi-Acquirer Router (Auto-Cascade Failover)
- Evaluates live latency, processor fee percentages, and bank health scores across **HDFC**, **ICICI**, **Stripe**, and **Chase**.
- **Zero-Drop Auto-Cascade**: If an acquirer experiences network failure or outage (`DOWN`), the transaction automatically cascades to the secondary switch without terminating the customer checkout session.

### 4. 🏪 Marketplace Split Payments & Instant Disbursements
- Stripe Connect / Razorpay Route multi-vendor architecture.
- Calculates automated platform commissions (e.g., 8–12%) and routes net balances to vendor balances.
- Instant single-call disbursement to virtual bank accounts.

### 5. 🔄 Recurring Subscriptions & UPI AutoPay (e-Mandate)
- Automated e-Mandate registration for monthly, quarterly, and annual billing intervals.
- Dunning lifecycle engine with automated retry cron schedules for handling card expiration and temporary payment failures.

### 6. ⚖️ Chargeback & Dispute Defense Center
- TC40 and SAFE fraud alert ingestion pipeline.
- Automatically locks disputed amounts into a `FRAUD_HOLD` escrow ledger account.
- Evidence submission module supporting invoice proof, delivery tracking, and issuer contestation.

### 7. 📒 Double-Entry Bookkeeping Ledger (ACID Financial Integrity)
- Every transaction creates immutable debit and credit journal entries across 4 fundamental T-accounts:
  - `ACQUIRER_CLEARING`: Asset account tracking receivables from bank switches.
  - `MERCHANT_PAYABLE`: Liability account tracking owed merchant settlement.
  - `GATEWAY_FEE_REVENUE`: Revenue account capturing gateway processing fees (2%).
  - `FRAUD_HOLD`: Escrow account locking disputed or high-risk funds.
- **Mathematical Invariant**: $\sum 	ext{Debits} \equiv \sum 	ext{Credits}$ strictly enforced before database commit.

### 8. 🔔 Webhook Transactional Outbox & Dead Letter Queue (DLQ)
- Atomic event generation adhering to the **Transactional Outbox Pattern**.
- Payload security: `X-Shurokkha-Signature: t={timestamp},v1={hmac_sha256}`.
- Replay attack mitigation: 300-second strict window.
- Exponential backoff schedule: 5s $ightarrow$ 30s $ightarrow$ 2m $ightarrow$ 10m $ightarrow$ **DLQ** with manual operator replay.

### 9. 🔍 Automated End-of-Day Bank Statement Reconciliation
- Ingests bank clearing settlement batches (JSON / CSV).
- Multi-way matching engine classifying line items into:
  - `MATCHED`: Gateway ledger matches bank clearing record 100%.
  - `AMOUNT_MISMATCH`: Bank settlement differs from authorized amount (e.g., hidden interchange fee deductions).
  - `MISSING_IN_BANK`: Transaction captured on gateway but missing from bank clearing report.

### 10. 🔐 Cryptographic & Idempotency Security Layer
- Idempotency guard utilizing UUID keys to cache and return identical responses on client-side network retries.
- Zero-logging policy for raw CVV and full PAN credentials.

---

## 📸 Interactive Dashboard Showcase

| Module | High-Resolution UI Preview |
|---|---|
| **01. Checkout Simulator** | ![](docs/assets/01_checkout_simulator.png) |
| **02. Smart Multi-Acquirer Router** | ![](docs/assets/02_smart_routing_switch.png) |
| **03. Sentinel AI Fraud Radar** | ![](docs/assets/03_sentinel_fraud_radar.png) |
| **04. Geo-Fraud Heatmap & Telemetry** | ![](docs/assets/04_geo_heatmap.png) |
| **05. Marketplace Split Payments** | ![](docs/assets/05_marketplace_splits.png) |
| **06. Subscriptions & UPI AutoPay** | ![](docs/assets/06_subscriptions_autopay.png) |
| **07. Double-Entry Ledger** | ![](docs/assets/07_double_entry_ledger.png) |
| **08. Webhook Outbox & DLQ** | ![](docs/assets/08_webhook_dispatcher.png) |
| **09. Bank Statement Reconciliation** | ![](docs/assets/09_bank_reconciliation.png) |
| **10. OpenAPI Swagger Docs** | ![](docs/assets/10_swagger_api_docs.png) |

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
|---|---|---|
| **Core Framework** | **FastAPI 0.141+** | High-performance asynchronous REST API framework |
| **Server Engine** | **Uvicorn 0.52+** | Production ASGI server implementation |
| **Database & ORM** | **SQLAlchemy 2.0** + **SQLite (WAL Mode)** | ACID transactional persistence with write-ahead logging |
| **Machine Learning** | **Scikit-Learn 1.7+** | GradientBoostingClassifier fraud prediction engine |
| **Data Processing** | **Pandas 2.3+** & **NumPy 2.2+** | Feature engineering and matrix vectorization |
| **Cryptography** | **Python `cryptography`** | Hardware-grade AES-256-GCM AEAD encryption |
| **Integrity & Signatures** | **HMAC-SHA256** | Webhook payload tampering and replay defense |
| **Frontend UI** | **Vanilla JS + Tailwind CSS + Chart.js** | Single-Page Application (SPA) with living particle canvas |

---

## 🔧 Configuration Reference (`.env`)

You can customize the platform by creating a `.env` file in the root or `backend/` directory:

```env
# Application Settings
APP_NAME="Shurokkha Fraud Rider"
DEBUG=True

# Cryptographic Keys (Must be 32-byte secret for production AES-256)
SECRET_KEY="shurokkha-aes-256-gcm-master-key-32-bytes"
HMAC_SECRET="shurokkha-hmac-webhook-sha256-secret-key"
API_KEY_HEADER="X-Shurokkha-API-Key"

# Fraud Thresholds
FRAUD_VELOCITY_MAX_PER_MINUTE=3
FRAUD_VELOCITY_MAX_PER_HOUR=10
FRAUD_AMOUNT_SPIKE_MULTIPLIER=5.0
FRAUD_ALLOW_THRESHOLD=30
FRAUD_BLOCK_THRESHOLD=70
FRAUD_IMPOSSIBLE_TRAVEL_MINUTES=30

# Webhook Retries & Replay Defense
WEBHOOK_RETRY_DELAYS=[5, 30, 120, 600]
WEBHOOK_REPLAY_WINDOW_SECONDS=300
WEBHOOK_TIMEOUT_SECONDS=10

# Gateway Processing Fee
GATEWAY_FEE_PERCENT=2.0
```

---

## ❓ Troubleshooting & FAQs

#### Q1: "Port 8000 is already in use" error?
**Solution:** Free port 8000 or run on another port:
- **Windows (PowerShell):**  
  `$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; if ($p) { Stop-Process -Id $p.OwningProcess -Force }`
- **Linux/macOS:**  
  `lsof -ti:8000 | xargs kill -9`
- Or launch on port 8080: `uvicorn app.main:app --host 127.0.0.1 --port 8080`

#### Q2: Can this integrate with real live banks?
**Yes!** The system is built with modular adapter interfaces (`app/services/smart_router.py` & `app/services/bank_simulator.py`). To connect live bank APIs (e.g., Visa Direct, Mastercard MPGS, CyberSource, HDFC SmartGateway, bKash/Nagad PGW), simply substitute the simulator with the bank's HTTP/ISO-8583 endpoints and inject your production merchant credentials.

#### Q3: How is double-entry ledger balance guaranteed?
Every captured payment, refund, dispute hold, and fee split posts debit and credit rows within a single atomic database transaction. An integrity check asserts $\sum 	ext{Debits} == \sum 	ext{Credits}$ before committing to disk.

---

<div align="center">
<br/>

**Built with pride by [Rakib](https://github.com/rakibdipu)**  
*Empowering ultra-secure, fraud-resistant FinTech infrastructure.*

</div>
