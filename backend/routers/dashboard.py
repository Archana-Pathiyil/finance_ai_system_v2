"""
Dashboard Router - Enhanced with filters, MIS, drill-down, cashflow
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.ap_service import get_ap_summary, get_vendor_wise_summary, get_cash_outflow_trend
from services.ar_service import get_ar_summary, get_ageing_buckets_total
from models.models import VendorLedger, CustomerLedger
from utils.date_utils import get_ageing_bucket, calculate_due_date, get_payment_status
from config import AP_PAYMENT_DAYS
from datetime import date
from collections import defaultdict

router = APIRouter()


@router.get("/kpis")
def dashboard_kpis(db: Session = Depends(get_db)):
    ap = get_ap_summary(db)
    ar = get_ar_summary(db)
    return {
        "total_payables": ap["total_outstanding"],
        "total_receivables": ar["total_outstanding"],
        "due_this_month": ap["due_this_month"],
        "overdue_payables": ap["overdue_amount"],
        "overdue_receivables": ar["overdue_amount"],
        "overdue_percentage": ar["overdue_percentage"],
        "net_position": round(ar["total_outstanding"] - ap["total_outstanding"], 2),
        "currency": "AED",
    }


@router.get("/charts")
def dashboard_charts(db: Session = Depends(get_db)):
    return {
        "cash_outflow_trend": get_cash_outflow_trend(db),
        "ar_ageing_buckets": get_ageing_buckets_total(db),
        "top_vendors": get_vendor_wise_summary(db)[:5],
    }


@router.get("/vendors")
def list_vendors(db: Session = Depends(get_db)):
    rows = db.query(VendorLedger.vendor_name).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@router.get("/customers")
def list_customers(db: Session = Depends(get_db)):
    rows = db.query(CustomerLedger.customer_name).distinct().all()
    return sorted([r[0] for r in rows if r[0]])


@router.get("/months")
def list_months(db: Session = Depends(get_db)):
    months = set()
    for r in db.query(VendorLedger).all():
        if r.invoice_date:
            months.add(r.invoice_date.strftime("%Y-%m"))
    for r in db.query(CustomerLedger).all():
        if r.invoice_date:
            months.add(r.invoice_date.strftime("%Y-%m"))
    return sorted(months)


@router.get("/vendor-drill")
def vendor_drill(vendor: str = Query(...), db: Session = Depends(get_db)):
    records = db.query(VendorLedger).filter(VendorLedger.vendor_name == vendor).all()
    if not records:
        return {}
    total_amount = sum(r.amount for r in records)
    total_paid = sum(r.paid_amount for r in records)
    total_outstanding = sum(r.outstanding or 0 for r in records)
    overdue = 0.0
    upcoming = 0.0
    monthly = defaultdict(float)
    invoices = []
    for r in records:
        due = r.due_date or calculate_due_date(r.invoice_date, AP_PAYMENT_DAYS)
        status = get_payment_status(due)
        if status == "overdue":
            overdue += r.outstanding or 0
        elif status in ("due", "upcoming"):
            upcoming += r.outstanding or 0
        if r.invoice_date:
            monthly[r.invoice_date.strftime("%Y-%m")] += r.amount
        invoices.append({
            "invoice_no": r.invoice_no,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "due_date": due.isoformat(),
            "amount": r.amount,
            "paid_amount": r.paid_amount,
            "outstanding": r.outstanding,
            "status": status,
        })
    payment_rate = round((total_paid / total_amount * 100) if total_amount else 0, 1)
    return {
        "vendor_name": vendor,
        "vendor_code": records[0].vendor_code,
        "invoice_count": len(records),
        "total_amount": round(total_amount, 2),
        "total_paid": round(total_paid, 2),
        "total_outstanding": round(total_outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "upcoming_amount": round(upcoming, 2),
        "payment_rate": payment_rate,
        "monthly_trend": [{"month": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())],
        "invoices": sorted(invoices, key=lambda x: x["invoice_date"] or "", reverse=True),
        "currency": "AED",
    }


@router.get("/customer-drill")
def customer_drill(customer: str = Query(...), db: Session = Depends(get_db)):
    records = db.query(CustomerLedger).filter(CustomerLedger.customer_name == customer).all()
    if not records:
        return {}
    total_amount = sum(r.amount for r in records)
    total_received = sum(r.received_amount for r in records)
    total_outstanding = sum(r.outstanding or 0 for r in records)
    buckets = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "90+": 0.0}
    monthly = defaultdict(float)
    invoices = []
    for r in records:
        bucket = get_ageing_bucket(r.invoice_date) if r.invoice_date else "0-30"
        buckets[bucket] += r.outstanding or 0
        if r.invoice_date:
            monthly[r.invoice_date.strftime("%Y-%m")] += r.amount
        invoices.append({
            "invoice_no": r.invoice_no,
            "invoice_date": r.invoice_date.isoformat() if r.invoice_date else None,
            "amount": r.amount,
            "received_amount": r.received_amount,
            "outstanding": r.outstanding,
            "bucket": bucket,
        })
    return {
        "customer_name": customer,
        "invoice_count": len(records),
        "total_amount": round(total_amount, 2),
        "total_received": round(total_received, 2),
        "total_outstanding": round(total_outstanding, 2),
        "collection_rate": round((total_received / total_amount * 100) if total_amount else 0, 1),
        "ageing_buckets": [{"bucket": k, "amount": round(v, 2)} for k, v in buckets.items()],
        "monthly_trend": [{"month": k, "amount": round(v, 2)} for k, v in sorted(monthly.items())],
        "invoices": sorted(invoices, key=lambda x: x["invoice_date"] or "", reverse=True),
        "currency": "AED",
    }


@router.get("/mis")
def mis_summary(month: str = Query(None), db: Session = Depends(get_db)):
    vl = db.query(VendorLedger).all()
    cl = db.query(CustomerLedger).all()
    if month:
        vl = [r for r in vl if r.invoice_date and r.invoice_date.strftime("%Y-%m") == month]
        cl = [r for r in cl if r.invoice_date and r.invoice_date.strftime("%Y-%m") == month]
    ap_invoiced = sum(r.amount for r in vl)
    ar_invoiced = sum(r.amount for r in cl)
    ap_paid = sum(r.paid_amount for r in vl)
    ar_received = sum(r.received_amount for r in cl)
    ap_total = sum(r.outstanding or 0 for r in vl)
    ar_total = sum(r.outstanding or 0 for r in cl)
    overdue_ap = sum(r.outstanding or 0 for r in vl if r.due_date and get_payment_status(r.due_date) == "overdue")
    overdue_ar = sum(r.outstanding or 0 for r in cl if r.invoice_date and get_ageing_bucket(r.invoice_date) != "0-30")
    ap_monthly = defaultdict(float)
    ar_monthly = defaultdict(float)
    for r in db.query(VendorLedger).all():
        if r.invoice_date:
            ap_monthly[r.invoice_date.strftime("%Y-%m")] += r.amount
    for r in db.query(CustomerLedger).all():
        if r.invoice_date:
            ar_monthly[r.invoice_date.strftime("%Y-%m")] += r.amount
    all_months = sorted(set(list(ap_monthly.keys()) + list(ar_monthly.keys())))
    cashflow_trend = [
        {"month": m, "payables": round(ap_monthly.get(m, 0), 2),
         "receivables": round(ar_monthly.get(m, 0), 2),
         "net": round(ar_monthly.get(m, 0) - ap_monthly.get(m, 0), 2)}
        for m in all_months
    ]
    return {
        "period": month or "All Time",
        "ap_invoiced": round(ap_invoiced, 2),
        "ar_invoiced": round(ar_invoiced, 2),
        "ap_outstanding": round(ap_total, 2),
        "ar_outstanding": round(ar_total, 2),
        "ap_paid": round(ap_paid, 2),
        "ar_received": round(ar_received, 2),
        "overdue_ap": round(overdue_ap, 2),
        "overdue_ar": round(overdue_ar, 2),
        "net_cashflow": round(ar_received - ap_paid, 2),
        "working_capital": round(ar_total - ap_total, 2),
        "ap_payment_rate": round((ap_paid / ap_invoiced * 100) if ap_invoiced else 0, 1),
        "ar_collection_rate": round((ar_received / ar_invoiced * 100) if ar_invoiced else 0, 1),
        "cashflow_trend": cashflow_trend,
        "currency": "AED",
    }


@router.get("/cashflow")
def cashflow_insights(db: Session = Depends(get_db)):
    vl = db.query(VendorLedger).filter(VendorLedger.outstanding > 0).all()
    cl = db.query(CustomerLedger).filter(CustomerLedger.outstanding > 0).all()
    ap_due = defaultdict(float)
    for r in vl:
        due = r.due_date or calculate_due_date(r.invoice_date, AP_PAYMENT_DAYS)
        ap_due[due.strftime("%Y-%m")] += r.outstanding or 0
    ar_expected = defaultdict(float)
    for r in cl:
        if r.invoice_date:
            ar_expected[r.invoice_date.strftime("%Y-%m")] += r.outstanding or 0
    all_months = sorted(set(list(ap_due.keys()) + list(ar_expected.keys())))
    forecast = [
        {"month": m, "cash_out": round(ap_due.get(m, 0), 2),
         "cash_in": round(ar_expected.get(m, 0), 2),
         "net": round(ar_expected.get(m, 0) - ap_due.get(m, 0), 2)}
        for m in all_months
    ]
    overdue_ap = [r for r in vl if r.due_date and get_payment_status(r.due_date) == "overdue"]
    critical_ar = [r for r in cl if r.invoice_date and get_ageing_bucket(r.invoice_date) == "90+"]
    return {
        "forecast": forecast,
        "total_cash_out_pending": round(sum(r.outstanding or 0 for r in vl), 2),
        "total_cash_in_pending": round(sum(r.outstanding or 0 for r in cl), 2),
        "overdue_ap_count": len(overdue_ap),
        "overdue_ap_amount": round(sum(r.outstanding or 0 for r in overdue_ap), 2),
        "critical_ar_count": len(critical_ar),
        "critical_ar_amount": round(sum(r.outstanding or 0 for r in critical_ar), 2),
        "currency": "AED",
    }
