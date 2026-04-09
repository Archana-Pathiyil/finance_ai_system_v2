"""
AR Router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from services.ar_service import (
    get_ar_summary, get_ageing_report, get_ageing_buckets_total,
    get_collection_followup, get_customer_wise_summary, get_all_customer_invoices
)

router = APIRouter()

@router.get("/summary")
def ar_summary(db: Session = Depends(get_db)):
    return get_ar_summary(db)

@router.get("/ageing")
def ageing_report(db: Session = Depends(get_db)):
    return get_ageing_report(db)

@router.get("/ageing-buckets")
def ageing_buckets(db: Session = Depends(get_db)):
    return get_ageing_buckets_total(db)

@router.get("/collection-followup")
def collection_followup(db: Session = Depends(get_db)):
    return get_collection_followup(db)

@router.get("/customers")
def customer_summary(db: Session = Depends(get_db)):
    return get_customer_wise_summary(db)

@router.get("/invoices")
def customer_invoices(customer: str = Query(None), db: Session = Depends(get_db)):
    return get_all_customer_invoices(db, customer)


@router.get("/summary-by-party")
def ar_summary_by_party(customer: str = Query(None), month: str = Query(None), db: Session = Depends(get_db)):
    """Dynamic AR KPIs filtered by customer and/or month."""
    from models.models import CustomerLedger
    from utils.date_utils import get_ageing_bucket
    q = db.query(CustomerLedger)
    if customer:
        q = q.filter(CustomerLedger.customer_name == customer)
    records = q.all()
    if month:
        records = [r for r in records if r.invoice_date and r.invoice_date.strftime("%Y-%m") == month]
    total_outstanding = sum(r.outstanding or 0 for r in records)
    overdue = sum(r.outstanding or 0 for r in records
                  if r.invoice_date and get_ageing_bucket(r.invoice_date) != "0-30")
    return {
        "customer": customer or "All Customers",
        "month": month or "All Months",
        "total_invoices": len(records),
        "total_outstanding": round(total_outstanding, 2),
        "overdue_amount": round(overdue, 2),
        "overdue_percentage": round((overdue / total_outstanding * 100) if total_outstanding else 0, 1),
        "customers": len(set(r.customer_name for r in records)),
        "currency": "AED",
    }


@router.get("/ageing-by-party")
def ageing_by_party(customer: str = Query(None), db: Session = Depends(get_db)):
    """AR ageing filtered by customer."""
    from services.ar_service import get_ageing_report
    data = get_ageing_report(db)
    if customer:
        data = [d for d in data if d["customer_name"] == customer]
    return data
