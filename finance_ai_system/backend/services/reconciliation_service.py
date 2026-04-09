"""
Reconciliation Service - Matches ERP ledger vs SOA, flags discrepancies
"""
from sqlalchemy.orm import Session
from models.models import VendorLedger, CustomerLedger, SOARecord, ReconciliationResult
from datetime import datetime


TOLERANCE = 0.01  # AED tolerance for amount matching


def run_ap_reconciliation(db: Session) -> dict:
    """Reconcile vendor ledger (ERP) against SOA records."""
    erp_records = db.query(VendorLedger).all()
    soa_records = db.query(SOARecord).filter(SOARecord.party_type == "vendor").all()

    erp_map = {r.invoice_no: r for r in erp_records}
    soa_map = {r.invoice_no: r for r in soa_records}

    # Clear previous reconciliation results for AP
    db.query(ReconciliationResult).filter(
        ReconciliationResult.reconciliation_type == "ap"
    ).delete()

    results = []
    all_invoices = set(erp_map.keys()) | set(soa_map.keys())

    matched = unmatched = discrepancies = 0

    for inv_no in all_invoices:
        erp = erp_map.get(inv_no)
        soa = soa_map.get(inv_no)

        erp_amt = erp.amount if erp else None
        soa_amt = soa.amount if soa else None
        party_name = (erp.vendor_name if erp else soa.party_name) or ""
        diff = None

        if erp and soa:
            diff = round(erp_amt - soa_amt, 2)
            status = "matched" if abs(diff) <= TOLERANCE else "discrepancy"
        elif erp and not soa:
            status = "unmatched"
        else:
            status = "unmatched"

        if status == "matched":
            matched += 1
        elif status == "discrepancy":
            discrepancies += 1
        else:
            unmatched += 1

        rec = ReconciliationResult(
            reconciliation_type="ap",
            party_name=party_name,
            invoice_no=inv_no,
            erp_amount=erp_amt,
            soa_amount=soa_amt,
            difference=diff,
            status=status,
        )
        db.add(rec)
        results.append({
            "party_name": party_name,
            "invoice_no": inv_no,
            "erp_amount": erp_amt,
            "soa_amount": soa_amt,
            "difference": diff,
            "status": status,
        })

    db.commit()
    total = len(results)
    return {
        "total_records": total,
        "matched": matched,
        "unmatched": unmatched,
        "discrepancies": discrepancies,
        "match_rate": round((matched / total * 100) if total else 0, 2),
        "items": results,
    }


def run_ar_reconciliation(db: Session) -> dict:
    """Reconcile customer ledger (ERP) against SOA records."""
    erp_records = db.query(CustomerLedger).all()
    soa_records = db.query(SOARecord).filter(SOARecord.party_type == "customer").all()

    erp_map = {r.invoice_no: r for r in erp_records}
    soa_map = {r.invoice_no: r for r in soa_records}

    db.query(ReconciliationResult).filter(
        ReconciliationResult.reconciliation_type == "ar"
    ).delete()

    results = []
    all_invoices = set(erp_map.keys()) | set(soa_map.keys())

    matched = unmatched = discrepancies = 0

    for inv_no in all_invoices:
        erp = erp_map.get(inv_no)
        soa = soa_map.get(inv_no)

        erp_amt = erp.amount if erp else None
        soa_amt = soa.amount if soa else None
        party_name = (erp.customer_name if erp else soa.party_name) or ""
        diff = None

        if erp and soa:
            diff = round(erp_amt - soa_amt, 2)
            status = "matched" if abs(diff) <= TOLERANCE else "discrepancy"
        else:
            status = "unmatched"

        if status == "matched":
            matched += 1
        elif status == "discrepancy":
            discrepancies += 1
        else:
            unmatched += 1

        rec = ReconciliationResult(
            reconciliation_type="ar",
            party_name=party_name,
            invoice_no=inv_no,
            erp_amount=erp_amt,
            soa_amount=soa_amt,
            difference=diff,
            status=status,
        )
        db.add(rec)
        results.append({
            "party_name": party_name,
            "invoice_no": inv_no,
            "erp_amount": erp_amt,
            "soa_amount": soa_amt,
            "difference": diff,
            "status": status,
        })

    db.commit()
    total = len(results)
    return {
        "total_records": total,
        "matched": matched,
        "unmatched": unmatched,
        "discrepancies": discrepancies,
        "match_rate": round((matched / total * 100) if total else 0, 2),
        "items": results,
    }


def get_reconciliation_results(db: Session, rec_type: str) -> list:
    """Fetch saved reconciliation results."""
    records = db.query(ReconciliationResult).filter(
        ReconciliationResult.reconciliation_type == rec_type
    ).all()
    return [
        {
            "party_name": r.party_name,
            "invoice_no": r.invoice_no,
            "erp_amount": r.erp_amount,
            "soa_amount": r.soa_amount,
            "difference": r.difference,
            "status": r.status,
        }
        for r in records
    ]
