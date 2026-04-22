"""
Mail Router - Simulated email notifications for AP/AR parties
In production, replace smtplib section with real SMTP or SendGrid config.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.models import VendorLedger, CustomerLedger, ReconciliationResult
from utils.date_utils import calculate_due_date, get_payment_status, get_ageing_bucket
from config import AP_PAYMENT_DAYS
from datetime import date, datetime

router = APIRouter()


class MailRequest(BaseModel):
    party_name: str
    party_type: str          # "vendor" | "customer"
    cc_department: str       # "AP" | "AR"
    subject: str = ""
    custom_message: str = ""


def _build_ap_email_body(vendor_name: str, records, recon_map: dict) -> str:
    total_outstanding = sum(r.outstanding or 0 for r in records)
    overdue = [r for r in records if r.due_date and get_payment_status(r.due_date) == "overdue"]

    lines = [
        f"Dear {vendor_name},",
        "",
        f"Please find below a summary of your outstanding invoices as of {date.today().isoformat()}.",
        "",
        "INVOICE DETAILS:",
        "-" * 60,
    ]
    for r in records:
        due = r.due_date or calculate_due_date(r.invoice_date, AP_PAYMENT_DAYS)
        status = get_payment_status(due)
        rec = recon_map.get(r.invoice_no)
        recon_status = rec.status if rec else "Pending Reconciliation"
        fine = f" | Difference: AED {abs(rec.difference or 0):,.2f}" if rec and rec.difference else ""
        lines.append(
            f"  Invoice: {r.invoice_no} | Date: {r.invoice_date} | "
            f"Amount: AED {r.amount:,.2f} | Outstanding: AED {r.outstanding or 0:,.2f} | "
            f"Due: {due} | Status: {status.upper()} | Recon: {recon_status}{fine}"
        )

    lines += [
        "-" * 60,
        f"Total Outstanding: AED {total_outstanding:,.2f}",
        f"Overdue Invoices: {len(overdue)}",
        "",
        "Kindly arrange payment for overdue invoices at the earliest.",
        "Please contact our AP department for any queries.",
        "",
        "Regards,",
        "Accounts Payable Department",
        f"Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    ]
    return "\n".join(lines)


def _build_ar_email_body(customer_name: str, records, recon_map: dict) -> str:
    total_outstanding = sum(r.outstanding or 0 for r in records)
    critical = [r for r in records if r.invoice_date and get_ageing_bucket(r.invoice_date) == "90+"]

    lines = [
        f"Dear {customer_name},",
        "",
        f"This is a reminder regarding outstanding invoices on your account as of {date.today().isoformat()}.",
        "",
        "INVOICE DETAILS:",
        "-" * 60,
    ]
    for r in records:
        bucket = get_ageing_bucket(r.invoice_date) if r.invoice_date else "N/A"
        rec = recon_map.get(r.invoice_no)
        recon_status = rec.status if rec else "Pending Reconciliation"
        fine = f" | Difference: AED {abs(rec.difference or 0):,.2f}" if rec and rec.difference else ""
        lines.append(
            f"  Invoice: {r.invoice_no} | Date: {r.invoice_date} | "
            f"Amount: AED {r.amount:,.2f} | Outstanding: AED {r.outstanding or 0:,.2f} | "
            f"Ageing: {bucket} days | Recon: {recon_status}{fine}"
        )

    lines += [
        "-" * 60,
        f"Total Outstanding: AED {total_outstanding:,.2f}",
        f"Critical (90+ days): {len(critical)} invoice(s)",
        "",
        "Please arrange settlement at the earliest to avoid further escalation.",
        "Contact our AR department for payment plans or queries.",
        "",
        "Regards,",
        "Accounts Receivable Department",
        f"Sent: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    ]
    return "\n".join(lines)


@router.post("/send")
def send_mail(req: MailRequest, db: Session = Depends(get_db)):
    """
    Simulate sending an email to the party.
    Returns the email body that would be sent.
    In production: configure SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    and replace the return with actual smtplib / SendGrid dispatch.
    """
    if req.party_type not in ("vendor", "customer"):
        raise HTTPException(400, "party_type must be 'vendor' or 'customer'")

    if req.party_type == "vendor":
        records = db.query(VendorLedger).filter(
            VendorLedger.vendor_name == req.party_name
        ).all()
        if not records:
            raise HTTPException(404, f"No records found for vendor: {req.party_name}")

        recon_map = {r.invoice_no: r for r in db.query(ReconciliationResult).filter(
            ReconciliationResult.reconciliation_type == "ap",
            ReconciliationResult.party_name == req.party_name
        ).all()}

        body = req.custom_message + "\n\n" + _build_ap_email_body(req.party_name, records, recon_map) \
            if req.custom_message else _build_ap_email_body(req.party_name, records, recon_map)

        subject = req.subject or f"AP Statement — {req.party_name} — {date.today().isoformat()}"

    else:
        records = db.query(CustomerLedger).filter(
            CustomerLedger.customer_name == req.party_name
        ).all()
        if not records:
            raise HTTPException(404, f"No records found for customer: {req.party_name}")

        recon_map = {r.invoice_no: r for r in db.query(ReconciliationResult).filter(
            ReconciliationResult.reconciliation_type == "ar",
            ReconciliationResult.party_name == req.party_name
        ).all()}

        body = req.custom_message + "\n\n" + _build_ar_email_body(req.party_name, records, recon_map) \
            if req.custom_message else _build_ar_email_body(req.party_name, records, recon_map)

        subject = req.subject or f"AR Collection Reminder — {req.party_name} — {date.today().isoformat()}"

    # ── PRODUCTION SMTP (uncomment and configure) ──────────────────
    # import smtplib, os
    # from email.mime.text import MIMEText
    # msg = MIMEText(body)
    # msg["Subject"] = subject
    # msg["From"] = os.getenv("SMTP_FROM", "finance@company.com")
    # msg["To"] = f"{req.party_name.lower().replace(' ','.')}@example.com"
    # msg["CC"] = f"{req.cc_department.lower()}@company.com"
    # with smtplib.SMTP(os.getenv("SMTP_HOST","localhost"), int(os.getenv("SMTP_PORT","587"))) as s:
    #     s.starttls()
    #     s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
    #     s.send_message(msg)
    # ──────────────────────────────────────────────────────────────

    return {
        "status": "simulated",
        "message": f"Email prepared for {req.party_name} (CC: {req.cc_department} dept). Configure SMTP in mail.py to enable real dispatch.",
        "subject": subject,
        "cc": f"{req.cc_department}@company.com",
        "body": body,
        "sent_at": datetime.utcnow().isoformat(),
        "invoice_count": len(records),
    }


@router.get("/preview")
def preview_mail(party_name: str, party_type: str, db: Session = Depends(get_db)):
    """Preview email body without sending."""
    if party_type == "vendor":
        records = db.query(VendorLedger).filter(VendorLedger.vendor_name == party_name).all()
        recon_map = {r.invoice_no: r for r in db.query(ReconciliationResult).filter(
            ReconciliationResult.reconciliation_type == "ap",
            ReconciliationResult.party_name == party_name
        ).all()}
        body = _build_ap_email_body(party_name, records, recon_map)
        subject = f"AP Statement — {party_name} — {date.today().isoformat()}"
    else:
        records = db.query(CustomerLedger).filter(CustomerLedger.customer_name == party_name).all()
        recon_map = {r.invoice_no: r for r in db.query(ReconciliationResult).filter(
            ReconciliationResult.reconciliation_type == "ar",
            ReconciliationResult.party_name == party_name
        ).all()}
        body = _build_ar_email_body(party_name, records, recon_map)
        subject = f"AR Reminder — {party_name} — {date.today().isoformat()}"

    return {"subject": subject, "body": body, "invoice_count": len(records)}
