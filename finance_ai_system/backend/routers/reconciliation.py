"""
Reconciliation Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.reconciliation_service import run_ap_reconciliation, run_ar_reconciliation, get_reconciliation_results

router = APIRouter()

@router.post("/run/ap")
def reconcile_ap(db: Session = Depends(get_db)):
    return run_ap_reconciliation(db)

@router.post("/run/ar")
def reconcile_ar(db: Session = Depends(get_db)):
    return run_ar_reconciliation(db)

@router.get("/results/ap")
def ap_results(db: Session = Depends(get_db)):
    return get_reconciliation_results(db, "ap")

@router.get("/results/ar")
def ar_results(db: Session = Depends(get_db)):
    return get_reconciliation_results(db, "ar")
