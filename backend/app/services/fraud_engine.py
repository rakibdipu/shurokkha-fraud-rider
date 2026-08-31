import json
import random
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field, asdict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Transaction, Order, PaymentToken


@dataclass
class FraudRule:
    name: str
    triggered: bool
    score_contribution: int  # 0-100
    reason: str


@dataclass 
class RiskAssessment:
    transaction_id: str
    total_score: int          # 0-100
    tier: str                 # ALLOW / CHALLENGE / BLOCK
    triggered_rules: list     # list of FraudRule dicts
    ml_score: int
    ml_top_features: list
    decision_reason: str
    rule_score: int           # raw rule-only score before ML blend


class SentinelFraudEngine:
    """
    Multi-tier real-time fraud scoring engine.
    
    Tier 1: Heuristic rule engine (velocity, anomalies, geo)
    Tier 2: ML model risk score  
    Tier 3: Dynamic decision matrix (ALLOW / CHALLENGE / BLOCK)
    """

    # ── TIER 1: HEURISTIC RULES ───────────────────────────────────────────────

    @staticmethod
    def _rule_velocity_1min(
        ip_address: str, 
        db: Session
    ) -> FraudRule:
        """
        Trigger if more than FRAUD_VELOCITY_MAX_PER_MINUTE transactions
        from the same IP in the last 60 seconds.
        Uses Transaction table - check transactions created in last 60s
        that share same IP via risk_details_json.
        Since we store ip in risk_details_json, we count recent transactions
        within 1 min window.
        Simplified: count all transactions created in last 60s (proxy for IP velocity).
        """
        cutoff = datetime.utcnow() - timedelta(seconds=60)
        count = db.query(Transaction).filter(
            Transaction.created_at >= cutoff,
            Transaction.risk_details_json.like(f'%{ip_address}%')
        ).count()
        
        triggered = count >= settings.FRAUD_VELOCITY_MAX_PER_MINUTE
        return FraudRule(
            name='velocity_1min',
            triggered=triggered,
            score_contribution=40 if triggered else 0,
            reason=f'{count} transactions from IP {ip_address} in last 60s (limit: {settings.FRAUD_VELOCITY_MAX_PER_MINUTE})'
        )

    @staticmethod
    def _rule_velocity_1hr(
        bin6: str,
        db: Session
    ) -> FraudRule:
        """
        Trigger if more than FRAUD_VELOCITY_MAX_PER_HOUR transactions
        from the same card BIN in the last hour.
        """
        cutoff = datetime.utcnow() - timedelta(hours=1)
        # Count PaymentTokens with this BIN in last 1 hour
        from app.models.models import PaymentToken
        count = db.query(PaymentToken).filter(
            PaymentToken.bin6 == bin6,
            PaymentToken.created_at >= cutoff
        ).count()
        
        triggered = count >= settings.FRAUD_VELOCITY_MAX_PER_HOUR
        return FraudRule(
            name='velocity_1hr',
            triggered=triggered,
            score_contribution=25 if triggered else 0,
            reason=f'{count} transactions with BIN {bin6} in last 1hr (limit: {settings.FRAUD_VELOCITY_MAX_PER_HOUR})'
        )

    @staticmethod
    def _rule_amount_spike(
        order: Order,
        db: Session
    ) -> FraudRule:
        """
        Trigger if current amount is > FRAUD_AMOUNT_SPIKE_MULTIPLIER * user's 30-day average.
        Uses orders for same merchant as proxy for user history.
        """
        cutoff = datetime.utcnow() - timedelta(days=30)
        past_orders = db.query(Order).filter(
            Order.merchant_id == order.merchant_id,
            Order.customer_email == order.customer_email,
            Order.created_at >= cutoff,
            Order.status == 'CAPTURED'
        ).all()
        
        if len(past_orders) < 3:
            # Not enough history — low confidence, skip
            return FraudRule(
                name='amount_spike',
                triggered=False,
                score_contribution=0,
                reason='Insufficient transaction history for spike detection'
            )
        
        avg_amount = sum(o.amount_paise for o in past_orders) / len(past_orders)
        multiplier = order.amount_paise / avg_amount if avg_amount > 0 else 0
        triggered = multiplier > settings.FRAUD_AMOUNT_SPIKE_MULTIPLIER
        return FraudRule(
            name='amount_spike',
            triggered=triggered,
            score_contribution=30 if triggered else 0,
            reason=f'Amount {order.amount_paise} paise is {multiplier:.1f}x the 30-day avg {int(avg_amount)} paise'
        )

    @staticmethod
    def _rule_high_risk_bin(bin6: str) -> FraudRule:
        """
        Check if card BIN is in known high-risk list.
        High-risk BINs (simulated): prepaid cards, known fraud BINs.
        """
        HIGH_RISK_BINS = {
            '400000', '411111',  # Test BINs (note: 411111 is ALLOW test card but we flag BIN separately)
            '426684', '485953', '402361', '404371',  # Sample high-risk prepaid BINs
            '520082', '527571', '529105'
        }
        # NOTE: 411111 is the test ALLOW card - we don't flag it as high-risk for test purposes
        test_allow_bins = {'411111'}
        triggered = bin6 in HIGH_RISK_BINS and bin6 not in test_allow_bins
        return FraudRule(
            name='high_risk_bin',
            triggered=triggered,
            score_contribution=35 if triggered else 0,
            reason=f'BIN {bin6} {"is" if triggered else "is not"} in high-risk BIN registry'
        )

    @staticmethod
    def _rule_proxy_ip(ip_address: str) -> FraudRule:
        """
        Detect known proxy/VPN IPs.
        Simulated: IPs in 10.255.x.x or 192.168.254.x ranges trigger this.
        """
        triggered = (
            ip_address.startswith('10.255.') or
            ip_address.startswith('192.168.254.') or
            ip_address in {'1.1.1.1', '8.8.8.8', '9.9.9.9'}  # Public DNS = likely proxy
        )
        return FraudRule(
            name='proxy_ip',
            triggered=triggered,
            score_contribution=20 if triggered else 0,
            reason=f'IP {ip_address} {"matches" if triggered else "does not match"} known proxy/VPN patterns'
        )

    @staticmethod
    def _rule_odd_hour() -> FraudRule:
        """
        Flag transactions between 2:00am - 4:00am UTC (historically higher fraud rate).
        """
        hour = datetime.utcnow().hour
        triggered = hour in (2, 3)  # 2am-3:59am UTC
        return FraudRule(
            name='odd_hour',
            triggered=triggered,
            score_contribution=10 if triggered else 0,
            reason=f'Transaction at UTC hour {hour} ({"high-risk" if triggered else "normal"} window)'
        )

    @staticmethod
    def _rule_impossible_travel(
        bin6: str,
        db: Session
    ) -> FraudRule:
        """
        Check if same BIN was used in another country within FRAUD_IMPOSSIBLE_TRAVEL_MINUTES.
        Simplified: if same BIN had a transaction AND current amount is very different, flag.
        Full geo implementation would require IP geolocation API.
        Here we simulate: if >2 transactions from same BIN in travel window, flag.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=settings.FRAUD_IMPOSSIBLE_TRAVEL_MINUTES)
        from app.models.models import PaymentToken
        recent = db.query(PaymentToken).filter(
            PaymentToken.bin6 == bin6,
            PaymentToken.created_at >= cutoff
        ).count()
        # Simplified: 3+ uses of same BIN in travel window = suspicious multi-location
        triggered = recent >= 3
        return FraudRule(
            name='impossible_travel',
            triggered=triggered,
            score_contribution=50 if triggered else 0,
            reason=f'BIN {bin6} used {recent} times in last {settings.FRAUD_IMPOSSIBLE_TRAVEL_MINUTES}min'
        )

    # ── TIER 2: ML RISK SCORE ─────────────────────────────────────────────────

    @staticmethod
    def _ml_score(
        rules: list,
        token: PaymentToken,
        order: Order,
        ip_address: str,
        db: Session
    ) -> dict:
        """
        Build feature vector and call ML model.
        Returns {ml_score: int, top_features: list[str]}
        """
        try:
            from app.ml.train_model import predict_risk
            
            # Extract velocity from rules
            velocity_1min = 0
            velocity_1hr = 0
            for rule in rules:
                if rule.name == 'velocity_1min' and rule.triggered:
                    velocity_1min = settings.FRAUD_VELOCITY_MAX_PER_MINUTE + 1
                if rule.name == 'velocity_1hr' and rule.triggered:
                    velocity_1hr = settings.FRAUD_VELOCITY_MAX_PER_HOUR + 1

            # Amount deviation — rough estimate
            amount_deviation = 1.0
            for rule in rules:
                if rule.name == 'amount_spike':
                    # Parse from reason string
                    import re
                    match = re.search(r'is ([\d.]+)x', rule.reason)
                    if match:
                        amount_deviation = float(match.group(1))

            features = {
                'velocity_1min': velocity_1min,
                'velocity_1hr': velocity_1hr,
                'amount_deviation': min(amount_deviation, 10.0),
                'hour_of_day': datetime.utcnow().hour,
                'is_foreign_card': 1 if (token.bin6 or '').startswith('4000') else 0,
                'is_high_risk_bin': 1 if any(r.name == 'high_risk_bin' and r.triggered for r in rules) else 0,
                'ip_proxy_flag': 1 if any(r.name == 'proxy_ip' and r.triggered for r in rules) else 0,
                'distance_km_from_last': 12000 if any(r.name == 'impossible_travel' and r.triggered for r in rules) else 50,
                'days_since_account_open': 5 if velocity_1min > 0 else 365
            }

            result = predict_risk(features)
            return {
                'ml_score': result['risk_score'],
                'top_features': result['top_features']
            }
        except Exception as e:
            # ML model unavailable — fallback to rule-only scoring
            return {'ml_score': 0, 'top_features': ['model_unavailable']}

    # ── TIER 3: DECISION MATRIX ───────────────────────────────────────────────

    @staticmethod
    def _make_decision(combined_score: int, triggered_rules: list) -> tuple:
        """
        Convert combined risk score to ALLOW / CHALLENGE / BLOCK tier.
        Returns (tier: str, reason: str)
        """
        if combined_score < settings.FRAUD_ALLOW_THRESHOLD:
            return 'ALLOW', f'Risk score {combined_score} below ALLOW threshold {settings.FRAUD_ALLOW_THRESHOLD}'
        elif combined_score < settings.FRAUD_BLOCK_THRESHOLD:
            return 'CHALLENGE', f'Risk score {combined_score} requires 3DS step-up authentication'
        else:
            top_rule = max(triggered_rules, key=lambda r: r.score_contribution, default=None)
            reason = f'Risk score {combined_score} exceeds BLOCK threshold {settings.FRAUD_BLOCK_THRESHOLD}'
            if top_rule:
                reason += f'. Primary trigger: {top_rule.name} ({top_rule.reason})'
            return 'BLOCK', reason

    # ── PUBLIC ASSESS METHOD ──────────────────────────────────────────────────

    @staticmethod
    def assess(
        transaction_id: str,
        card_token: PaymentToken,
        ip_address: str,
        order: Order,
        db: Session
    ) -> dict:
        """
        Full fraud assessment pipeline.
        Returns a dict matching RiskAssessment fields.
        """
        bin6 = card_token.bin6 or '000000'

        # TEST CARD OVERRIDES (deterministic for demo/testing)
        if card_token.last4 == '1111' and bin6 == '411111':
            return asdict(RiskAssessment(
                transaction_id=transaction_id,
                total_score=5,
                tier='ALLOW',
                triggered_rules=[],
                ml_score=5,
                ml_top_features=['velocity_1min'],
                decision_reason='Test card: always ALLOW',
                rule_score=0
            ))
        if card_token.last4 == '0002' and bin6 == '400000':
            return asdict(RiskAssessment(
                transaction_id=transaction_id,
                total_score=50,
                tier='CHALLENGE',
                triggered_rules=[asdict(FraudRule('test_card', True, 50, 'Test card: always CHALLENGE'))],
                ml_score=50,
                ml_top_features=['is_foreign_card'],
                decision_reason='Test card: always CHALLENGE (3DS required)',
                rule_score=50
            ))
        if card_token.last4 == '0069' and bin6 == '400000':
            return asdict(RiskAssessment(
                transaction_id=transaction_id,
                total_score=90,
                tier='BLOCK',
                triggered_rules=[asdict(FraudRule('test_card', True, 90, 'Test card: always BLOCK'))],
                ml_score=90,
                ml_top_features=['ip_proxy_flag', 'velocity_1min'],
                decision_reason='Test card: always BLOCK (known fraud card)',
                rule_score=90
            ))

        # TIER 1: Run all heuristic rules
        rules = [
            SentinelFraudEngine._rule_velocity_1min(ip_address, db),
            SentinelFraudEngine._rule_velocity_1hr(bin6, db),
            SentinelFraudEngine._rule_amount_spike(order, db),
            SentinelFraudEngine._rule_high_risk_bin(bin6),
            SentinelFraudEngine._rule_proxy_ip(ip_address),
            SentinelFraudEngine._rule_odd_hour(),
            SentinelFraudEngine._rule_impossible_travel(bin6, db),
        ]

        triggered_rules = [r for r in rules if r.triggered]
        rule_score = min(sum(r.score_contribution for r in triggered_rules), 100)

        # TIER 2: ML score
        ml_result = SentinelFraudEngine._ml_score(rules, card_token, order, ip_address, db)
        ml_score = ml_result['ml_score']

        # Blend: 60% rules + 40% ML
        combined_score = int(0.6 * rule_score + 0.4 * ml_score)
        combined_score = max(0, min(100, combined_score))

        # TIER 3: Decision
        tier, decision_reason = SentinelFraudEngine._make_decision(combined_score, triggered_rules)

        return asdict(RiskAssessment(
            transaction_id=transaction_id,
            total_score=combined_score,
            tier=tier,
            triggered_rules=[asdict(r) for r in triggered_rules],
            ml_score=ml_score,
            ml_top_features=ml_result['top_features'],
            decision_reason=decision_reason,
            rule_score=rule_score
        ))

    @staticmethod
    def get_rules_config() -> list:
        """Return current rule configuration for API exposure."""
        return [
            {'name': 'velocity_1min', 'threshold': settings.FRAUD_VELOCITY_MAX_PER_MINUTE, 'score': 40, 'description': 'Max transactions per minute from same IP'},
            {'name': 'velocity_1hr', 'threshold': settings.FRAUD_VELOCITY_MAX_PER_HOUR, 'score': 25, 'description': 'Max transactions per hour from same card BIN'},
            {'name': 'amount_spike', 'threshold': settings.FRAUD_AMOUNT_SPIKE_MULTIPLIER, 'score': 30, 'description': 'Amount spike multiplier vs 30-day average'},
            {'name': 'impossible_travel', 'threshold': settings.FRAUD_IMPOSSIBLE_TRAVEL_MINUTES, 'score': 50, 'description': 'Impossible travel window in minutes'},
            {'name': 'high_risk_bin', 'threshold': None, 'score': 35, 'description': 'Card BIN in high-risk registry'},
            {'name': 'proxy_ip', 'threshold': None, 'score': 20, 'description': 'IP matches known proxy/VPN patterns'},
            {'name': 'odd_hour', 'threshold': None, 'score': 10, 'description': 'Transaction in high-risk hour window (2am-4am UTC)'},
        ]
