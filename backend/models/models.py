"""
Database Models - SQLAlchemy ORM
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class UploadStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    VENDOR_LEDGER = "vendor_ledger"
    CUSTOMER_LEDGER = "customer_ledger"
    SOA = "soa"


class MatchStatus(str, enum.Enum):
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    DISCREPANCY = "discrepancy"


class UploadHistory(Base):
    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    document_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    row_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)


class VendorLedger(Base):
    __tablename__ = "vendor_ledger"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)
    vendor_code = Column(String(50), nullable=True)
    vendor_name = Column(String(255), nullable=False)
    invoice_no = Column(String(100), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    outstanding = Column(Float, nullable=True)
    currency = Column(String(10), default="AED")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


class CustomerLedger(Base):
    __tablename__ = "customer_ledger"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)
    customer_code = Column(String(50), nullable=True)
    customer_name = Column(String(255), nullable=False)
    invoice_no = Column(String(100), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    received_amount = Column(Float, default=0.0)
    outstanding = Column(Float, nullable=True)
    currency = Column(String(10), default="AED")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


class SOARecord(Base):
    __tablename__ = "soa_records"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, nullable=False)
    party_name = Column(String(255), nullable=False)
    party_type = Column(String(20), nullable=False)  # vendor / customer
    invoice_no = Column(String(100), nullable=False, index=True)
    invoice_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="AED")
    created_at = Column(DateTime, default=func.now())


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True)
    reconciliation_type = Column(String(20), nullable=False)  # ap / ar
    party_name = Column(String(255), nullable=False)
    invoice_no = Column(String(100), nullable=False)
    erp_amount = Column(Float, nullable=True)
    soa_amount = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    status = Column(String(20), nullable=False)  # matched / unmatched / discrepancy
    created_at = Column(DateTime, default=func.now())
