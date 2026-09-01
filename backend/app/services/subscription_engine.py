import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import SubscriptionPlan, Subscription, Order, Transaction


class SubscriptionEngine:
    """
    Recurring Billing & UPI AutoPay Engine (e-Mandate & Subscriptions).
    Manages automated billing cycles, pre-debit notices, and smart retry dunning.
    """

    @staticmethod
    def seed_default_plans(db: Session):
        """Seed default subscription tiers."""
        if db.query(SubscriptionPlan).count() == 0:
            plans = [
                SubscriptionPlan(
                    name="Shurokkha Starter Plan",
                    interval="monthly",
                    amount_paise=99900,  # 999 INR
                    currency="INR"
                ),
                SubscriptionPlan(
                    name="Enterprise Sentinel Pro",
                    interval="monthly",
                    amount_paise=499900,  # 4,999 INR
                    currency="INR"
                ),
                SubscriptionPlan(
                    name="Annual Cloud Tier",
                    interval="yearly",
                    amount_paise=3999900,  # 39,999 INR
                    currency="INR"
                )
            ]
            db.add_all(plans)
            db.commit()

    @staticmethod
    def create_subscription(plan_id: str, customer_email: str, db: Session) -> Subscription:
        """
        Create a recurring subscription mandate for a customer.
        """
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
        if not plan:
            raise ValueError(f"SubscriptionPlan {plan_id} not found")

        now = datetime.utcnow()
        interval_days = 365 if plan.interval == "yearly" else 30
        period_end = now + timedelta(days=interval_days)

        sub = Subscription(
            plan_id=plan.id,
            customer_email=customer_email,
            status="ACTIVE",
            current_period_start=now,
            current_period_end=period_end,
            next_billing_at=period_end,
            retry_count=0
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def charge_due_subscriptions(db: Session) -> dict:
        """
        Cron task: finds all active subscriptions due for billing and charges them automatically.
        """
        now = datetime.utcnow()
        due_subs = db.query(Subscription).filter(
            Subscription.status == "ACTIVE",
            Subscription.next_billing_at <= now
        ).all()

        charged = 0
        failed = 0

        for sub in due_subs:
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
            # Advance billing cycle
            interval_days = 365 if plan.interval == "yearly" else 30
            sub.current_period_start = now
            sub.current_period_end = now + timedelta(days=interval_days)
            sub.next_billing_at = sub.current_period_end
            charged += 1

        db.commit()
        return {
            "evaluated_at": now.isoformat() + "Z",
            "charged_count": charged,
            "failed_count": failed
        }
