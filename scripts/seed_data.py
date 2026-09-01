"""
Shurokkha Seed Data Script
Run from: r:/company-wise-projects-main/razorflow-gateway/backend/
Command:   python ../scripts/seed_data.py
"""
import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import uuid
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, create_all_tables
from app.models.models import Merchant, Order, Transaction, LedgerEntry, WebhookEvent, PaymentToken
from app.core.security import CardVault
from app.services.ledger_service import LedgerService

def seed():
    create_all_tables()
    db = SessionLocal()
    
    # Check if already seeded
    if db.query(Merchant).count() > 0:
        print('[Seed] Database already seeded. Skipping.')
        db.close()
        return
    
    print('[Seed] Seeding merchants...')
    
    merchants = [
        Merchant(
            id=str(uuid.uuid4()),
            name='TechShop India',
            email='payments@techshop.in',
            api_key='rflow_live_techshop_key_001',
            webhook_url='http://127.0.0.1:8000/api/v1/webhooks/test-receiver',
            webhook_secret='techshop_webhook_secret_001',
            is_active=True,
            created_at=datetime.utcnow()
        ),
        Merchant(
            id=str(uuid.uuid4()),
            name='FoodExpress',
            email='billing@foodexpress.com',
            api_key='rflow_live_foodexpress_key_002',
            webhook_url='http://127.0.0.1:8000/api/v1/webhooks/test-receiver',
            webhook_secret='foodexpress_webhook_secret_002',
            is_active=True,
            created_at=datetime.utcnow()
        ),
        Merchant(
            id=str(uuid.uuid4()),
            name='TravelDeals',
            email='finance@traveldeals.io',
            api_key='rflow_live_traveldeals_key_003',
            webhook_url='http://127.0.0.1:8000/api/v1/webhooks/test-receiver',
            webhook_secret='traveldeals_webhook_secret_003',
            is_active=True,
            created_at=datetime.utcnow()
        )
    ]
    db.add_all(merchants)
    db.commit()
    print(f'[Seed] Created {len(merchants)} merchants.')
    
    # Seed 200 historical transactions
    print('[Seed] Seeding transactions...')
    
    test_cards = [
        {'number': '4111111111111111', 'expiry': '12/2027'},
        {'number': '4000000000000002', 'expiry': '06/2026'},
        {'number': '5200828282828210', 'expiry': '03/2028'},
        {'number': '4012888888881881', 'expiry': '08/2027'},
    ]
    
    statuses = ['CAPTURED'] * 75 + ['BLOCKED'] * 15 + ['REFUNDED'] * 10  # 75/15/10 split
    random.shuffle(statuses)
    
    for i, status in enumerate(statuses):
        merchant = random.choice(merchants)
        amount = random.choice([49900, 99900, 199900, 499900, 999900, 149900, 29900])
        days_ago = random.randint(0, 30)
        created = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0,23))
        card = random.choice(test_cards)
        
        order = Order(
            id=str(uuid.uuid4()),
            merchant_id=merchant.id,
            amount_paise=amount,
            currency='INR',
            status=status,
            customer_email=f'customer{i+1}@example.com',
            idempotency_key=str(uuid.uuid4()),
            created_at=created,
            updated_at=created
        )
        db.add(order)
        db.flush()
        
        token = PaymentToken(
            id=str(uuid.uuid4()),
            order_id=order.id,
            encrypted_pan=CardVault.encrypt_pan(card['number']),
            card_brand=CardVault.get_card_brand(card['number']),
            last4=card['number'][-4:],
            bin6=card['number'][:6],
            expiry_masked=card['expiry'],
            created_at=created
        )
        db.add(token)
        
        if status == 'BLOCKED':
            risk_score = random.randint(70, 95)
            risk_tier = 'BLOCK'
        elif status == 'REFUNDED':
            risk_score = random.randint(0, 29)
            risk_tier = 'ALLOW'
        else:
            risk_score = random.randint(0, 45)
            risk_tier = random.choice(['ALLOW', 'CHALLENGE'])
        
        txn = Transaction(
            id=str(uuid.uuid4()),
            order_id=order.id,
            status=status,
            risk_score=risk_score,
            risk_tier=risk_tier,
            risk_details_json=json.dumps({'tier': risk_tier, 'score': risk_score}),
            bank_ref=f'BNK-{str(uuid.uuid4())[:8].upper()}' if status in ('CAPTURED', 'REFUNDED') else None,
            captured_at=created + timedelta(seconds=random.randint(2, 10)) if status in ('CAPTURED', 'REFUNDED') else None,
            refunded_at=created + timedelta(minutes=random.randint(10, 1440)) if status == 'REFUNDED' else None,
            created_at=created,
            updated_at=created
        )
        db.add(txn)
        db.flush()
        
        # Add ledger entries for CAPTURED/REFUNDED transactions
        if status in ('CAPTURED', 'REFUNDED'):
            LedgerService.post_capture(txn.id, amount, db)
            if status == 'REFUNDED':
                LedgerService.post_refund(txn.id, amount, db)
    
    db.commit()
    print(f'[Seed] Created {len(statuses)} transactions with ledger entries.')
    
    # Seed webhook events
    print('[Seed] Seeding webhook events...')
    m0 = merchants[0]
    webhook_events = [
        WebhookEvent(
            id=str(uuid.uuid4()),
            merchant_id=m0.id,
            event_type='payment.captured',
            payload_json=json.dumps({'event': 'payment.captured', 'amount_paise': 49900}),
            status='SENT',
            attempts=1,
            response_code=200,
            created_at=datetime.utcnow() - timedelta(hours=2)
        ),
        WebhookEvent(
            id=str(uuid.uuid4()),
            merchant_id=m0.id,
            event_type='payment.captured',
            payload_json=json.dumps({'event': 'payment.captured', 'amount_paise': 99900}),
            status='FAILED',
            attempts=2,
            response_code=503,
            next_retry_at=datetime.utcnow() + timedelta(minutes=2),
            created_at=datetime.utcnow() - timedelta(hours=1)
        ),
        WebhookEvent(
            id=str(uuid.uuid4()),
            merchant_id=m0.id,
            event_type='fraud.blocked',
            payload_json=json.dumps({'event': 'fraud.blocked', 'risk_score': 85}),
            status='DLQ',
            attempts=4,
            response_code=500,
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
    ]
    db.add_all(webhook_events)
    db.commit()
    print('[Seed] Created 3 webhook events (SENT, FAILED, DLQ).')
    
    first_api_key = merchants[0].api_key  # capture before session close
    db.close()
    print('[Seed] ✅ Database seeded successfully!')
    print(f'[Seed] Merchants: {len(merchants)}')
    print(f'[Seed] First merchant API key: {first_api_key}')

if __name__ == '__main__':
    seed()
