"""
Accounts Payable Service - Core AP processing and analytics
"""
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import VendorLedger
from utils.date_utils import calculate_due_date, get_payment_status, days_until_due
from config import AP_PAYMENT_DAYS


def get_ap_summary(db: Session) -> dict:
    """Get high-level AP KPIs."""
    records = db.query(VendorLedger).all()
    if not records:
        return {
            "total_vendors": 0,
            "total_invoices": 0,
            "total_outstanding": 0.0,
            "due_this_month": 0.0,
            "overdue_amount": 0.0,
            "currency": "AED",
        }

    today = date.today()
    total_outstanding = sum(r.outstanding or 0 for r in records)
    vendors = set(r.vendor_name for r in records)

    due_this_month = 0.0
    overdue_amount = 0.0
    for r in records:
        if r.due_date:
            status = get_payment_status(r.due_date)
            if status == "overdue":
                overdue_amount += r.outstanding or 0
            elif status in ("due", "upcoming") and r.due_date.month == today.month:
                due_this_month += r.outstanding or 0

    return {
        "total_vendors": len(vendors),
        "total_invoices": len(records),
        "total_outstanding": round(total_outstanding, 2),
        "due_this_month": round(due_this_month, 2),
        "overdue_amount": round(overdue_amount, 2),
        "currency": "AED",
    }


def get_payment_due_report(db: Session) -> list:
    """Get payment due schedule applying 45-day rule."""
    records = db.query(VendorLedger).filter(VendorLedger.outstanding > 0).all()
    result = []
    for r in records:
        due_date = r.due_date or calculate_due_date(r.invoice_date, AP_PAYMENT_DAYS)
        status = get_payment_status(due_date)
        d = days_until_due(due_date)
        result.append({
            "vendor_name": r.vendor_name,
            "invoice_no": r.invoice_no,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "due_date": due_date.isoformat(),
            "amount": r.amount,
            "outstanding": r.outstanding,
            "days_until_due": d,
            "status": status,
        })
    # Sort: overdue first, then by due date
    result.sort(key=lambda x: x["days_until_due"])
    return result


def get_vendor_wise_summary(db: Session) -> list:
    """Group invoices by vendor."""
    records = db.query(VendorLedger).all()
    vendor_map = {}
    for r in records:
        name = r.vendor_name
        if name not in vendor_map:
            vendor_map[name] = {
                "vendor_name": name,
                "vendor_code": r.vendor_code,
                "invoice_count": 0,
                "total_amount": 0.0,
                "total_outstanding": 0.0,
                "currency": r.currency,
            }
        vendor_map[name]["invoice_count"] += 1
        vendor_map[name]["total_amount"] += r.amount
        vendor_map[name]["total_outstanding"] += r.outstanding or 0

    return sorted(vendor_map.values(), key=lambda x: -x["total_outstanding"])


def get_all_vendor_invoices(db: Session, vendor_name: str = None) -> list:
    """Get all vendor ledger records, optionally filtered by vendor."""
    q = db.query(VendorLedger)
    if vendor_name:
        q = q.filter(VendorLedger.vendor_name.ilike(f"%{vendor_name}%"))
    records = q.order_by(VendorLedger.invoice_date.desc()).all()
    return [
        {
            "id": r.id,
            "vendor_name": r.vendor_name,
            "vendor_code": r.vendor_code,
            "invoice_no": r.invoice_no,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "due_date": r.due_date.isoformat() if r.due_date else None,
            "amount": r.amount,
            "paid_amount": r.paid_amount,
            "outstanding": r.outstanding,
            "currency": r.currency,
        }
        for r in records
    ]


def get_cash_outflow_trend(db: Session) -> list:
    """Monthly cash outflow trend for charts."""
    records = db.query(VendorLedger).all()
    monthly = {}
    for r in records:
        if r.invoice_date:
            key = r.invoice_date.strftime("%Y-%m")
            monthly[key] = monthly.get(key, 0) + (r.amount or 0)
    return [{"month": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())]
