"""
AP Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.ap_service import (
    get_ap_summary, get_payment_due_report, get_vendor_wise_summary,
    get_all_vendor_invoices, get_cash_outflow_trend
)

router = APIRouter()

@router.get("/summary")
def ap_summary(db: Session = Depends(get_db)):
    return get_ap_summary(db)

@router.get("/payment-due")
def payment_due(db: Session = Depends(get_db)):
    return get_payment_due_report(db)

@router.get("/vendors")
def vendor_summary(db: Session = Depends(get_db)):
    return get_vendor_wise_summary(db)

@router.get("/invoices")
def vendor_invoices(vendor: str = Query(None), db: Session = Depends(get_db)):
    return get_all_vendor_invoices(db, vendor)

@router.get("/cash-outflow-trend")
def cash_outflow(db: Session = Depends(get_db)):
    return get_cash_outflow_trend(db)


@router.get("/summary-by-party")
def ap_summary_by_party(vendor: str = Query(None), month: str = Query(None), db: Session = Depends(get_db)):
    """Dynamic KPIs filtered by vendor and/or month."""
    from models.models import VendorLedger
    from utils.date_utils import calculate_due_date, get_payment_status
    from config import AP_PAYMENT_DAYS
    from datetime import date
    q = db.query(VendorLedger)
    if vendor:
        q = q.filter(VendorLedger.vendor_name == vendor)
    records = q.all()
    if month:
        records = [r for r in records if r.invoice_date and r.invoice_date.strftime("%Y-%m") == month]
    total_outstanding = sum(r.outstanding or 0 for r in records)
    overdue = sum(r.outstanding or 0 for r in records
                  if r.due_date and get_payment_status(r.due_date) == "overdue")
    due_this_month = sum(r.outstanding or 0 for r in records
                         if r.due_date and r.due_date.month == date.today().month
                         and get_payment_status(r.due_date) in ("due", "upcoming"))
    return {
        "vendor": vendor or "All Vendors",
        "month": month or "All Months",
        "total_invoices": len(records),
        "total_outstanding": round(total_outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "due_this_month": round(due_this_month, 2),
        "vendors": len(set(r.vendor_name for r in records)),
        "currency": "AED",
    }


@router.get("/payment-due-by-party")
def payment_due_by_party(vendor: str = Query(None), db: Session = Depends(get_db)):
    """Payment due filtered by vendor."""
    from services.ap_service import get_payment_due_report
    data = get_payment_due_report(db)
    if vendor:
        data = [d for d in data if d["vendor_name"] == vendor]
    return data
