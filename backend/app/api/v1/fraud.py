from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.models.models import Transaction
from app.models.schemas import FraudRuleUpdateRequest
from app.services.fraud_engine import SentinelFraudEngine
from app.core.config import settings

router = APIRouter(prefix='/fraud', tags=['Fraud Detection'])

@router.get('/assessment/{transaction_id}')
def get_risk_assessment(transaction_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the full Sentinel fraud risk assessment for a transaction.
    Includes triggered rules, ML score, and decision reason.
    """
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail=f'Transaction {transaction_id} not found')
    
    if not txn.risk_details_json:
        raise HTTPException(status_code=404, detail='No risk assessment found for this transaction')
    
    risk_data = json.loads(txn.risk_details_json)
    return {
        'transaction_id': transaction_id,
        'risk_score': txn.risk_score,
        'risk_tier': txn.risk_tier,
        'assessment': risk_data
    }

@router.get('/rules')
def get_fraud_rules():
    """
    List all active heuristic fraud rules with current thresholds and scores.
    """
    return {
        'rules': SentinelFraudEngine.get_rules_config(),
        'thresholds': {
            'allow_below': settings.FRAUD_ALLOW_THRESHOLD,
            'block_above': settings.FRAUD_BLOCK_THRESHOLD,
            'challenge_range': f'{settings.FRAUD_ALLOW_THRESHOLD}-{settings.FRAUD_BLOCK_THRESHOLD}'
        },
        'ml_blend': '60% rules + 40% ML model'
    }

@router.get('/stats')
def get_fraud_stats(db: Session = Depends(get_db)):
    """
    Aggregated fraud detection statistics.
    """
    transactions = db.query(Transaction).all()
    total = len(transactions)
    if total == 0:
        return {'total': 0, 'allow': 0, 'challenge': 0, 'block': 0, 'blocked_rate': '0%'}
    
    allow_count = sum(1 for t in transactions if t.risk_tier == 'ALLOW')
    challenge_count = sum(1 for t in transactions if t.risk_tier == 'CHALLENGE')
    block_count = sum(1 for t in transactions if t.risk_tier == 'BLOCK')
    avg_score = sum((t.risk_score or 0) for t in transactions) / total
    
    return {
        'total_transactions': total,
        'allow': allow_count,
        'challenge': challenge_count,
        'block': block_count,
        'blocked_rate': f'{block_count/total*100:.1f}%',
        'avg_risk_score': round(avg_score, 1)
    }
