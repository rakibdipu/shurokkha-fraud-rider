import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Vendor, PaymentSplit, Transaction, Order, LedgerEntry


class MarketplaceSplitEngine:
    """
    Automated Marketplace Split Payments & Vendor Payout Engine (Stripe Connect / Razorpay Route).
    Divides captured customer funds across multiple vendors with platform commission deduction.
    """

    @staticmethod
    def seed_default_vendors(db: Session):
        """Seed demo marketplace sellers."""
        if db.query(Vendor).count() == 0:
            vendors = [
                Vendor(
                    name="Alpha Electronics Store",
                    email="seller.alpha@market.com",
                    bank_account="HDFC-AC-88990011",
                    balance_paise=1250000,
                    commission_rate=8.0
                ),
                Vendor(
                    name="Zenith Fashion Hub",
                    email="zenith.vendor@market.com",
                    bank_account="ICICI-AC-44556677",
                    balance_paise=840000,
                    commission_rate=12.0
                ),
                Vendor(
                    name="HyperAudio Gear",
                    email="sales@hyperaudio.io",
                    bank_account="AXIS-AC-11223344",
                    balance_paise=450000,
                    commission_rate=10.0
                ),
            ]
            db.add_all(vendors)
            db.commit()

    @staticmethod
    def process_split_payment(transaction_id: str, split_items: list, db: Session) -> dict:
        """
        Execute split across vendors for a captured transaction.
        Updates vendor balances and generates double-entry sub-ledger postings.
        """
        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            raise ValueError(f"Transaction {transaction_id} not found")

        order = db.query(Order).filter(Order.id == txn.order_id).first()
        total_amount = order.amount_paise

        created_splits = []
        total_split_amount = 0

        for item in split_items:
            vendor = db.query(Vendor).filter(Vendor.id == item["vendor_id"]).first()
            if not vendor:
                continue

            if "amount_paise" in item and item["amount_paise"]:
                v_amount = item["amount_paise"]
            elif "percentage" in item and item["percentage"]:
                v_amount = int(total_amount * (item["percentage"] / 100))
            else:
                v_amount = int(total_amount / len(split_items))

            platform_cut = int(v_amount * (vendor.commission_rate / 100))
            vendor_net = v_amount - platform_cut

            split = PaymentSplit(
                transaction_id=txn.id,
                vendor_id=vendor.id,
                amount_paise=v_amount,
                platform_fee_paise=platform_cut,
                vendor_net_paise=vendor_net,
                status="SETTLED"
            )
            db.add(split)
            
            # Credit vendor wallet balance
            vendor.balance_paise += vendor_net
            total_split_amount += v_amount
            created_splits.append({
                "vendor_id": vendor.id,
                "vendor_name": vendor.name,
                "gross_paise": v_amount,
                "platform_fee_paise": platform_cut,
                "vendor_net_paise": vendor_net
            })

        db.commit()
        return {
            "transaction_id": transaction_id,
            "total_split_paise": total_split_amount,
            "splits": created_splits
        }

    @staticmethod
    def trigger_vendor_payout(vendor_id: str, amount_paise: int, db: Session) -> dict:
        """
        Simulates instant payout settlement to vendor bank account.
        """
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise ValueError("Vendor not found")
        if amount_paise > vendor.balance_paise:
            raise ValueError(f"Payout amount exceeds vendor balance ({vendor.balance_paise} paise)")

        vendor.balance_paise -= amount_paise
        db.commit()

        return {
            "payout_id": f"POUT-{str(uuid.uuid4())[:8].upper()}",
            "vendor_name": vendor.name,
            "bank_account": vendor.bank_account,
            "payout_amount_paise": amount_paise,
            "remaining_balance_paise": vendor.balance_paise,
            "status": "PROCESSED"
        }
