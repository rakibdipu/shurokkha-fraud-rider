# ⚡ RazorFlow Enterprise — Real-Time Payment Gateway & Sentinel AI Fraud Radar

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Machine Learning](https://img.shields.io/badge/ML%20Engine-GradientBoosting%20Classifier-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![Security](https://img.shields.io/badge/Security-AES--256--GCM%20%2B%20HMAC--SHA256-blue.svg)](https://en.wikipedia.org/wiki/Galois/Counter_Mode)
[![Accounting](https://img.shields.io/badge/Ledger-Double--Entry%20ACID-success.svg)](https://en.wikipedia.org/wiki/Double-entry_bookkeeping)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **RazorFlow Enterprise** is an end-to-end, production-grade FinTech Payment Gateway engine inspired by **Stripe, Razorpay, and Juspay Hyperswitch**. It combines multi-acquirer smart routing, auto-cascade failover, AI-driven fraud prevention, double-entry ledger bookkeeping, marketplace split payouts, recurring subscriptions, dispute defense, transactional outbox webhooks, and automated bank reconciliation.

---

## 📸 Interactive Showcase & Visual Tour

### 1. 💳 Checkout Simulator & Interactive Presets
Real-time card tokenization with AES-256-GCM vault, instant UPI Dynamic QR, and live transaction risk telemetry.
![Checkout Simulator](docs/assets/01_checkout_simulator.png)

---

### 2. ⚡ Smart Multi-Acquirer Router & Auto-Cascade Switch
Dynamic cost & health-based traffic routing across **HDFC, ICICI, Stripe, and Chase** with automated zero-downtime failover.
![Smart Routing & Auto-Cascade](docs/assets/02_smart_routing_switch.png)

---

### 3. 🛡 Sentinel AI Fraud Radar & Decision Matrix
7 heuristic velocity/anomaly rules combined with a trained `GradientBoosting` ML classifier (`ALLOW`, `3DS CHALLENGE`, `BLOCK`).
![Sentinel Fraud Radar](docs/assets/03_sentinel_fraud_radar.png)

---

### 4. 🌍 Global Real-Time Geo-Fraud Heatmap & Telemetry
Live HTML5 canvas radar tracking global transaction origins, Tor/Proxy anomalies, and impossible travel speeds.
![Geo Heatmap](docs/assets/04_geo_heatmap.png)

---

### 5. 🏪 Marketplace Split Payments & Instant Payouts (Stripe Connect Style)
Multi-vendor order splitting, platform commission deduction, and instant merchant bank payouts.
![Marketplace Splits](docs/assets/05_marketplace_splits.png)

---

### 6. 🔄 Recurring Subscriptions & UPI AutoPay Studio
Subscription plan management, customer e-Mandate registration, and automated recurring billing cron.
![Subscriptions & AutoPay](docs/assets/06_subscriptions_autopay.png)

---

### 7. 📒 Double-Entry Bookkeeping Ledger
Strict immutable T-accounts journal (`ACQUIRER_CLEARING`, `MERCHANT_PAYABLE`, `GATEWAY_FEE_REVENUE`, `FRAUD_HOLD`) verifying $\sum 	ext{Dr} = \sum 	ext{Cr}$.
![Double-Entry Ledger](docs/assets/07_double_entry_ledger.png)

---

### 8. 🔔 Transactional Outbox Webhook Dispatcher
HMAC-SHA256 cryptographically signed webhook delivery with anti-replay timestamps and Dead Letter Queue (DLQ) replay.
![Webhook Dispatcher](docs/assets/08_webhook_dispatcher.png)

---

### 9. 🔍 Automated End-of-Day Bank Statement Reconciliation
4-way automated clearing reconciliation classifying bank batches into `MATCHED`, `AMOUNT_MISMATCH`, and `MISSING_IN_BANK`.
![Bank Reconciliation](docs/assets/09_bank_reconciliation.png)

---

### 10. 📖 Interactive OpenAPI Swagger Documentation
Over 25+ production REST endpoints organized across 10 modular controllers.
![OpenAPI Swagger Docs](docs/assets/10_swagger_api_docs.png)

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

## 🛠 Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python REST API |
| **Database & ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) + SQLite WAL | Synchronous ACID transactions with Write-Ahead Logging |
| **Machine Learning** | [Scikit-Learn](https://scikit-learn.org/) + [Joblib](https://joblib.readthedocs.io/) | GradientBoosting fraud probability model |
| **Cryptography** | [Cryptography (AESGCM)](https://cryptography.io/) + `hmac` | AES-256-GCM card tokenization & HMAC-SHA256 signatures |
| **Frontend UI** | Modern Vanilla JS + [Tailwind CSS](https://tailwindcss.com/) + [Chart.js](https://www.chartjs.org/) + [QRCode.js](https://davidshimjs.github.io/qrcodejs/) | Clean SaaS Light Mode Dashboard (Zero build tools needed) |

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
├── docs/
│   └── assets/                     # High-resolution UI screenshots & diagrams
│       ├── 01_checkout_simulator.png
│       ├── 02_smart_routing_switch.png
│       ├── 03_sentinel_fraud_radar.png
│       ├── 04_geo_heatmap.png
│       ├── 05_marketplace_splits.png
│       ├── 06_subscriptions_autopay.png
│       ├── 07_double_entry_ledger.png
│       ├── 08_webhook_dispatcher.png
│       ├── 09_bank_reconciliation.png
│       └── 10_swagger_api_docs.png
├── backend/
│   ├── app/
│   │   ├── api/v1/                 # 10 modular REST API controllers
│   │   ├── core/                   # Security (AES-256/HMAC), config & database
│   │   ├── ml/                     # Trained GradientBoosting fraud classifier
│   │   ├── models/                 # 14 SQLAlchemy ORM tables & Pydantic DTOs
│   │   ├── services/               # Core payment, routing, split, sub & dispute engines
│   │   └── main.py                 # FastAPI application lifespan & router mounts
│   └── requirements.txt            # Pinned dependencies
├── frontend/
│   └── index.html                  # Single-page SaaS Light Mode Dashboard
├── .gitignore                      # Git ignore rules
└── README.md                       # Illustrated documentation
```

---

## 🔒 Security & Compliance Principles
- **PCI-DSS Level 1 Principles**: Raw PANs are never stored in plaintext. PANs are encrypted using authenticated **AES-256-GCM** with a unique 12-byte initialization vector (nonce) per entry.
- **HMAC Signatures & Anti-Replay**: Outgoing webhooks are signed using SHA-256 HMAC with timestamps. Receivers verify timestamps within a strict 300-second window to prevent replay attacks.
- **Double-Entry Balance Guarantee**: Every financial transfer is posted across matching Debit and Credit T-accounts, enforcing strict mathematical conservation of money.

---

## 📄 License
Distributed under the **MIT License**.
