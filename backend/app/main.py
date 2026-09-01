import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.database import create_all_tables, SessionLocal
from app.api.v1 import (
    orders,
    payments,
    fraud,
    webhooks,
    ledger,
    reconciliation,
    router_api,
    marketplace,
    subscriptions,
    disputes
)
from app.services.smart_router import SmartRoutingEngine
from app.services.split_engine import MarketplaceSplitEngine
from app.services.subscription_engine import SubscriptionEngine


def ensure_ml_model():
    """Train ML model if not already trained."""
    model_path = os.path.join(os.path.dirname(__file__), "ml", "fraud_model.pkl")
    if not os.path.exists(model_path):
        print("[Shurokkha] ML model not found. Training now...")
        from app.ml.train_model import train_and_save
        train_and_save()


def webhook_background_worker():
    """Background thread that dispatches pending webhooks every 10 seconds."""
    from app.services.webhook_dispatcher import WebhookDispatcher
    while True:
        try:
            db = SessionLocal()
            result = WebhookDispatcher.dispatch_pending(db)
            db.close()
        except Exception:
            pass
        time.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[Shurokkha] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    create_all_tables()
    ensure_ml_model()
    
    # Initialize default engines
    try:
        db = SessionLocal()
        SmartRoutingEngine.initialize_gateways(db)
        MarketplaceSplitEngine.seed_default_vendors(db)
        SubscriptionEngine.seed_default_plans(db)
        db.close()
    except Exception as e:
        print("[Shurokkha Setup Error]", e)

    # Start background worker
    worker = threading.Thread(target=webhook_background_worker, daemon=True)
    worker.start()

    yield
    print("[Shurokkha] Shutting down.")


app = FastAPI(
    title="Shurokkha Fraud Rider — Payment Gateway",
    description="Real-Time Payment Gateway & Sentinel AI Fraud Radar",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Shurokkha-Version"] = settings.APP_VERSION
    return response

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount API v1 Routers
app.include_router(orders.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(fraud.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(ledger.router, prefix="/api/v1")
app.include_router(reconciliation.router, prefix="/api/v1")
app.include_router(router_api.router, prefix="/api/v1")
app.include_router(marketplace.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(disputes.router, prefix="/api/v1")

frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html")

@app.get("/")
def serve_dashboard():
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return JSONResponse({"message": "Shurokkha API running. See /docs for API reference."})

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
