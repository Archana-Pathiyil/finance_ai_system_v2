"""
Ingestion Service - Handles file parsing and storage into the database
"""
import pandas as pd
from datetime import datetime, date
from sqlalchemy.orm import Session
from models.models import UploadHistory, VendorLedger, CustomerLedger, SOARecord
from utils.file_parser import (
    parse_vendor_ledger, parse_customer_ledger, parse_soa, get_preview
)
from utils.date_utils import calculate_due_date
from config import AP_PAYMENT_DAYS
import math


def _safe_float(val) -> float:
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except Exception:
        return 0.0


def _safe_date(val):
    try:
        if val is None:
            return None
        # Already a date object
        if isinstance(val, date):
            return val
        # Pandas Timestamp or datetime
        if hasattr(val, "date"):
            return val.date()
        # String like "2025-01-20"
        if isinstance(val, str) and val.strip():
            return pd.to_datetime(val.strip()).date()
        # Check for pandas NaT / NaN
        if pd.isnull(val):
            return None
        return None
    except Exception:
        return None


def create_upload_record(db: Session, filename: str, doc_type: str) -> UploadHistory:
    record = UploadHistory(filename=filename, document_type=doc_type, status="pending")
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def process_vendor_ledger(db: Session, content: bytes, filename: str) -> dict:
    """Parse and store vendor ledger data."""
    upload = create_upload_record(db, filename, "vendor_ledger")
    try:
        df = parse_vendor_ledger(content, filename)
        rows = []
        for _, row in df.iterrows():
            inv_date = _safe_date(row.get("Invoice Date"))
            due_date = _safe_date(row.get("Due Date")) or (
                calculate_due_date(inv_date, AP_PAYMENT_DAYS) if inv_date else None
            )
            rows.append(VendorLedger(
                upload_id=upload.id,
                vendor_name=str(row.get("Vendor Name", "")).strip(),
                vendor_code=str(row.get("Vendor Code", "")).strip() or None,
                invoice_no=str(row.get("Invoice No", "")).strip(),
                invoice_date=inv_date,
                due_date=due_date,
                amount=_safe_float(row.get("Amount", 0)),
                paid_amount=_safe_float(row.get("Paid Amount", 0)),
                outstanding=_safe_float(row.get("Outstanding", 0)),
                currency=str(row.get("Currency", "AED")).strip(),
                description=str(row.get("Description", "")).strip() or None,
            ))
        db.bulk_save_objects(rows)
        upload.status = "processed"
        upload.row_count = len(rows)
        upload.processed_at = datetime.utcnow()
        db.commit()
        return {"upload_id": upload.id, "rows_imported": len(rows), "preview": get_preview(df)}
    except Exception as e:
        upload.status = "failed"
        upload.error_message = str(e)
        db.commit()
        raise


def process_customer_ledger(db: Session, content: bytes, filename: str) -> dict:
    """Parse and store customer ledger data."""
    upload = create_upload_record(db, filename, "customer_ledger")
    try:
        df = parse_customer_ledger(content, filename)
        rows = []
        for _, row in df.iterrows():
            inv_date = _safe_date(row.get("Invoice Date"))
            rows.append(CustomerLedger(
                upload_id=upload.id,
                customer_name=str(row.get("Customer Name", "")).strip(),
                customer_code=str(row.get("Customer Code", "")).strip() or None,
                invoice_no=str(row.get("Invoice No", "")).strip(),
                invoice_date=inv_date,
                due_date=_safe_date(row.get("Due Date")),
                amount=_safe_float(row.get("Amount", 0)),
                received_amount=_safe_float(row.get("Received Amount", 0)),
                outstanding=_safe_float(row.get("Outstanding", 0)),
                currency=str(row.get("Currency", "AED")).strip(),
                description=str(row.get("Description", "")).strip() or None,
            ))
        db.bulk_save_objects(rows)
        upload.status = "processed"
        upload.row_count = len(rows)
        upload.processed_at = datetime.utcnow()
        db.commit()
        return {"upload_id": upload.id, "rows_imported": len(rows), "preview": get_preview(df)}
    except Exception as e:
        upload.status = "failed"
        upload.error_message = str(e)
        db.commit()
        raise


def process_soa(db: Session, content: bytes, filename: str, party_type: str) -> dict:
    """Parse and store SOA data."""
    upload = create_upload_record(db, filename, "soa")
    try:
        df = parse_soa(content, filename)
        rows = []
        for _, row in df.iterrows():
            rows.append(SOARecord(
                upload_id=upload.id,
                party_name=str(row.get("Party Name", "")).strip(),
                party_type=party_type,
                invoice_no=str(row.get("Invoice No", "")).strip(),
                invoice_date=_safe_date(row.get("Invoice Date")),
                amount=_safe_float(row.get("Amount", 0)),
                currency=str(row.get("Currency", "AED")).strip(),
            ))
        db.bulk_save_objects(rows)
        upload.status = "processed"
        upload.row_count = len(rows)
        upload.processed_at = datetime.utcnow()
        db.commit()
        return {"upload_id": upload.id, "rows_imported": len(rows), "preview": get_preview(df)}
    except Exception as e:
        upload.status = "failed"
        upload.error_message = str(e)
        db.commit()
        raise


def get_upload_history(db: Session) -> list:
    return db.query(UploadHistory).order_by(UploadHistory.uploaded_at.desc()).all()
