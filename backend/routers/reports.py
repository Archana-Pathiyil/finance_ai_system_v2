"""
Reports Router - Excel report downloads
"""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from services.report_service import (
    generate_ap_outstanding_report, generate_payment_due_report,
    generate_ar_ageing_report, generate_collection_followup_report,
    generate_reconciliation_report
)

router = APIRouter()

EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/ap-outstanding")
def report_ap_outstanding(db: Session = Depends(get_db)):
    data = generate_ap_outstanding_report(db)
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": "attachment; filename=ap_outstanding.xlsx"})


@router.get("/payment-due")
def report_payment_due(db: Session = Depends(get_db)):
    data = generate_payment_due_report(db)
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": "attachment; filename=payment_due.xlsx"})


@router.get("/ar-ageing")
def report_ar_ageing(db: Session = Depends(get_db)):
    data = generate_ar_ageing_report(db)
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": "attachment; filename=ar_ageing.xlsx"})


@router.get("/collection-followup")
def report_collection_followup(db: Session = Depends(get_db)):
    data = generate_collection_followup_report(db)
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": "attachment; filename=collection_followup.xlsx"})


@router.get("/reconciliation/{rec_type}")
def report_reconciliation(rec_type: str, db: Session = Depends(get_db)):
    if rec_type not in ("ap", "ar"):
        from fastapi import HTTPException
        raise HTTPException(400, "rec_type must be 'ap' or 'ar'")
    data = generate_reconciliation_report(db, rec_type)
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": f"attachment; filename=reconciliation_{rec_type}.xlsx"})


@router.get("/party-statement/ap")
def party_statement_ap(vendor: str, db: Session = Depends(get_db)):
    from services.report_service import generate_party_statement_ap
    from fastapi import HTTPException
    if not vendor:
        raise HTTPException(400, "vendor name required")
    data = generate_party_statement_ap(db, vendor)
    safe = vendor.replace(" ", "_").replace("/", "-")
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": f"attachment; filename=statement_AP_{safe}.xlsx"})


@router.get("/party-statement/ar")
def party_statement_ar(customer: str, db: Session = Depends(get_db)):
    from services.report_service import generate_party_statement_ar
    from fastapi import HTTPException
    if not customer:
        raise HTTPException(400, "customer name required")
    data = generate_party_statement_ar(db, customer)
    safe = customer.replace(" ", "_").replace("/", "-")
    return Response(content=data, media_type=EXCEL_MIME,
                    headers={"Content-Disposition": f"attachment; filename=statement_AR_{safe}.xlsx"})
