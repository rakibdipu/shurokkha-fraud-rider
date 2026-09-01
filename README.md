<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,19,20&height=220&section=header&text=Shurokkha&fontSize=68&fontAlignY=36&fontColor=ffffff&desc=Real-Time%20Payment%20Gateway%20%26%20Sentinel%20AI%20Fraud%20Radar&descAlignY=58&descSize=19&animation=fadeIn" width="100%"/>

<br/>

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11+-0EA5E9?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Sentinel AI](https://img.shields.io/badge/Sentinel_AI-10B981?style=for-the-badge&logo=scikit-learn&logoColor=white)](#)
[![AES-256-GCM](https://img.shields.io/badge/AES--256--GCM_Vault-06B6D4?style=for-the-badge&logo=protonmail&logoColor=white)](#)
[![HMAC-SHA256](https://img.shields.io/badge/HMAC--SHA256-14B8A6?style=for-the-badge&logo=letsencrypt&logoColor=white)](#)
[![License MIT](https://img.shields.io/badge/License-MIT-34D399?style=for-the-badge)](LICENSE)

<br/>

> **সুরক্ষা (Shurokkha)** — বাংলায় "সুরক্ষা" মানে *Protection* & *Security*.  
> An end-to-end, production-grade FinTech engine with Sentinel AI Fraud Radar — inspired by Stripe, Razorpay & Juspay Hyperswitch.

<br/>

**Built by [Rakib](https://github.com/rakibdipu)** &nbsp;·&nbsp; ⭐ Star if you find it useful!

<br/>

</div>

---

## 🛡 What is Shurokkha?

**Shurokkha** is a complete, self-contained **FinTech Payment Gateway** with 10 production-grade modules built entirely from scratch. The name comes from the Bengali word for *security & protection* — reflecting its core mission: securing every transaction with military-grade encryption, real-time AI fraud detection, and mathematically-verified financial integrity.

This was built as a deep technical study into how real payment systems like **Stripe**, **Razorpay**, and **Juspay** work under the hood — from AES-256 card tokenization to gradient-boosting ML fraud models, double-entry bookkeeping, marketplace split payments, and HMAC-signed webhooks with exponential backoff retries.

---

## 🎨 Design Philosophy

> Clean · Minimal · Enterprise-Grade · Light Mode SaaS

The entire dashboard follows a **Mint Green + Sky Blue + Ice White** color palette:

| Token | Hex | Usage |
|---|---|---|
| **Mint Primary** | `#10B981` | CTAs, success states, brand accent |
| **Sky Cyan** | `#06B6D4` | AI indicators, links, tech highlights |
| **Ice White** | `#F0FDF9` | Page background, section separators |
| **Slate Text** | `#134E4A` | Body text — readable without being harsh |
| **Soft Card Border** | `#D1FAE5` | Card borders — float effect on white |

No dark gradients. No heavy corporate navy. Just clean, glassy, FinTech-startup premium.

---

## 📸 UI Showcase

### 💳 Checkout Simulator — Card, UPI QR & 3DS OTP
> AES-256-GCM tokenized card vault. Sentinel AI scores every transaction (0–100) before capture.

![Checkout Simulator](docs/assets/01_checkout_simulator.png)

<br/>

### ⚡ Smart Multi-Acquirer Router & Auto-Cascade Engine
> Routes dynamically across HDFC, ICICI, Stripe, and Chase. Auto-cascades on outage — zero customer drop.

![Smart Routing Switch](docs/assets/02_smart_routing_switch.png)

<br/>

### 🛡 Sentinel AI Fraud Radar — 7 Rules + ML Classifier
> 7 heuristic velocity rules blended with a trained `GradientBoostingClassifier`.  
> Scores 0–100 → **ALLOW** (<30) / **CHALLENGE** (30–69, 3DS OTP) / **BLOCK** (≥70)

![Sentinel Fraud Radar](docs/assets/03_sentinel_fraud_radar.png)

<br/>

### 🌍 Global Geo-Fraud Heatmap & Real-Time Telemetry
> Canvas-rendered world ping radar — Tor/Proxy anomalies, impossible travel speed detection.

![Geo Heatmap](docs/assets/04_geo_heatmap.png)

<br/>

### 🏪 Marketplace Split Payments & Instant Vendor Payouts
> Stripe Connect-style multi-vendor split engine with per-vendor commission deduction and instant settlement.

![Marketplace Splits](docs/assets/05_marketplace_splits.png)

<br/>

### 🔄 Recurring Subscriptions & UPI AutoPay Engine
> Monthly/annual e-Mandate registration, automated billing cycles, dunning retry logic.

![Subscriptions AutoPay](docs/assets/06_subscriptions_autopay.png)

<br/>

### 📒 Strict Double-Entry Bookkeeping Ledger
> Every paisa tracked across 4 immutable T-accounts.  
> Mathematically guaranteed: **Σ Debits = Σ Credits** on every single transaction.

![Double Entry Ledger](docs/assets/07_double_entry_ledger.png)

<br/>

### 🔔 Transactional Outbox Webhook Dispatcher
> HMAC-SHA256 signed payloads, timestamp anti-replay defense, exponential backoff (5s → 30s → 2m → 10m), DLQ + manual replay.

![Webhook Dispatcher](docs/assets/08_webhook_dispatcher.png)

<br/>

### 🔍 Automated End-of-Day Bank Reconciliation
> Ingests bank settlement CSVs and classifies: `MATCHED` / `AMOUNT_MISMATCH` / `MISSING_IN_BANK` / `EXTRA_IN_BANK`

![Bank Reconciliation](docs/assets/09_bank_reconciliation.png)

<br/>

### 📖 Interactive OpenAPI / Swagger Documentation
> 25+ production REST endpoints fully documented across 10 API controllers.

![Swagger API Docs](docs/assets/10_swagger_api_docs.png)

---

## 🏛 System Architecture

```
  ┌────────────────────────────────────────────────────────────────┐
  │                  Merchant / Checkout Client                    │
  └──────────────────────────┬─────────────────────────────────────┘
                             │
               ┌─────────────▼──────────────┐
               │   Idempotency Guard (UUID)  │
               │   + AES-256-GCM Card Vault  │
               └─────────────┬──────────────┘
                             │
               ┌─────────────▼──────────────┐
               │    Sentinel AI Fraud Radar  │
               │  ┌──────────┬────────────┐  │
               │  │ 7 Rules  │  GBM Model │  │
               │  └──────────┴────────────┘  │
               │   60% Rules + 40% ML        │
               └────┬──────┬────────┬────────┘
                    │      │        │
               ALLOW   CHALLENGE  BLOCK
                    │      │        └── Rejected + Ledger FRAUD_HOLD
                    │   3DS OTP
                    │      │
               ┌────▼──────▼────────────────┐
               │  Smart Multi-Acquirer Router│
               │  HDFC → ICICI → Stripe      │
               │  (Auto-Cascade on Outage)   │
               └────────────┬───────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
  ┌───────▼──────────────┐    ┌───────────────▼────────────┐
  │  Double-Entry Ledger  │    │  Webhook Outbox + DLQ      │
  │  (ACID: Σ Dr = Σ Cr)  │    │  (HMAC-SHA256 Signed)      │
  └──────────────────────┘    └────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API** | FastAPI + Uvicorn | Async, type-safe, 40k+ req/s |
| **Database** | SQLAlchemy 2.0 + SQLite (WAL) | ACID transactions, zero dependency |
| **ML Engine** | Scikit-Learn `GradientBoostingClassifier` | Trained on 2,000 synthetic fraud vectors |
| **Cryptography** | `cryptography` (AESGCM) + `hmac` | PCI-DSS AES-256-GCM + HMAC-SHA256 |
| **Frontend** | Vanilla JS + Tailwind + Chart.js + QRCode.js | Clean SaaS light-mode dashboard, zero build tools |

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/rakibdipu/razorflow-gateway.git
cd razorflow-gateway

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Linux/macOS
.\venv\Scripts\Activate.ps1     # Windows PowerShell

pip install -r backend/requirements.txt

# 3. Start the server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open in browser:
- 🖥 **Shurokkha Dashboard** → http://127.0.0.1:8000/
- 📖 **Swagger API Docs** → http://127.0.0.1:8000/docs

---

## 🧪 Test Presets

| Scenario | Card Number | CVV | Result |
|---|---|---|---|
| ✅ **Instant Capture** | `4111 1111 1111 1111` | `123` | Risk score < 30 → ALLOW |
| ⚠️ **3DS Challenge** | `4000 0000 0000 0002` | `111` | Risk 30–69 → OTP step-up |
| 🚫 **AI Fraud Block** | `4000 0000 0000 0069` | `000` | Risk ≥ 70 → BLOCK + FRAUD_HOLD |

---

## 🔒 Security Highlights

| Feature | Implementation |
|---|---|
| **Card Tokenization** | AES-256-GCM with per-entry 12-byte nonce — PAN never stored in plaintext |
| **Webhook Integrity** | HMAC-SHA256 signature + 300-second timestamp replay window |
| **Double-Entry Integrity** | Every transaction algebraically verified: `Σ Dr = Σ Cr` |
| **Fraud Escrow** | Disputed funds auto-locked in `FRAUD_HOLD` T-account |
| **Idempotency** | UUID-keyed request deduplication — safe for mobile retries |

---

## 📁 Project Structure

```
razorflow-gateway/
├── docs/assets/              # UI screenshots embedded in this README
├── backend/
│   ├── app/
│   │   ├── api/v1/           # 10 REST API controllers
│   │   ├── core/             # AES-256 vault, HMAC signer, config
│   │   ├── ml/               # Fraud model training & real-time inference
│   │   ├── models/           # SQLAlchemy tables + Pydantic DTOs
│   │   ├── services/         # Business logic engines
│   │   └── main.py           # App lifespan & router registration
│   └── requirements.txt
├── frontend/
│   └── index.html            # Complete SaaS dashboard (single file SPA)
└── README.md
```

---

<div align="center">

<br/>

**Crafted with 💚 by [Rakib](https://github.com/rakibdipu)**

*সুরক্ষা — Protection through technology.*

<br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,19,20&height=120&section=footer" width="100%"/>

</div>
