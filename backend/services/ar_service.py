"""
Accounts Receivable Service - AR processing, ageing, and collection logic
"""
from datetime import date
from sqlalchemy.orm import Session
from models.models import CustomerLedger
from utils.date_utils import get_ageing_bucket
from config import AR_FOLLOWUP_DAYS


def get_ar_summary(db: Session) -> dict:
    """Get high-level AR KPIs."""
    records = db.query(CustomerLedger).all()
    if not records:
        return {
            "total_customers": 0,
            "total_invoices": 0,
            "total_outstanding": 0.0,
            "overdue_amount": 0.0,
            "overdue_percentage": 0.0,
            "currency": "AED",
        }

    total_outstanding = sum(r.outstanding or 0 for r in records)
    customers = set(r.customer_name for r in records)

    overdue_amount = 0.0
    for r in records:
        if r.invoice_date:
            bucket = get_ageing_bucket(r.invoice_date)
            if bucket != "0-30":
                overdue_amount += r.outstanding or 0

    overdue_pct = (overdue_amount / total_outstanding * 100) if total_outstanding else 0

    return {
        "total_customers": len(customers),
        "total_invoices": len(records),
        "total_outstanding": round(total_outstanding, 2),
        "overdue_amount": round(overdue_amount, 2),
        "overdue_percentage": round(overdue_pct, 2),
        "currency": "AED",
    }


def get_ageing_report(db: Session) -> list:
    """Customer-wise ageing breakdown."""
    records = db.query(CustomerLedger).filter(CustomerLedger.outstanding > 0).all()
    customer_map = {}
    for r in records:
        name = r.customer_name
        if name not in customer_map:
            customer_map[name] = {
                "customer_name": name,
                "total_outstanding": 0.0,
                "bucket_0_30": 0.0,
                "bucket_31_60": 0.0,
                "bucket_61_90": 0.0,
                "bucket_90_plus": 0.0,
            }
        amt = r.outstanding or 0
        customer_map[name]["total_outstanding"] += amt

        if r.invoice_date:
            bucket = get_ageing_bucket(r.invoice_date)
            if bucket == "0-30":
                customer_map[name]["bucket_0_30"] += amt
            elif bucket == "31-60":
                customer_map[name]["bucket_31_60"] += amt
            elif bucket == "61-90":
                customer_map[name]["bucket_61_90"] += amt
            else:
                customer_map[name]["bucket_90_plus"] += amt

    result = list(customer_map.values())
    for row in result:
        for k in ["total_outstanding", "bucket_0_30", "bucket_31_60", "bucket_61_90", "bucket_90_plus"]:
            row[k] = round(row[k], 2)
    return sorted(result, key=lambda x: -x["total_outstanding"])


def get_ageing_buckets_total(db: Session) -> list:
    """Aggregate ageing buckets across all customers for charts."""
    records = db.query(CustomerLedger).filter(CustomerLedger.outstanding > 0).all()
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    total = 0.0
    for r in records:
        if r.invoice_date:
            b = get_ageing_bucket(r.invoice_date)
            buckets[b] = buckets.get(b, 0) + (r.outstanding or 0)
            total += r.outstanding or 0

    return [
        {
            "bucket": k,
            "amount": round(v, 2),
            "invoice_count": sum(
                1 for r in records
                if r.invoice_date and get_ageing_bucket(r.invoice_date) == k
            ),
            "percentage": round((v / total * 100) if total else 0, 2),
        }
        for k, v in buckets.items()
    ]


def get_collection_followup(db: Session) -> list:
    """Invoices overdue by more than AR_FOLLOWUP_DAYS requiring follow-up."""
    records = db.query(CustomerLedger).filter(CustomerLedger.outstanding > 0).all()
    result = []
    for r in records:
        if r.invoice_date:
            age = (date.today() - r.invoice_date).days
            if age > AR_FOLLOWUP_DAYS:
                result.append({
                    "customer_name": r.customer_name,
                    "invoice_no": r.invoice_no,
                    "invoice_date": r.invoice_date.isoformat(),
                    "days_outstanding": age,
                    "amount": r.amount,
                    "outstanding": r.outstanding,
                    "currency": r.currency,
                    "bucket": get_ageing_bucket(r.invoice_date),
                })
    return sorted(result, key=lambda x: -x["days_outstanding"])


def get_customer_wise_summary(db: Session) -> list:
    """Group invoices by customer."""
    records = db.query(CustomerLedger).all()
    cust_map = {}
    for r in records:
        name = r.customer_name
        if name not in cust_map:
            cust_map[name] = {
                "customer_name": name,
                "invoice_count": 0,
                "total_amount": 0.0,
                "total_outstanding": 0.0,
                "currency": r.currency,
            }
        cust_map[name]["invoice_count"] += 1
        cust_map[name]["total_amount"] += r.amount
        cust_map[name]["total_outstanding"] += r.outstanding or 0

    return sorted(cust_map.values(), key=lambda x: -x["total_outstanding"])


def get_all_customer_invoices(db: Session, customer_name: str = None) -> list:
    q = db.query(CustomerLedger)
    if customer_name:
        q = q.filter(CustomerLedger.customer_name.ilike(f"%{customer_name}%"))
    records = q.order_by(CustomerLedger.invoice_date.desc()).all()
    return [
        {
            "id": r.id,
            "customer_name": r.customer_name,
            "invoice_no": r.invoice_no,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "amount": r.amount,
            "received_amount": r.received_amount,
            "outstanding": r.outstanding,
            "currency": r.currency,
            "ageing_bucket": get_ageing_bucket(r.invoice_date) if r.invoice_date else "N/A",
        }
        for r in records
    ]
