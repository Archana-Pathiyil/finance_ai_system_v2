"""
Pydantic Schemas - Request & Response Validation
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


# ─── Upload Schemas ───────────────────────────────────────────────

class UploadResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    status: str
    row_count: int
    uploaded_at: datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Vendor / AP Schemas ──────────────────────────────────────────

class VendorLedgerOut(BaseModel):
    id: int
    vendor_name: str
    vendor_code: Optional[str]
    invoice_no: str
    invoice_date: date
    due_date: Optional[date]
    amount: float
    paid_amount: float
    outstanding: Optional[float]
    currency: str

    class Config:
        from_attributes = True


class APSummary(BaseModel):
    total_vendors: int
    total_invoices: int
    total_outstanding: float
    due_this_month: float
    overdue_amount: float
    currency: str = "AED"


class PaymentDueItem(BaseModel):
    vendor_name: str
    invoice_no: str
    invoice_date: date
    due_date: date
    amount: float
    outstanding: float
    days_until_due: int
    status: str  # due / upcoming / overdue


# ─── Customer / AR Schemas ────────────────────────────────────────

class CustomerLedgerOut(BaseModel):
    id: int
    customer_name: str
    customer_code: Optional[str]
    invoice_no: str
    invoice_date: date
    due_date: Optional[date]
    amount: float
    received_amount: float
    outstanding: Optional[float]
    currency: str

    class Config:
        from_attributes = True


class ARSummary(BaseModel):
    total_customers: int
    total_invoices: int
    total_outstanding: float
    overdue_amount: float
    overdue_percentage: float
    currency: str = "AED"


class AgeingBucket(BaseModel):
    bucket: str
    amount: float
    invoice_count: int
    percentage: float


class AgeingReport(BaseModel):
    customer_name: str
    total_outstanding: float
    bucket_0_30: float
    bucket_31_60: float
    bucket_61_90: float
    bucket_90_plus: float


# ─── Reconciliation Schemas ───────────────────────────────────────

class ReconciliationItem(BaseModel):
    party_name: str
    invoice_no: str
    erp_amount: Optional[float]
    soa_amount: Optional[float]
    difference: Optional[float]
    status: str  # matched / unmatched / discrepancy


class ReconciliationSummary(BaseModel):
    total_records: int
    matched: int
    unmatched: int
    discrepancies: int
    match_rate: float
    items: List[ReconciliationItem]


# ─── Dashboard Schemas ────────────────────────────────────────────

class DashboardKPIs(BaseModel):
    total_payables: float
    total_receivables: float
    due_this_month: float
    overdue_receivables: float
    overdue_percentage: float
    currency: str = "AED"


# ─── AI Query Schemas ─────────────────────────────────────────────

class AIQueryRequest(BaseModel):
    query: str


class AIQueryResponse(BaseModel):
    query: str
    answer: str
    data: Optional[dict] = None
    chart_type: Optional[str] = None  # bar / pie / line / none
