"""
Upload Router - File upload endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from services.ingestion_service import (
    process_vendor_ledger, process_customer_ledger, process_soa, get_upload_history
)
from utils.file_parser import validate_extension, parse_vendor_ledger, parse_customer_ledger, parse_soa, get_preview

router = APIRouter()


@router.post("/vendor-ledger")
async def upload_vendor_ledger(file: UploadFile = File(...), db: Session = Depends(get_db)):
    validate_extension(file.filename)
    content = await file.read()
    result = process_vendor_ledger(db, content, file.filename)
    return {"message": "Vendor ledger uploaded successfully", **result}


@router.post("/customer-ledger")
async def upload_customer_ledger(file: UploadFile = File(...), db: Session = Depends(get_db)):
    validate_extension(file.filename)
    content = await file.read()
    result = process_customer_ledger(db, content, file.filename)
    return {"message": "Customer ledger uploaded successfully", **result}


@router.post("/soa")
async def upload_soa(
    file: UploadFile = File(...),
    party_type: str = Query("vendor", description="vendor or customer"),
    db: Session = Depends(get_db),
):
    if party_type not in ("vendor", "customer"):
        raise HTTPException(400, "party_type must be 'vendor' or 'customer'")
    validate_extension(file.filename)
    content = await file.read()
    result = process_soa(db, content, file.filename, party_type)
    return {"message": "SOA uploaded successfully", **result}


@router.post("/preview/vendor-ledger")
async def preview_vendor_ledger(file: UploadFile = File(...)):
    """Preview vendor ledger without saving to DB."""
    validate_extension(file.filename)
    content = await file.read()
    df = parse_vendor_ledger(content, file.filename)
    return get_preview(df)


@router.post("/preview/customer-ledger")
async def preview_customer_ledger(file: UploadFile = File(...)):
    validate_extension(file.filename)
    content = await file.read()
    df = parse_customer_ledger(content, file.filename)
    return get_preview(df)


@router.post("/preview/soa")
async def preview_soa(file: UploadFile = File(...)):
    validate_extension(file.filename)
    content = await file.read()
    df = parse_soa(content, file.filename)
    return get_preview(df)


@router.get("/history")
def upload_history(db: Session = Depends(get_db)):
    records = get_upload_history(db)
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "document_type": r.document_type,
            "status": r.status,
            "row_count": r.row_count,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "error_message": r.error_message,
        }
        for r in records
    ]
