"""
Date Utilities - Payment due date calculations and ageing logic
"""
from datetime import date, timedelta
from typing import Optional


def calculate_due_date(invoice_date: date, payment_days: int = 45) -> date:
    """Calculate payment due date based on invoice date."""
    return invoice_date + timedelta(days=payment_days)


def days_overdue(due_date: date, reference_date: Optional[date] = None) -> int:
    """Return number of days overdue. Negative means still within terms."""
    ref = reference_date or date.today()
    return (ref - due_date).days


def get_ageing_bucket(invoice_date: date, reference_date: Optional[date] = None) -> str:
    """Classify an invoice into an ageing bucket."""
    ref = reference_date or date.today()
    age = (ref - invoice_date).days
    if age <= 30:
        return "0-30"
    elif age <= 60:
        return "31-60"
    elif age <= 90:
        return "61-90"
    else:
        return "90+"


def get_payment_status(due_date: date, reference_date: Optional[date] = None) -> str:
    """Classify payment status relative to due date."""
    ref = reference_date or date.today()
    days = (due_date - ref).days
    if days < 0:
        return "overdue"
    elif days <= 7:
        return "due"
    else:
        return "upcoming"


def days_until_due(due_date: date, reference_date: Optional[date] = None) -> int:
    """Return days remaining until due date (negative if overdue)."""
    ref = reference_date or date.today()
    return (due_date - ref).days
