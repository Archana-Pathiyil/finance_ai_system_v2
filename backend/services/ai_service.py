"""
AI Query Service - Rule-based NLP engine for finance queries
Falls back to keyword matching; can be extended with LLM integration.
"""
import re
from datetime import date
from sqlalchemy.orm import Session
from services.ap_service import get_ap_summary, get_payment_due_report, get_vendor_wise_summary
from services.ar_service import get_ar_summary, get_collection_followup, get_ageing_buckets_total


def parse_query(query: str) -> dict:
    """Classify intent from natural language query."""
    q = query.lower().strip()

    # AP intents
    if any(w in q for w in ["total payable", "payables", "ap total", "how much do we owe"]):
        return {"intent": "ap_total"}
    if any(w in q for w in ["payment due", "due this month", "upcoming payment", "pay this"]):
        return {"intent": "payment_due"}
    if any(w in q for w in ["overdue payment", "late payment", "ap overdue"]):
        return {"intent": "ap_overdue"}
    if any(w in q for w in ["vendor", "supplier", "top vendor"]):
        return {"intent": "vendor_summary"}

    # AR intents
    if any(w in q for w in ["total receivable", "receivables", "ar total", "how much owed to us"]):
        return {"intent": "ar_total"}
    if any(w in q for w in ["overdue customer", "overdue receivable", "follow up", "collection"]):
        return {"intent": "collection_followup"}
    if any(w in q for w in ["ageing", "aging", "bucket"]):
        return {"intent": "ar_ageing"}
    if any(w in q for w in ["customer", "top customer"]):
        return {"intent": "customer_summary"}

    # General
    if any(w in q for w in ["cash flow", "cashflow", "forecast"]):
        return {"intent": "cashflow"}
    if any(w in q for w in ["summary", "overview", "dashboard", "kpi"]):
        return {"intent": "summary"}

    return {"intent": "unknown"}


def handle_query(db: Session, query: str) -> dict:
    """Route query to appropriate data handler."""
    parsed = parse_query(query)
    intent = parsed["intent"]

    if intent == "ap_total":
        data = get_ap_summary(db)
        return {
            "query": query,
            "answer": f"Total Accounts Payable outstanding is AED {data['total_outstanding']:,.2f} across {data['total_invoices']} invoices from {data['total_vendors']} vendors.",
            "data": data,
            "chart_type": None,
        }

    elif intent == "payment_due":
        items = get_payment_due_report(db)
        due = [i for i in items if i["status"] in ("due", "overdue")]
        total = sum(i["outstanding"] for i in due)
        return {
            "query": query,
            "answer": f"There are {len(due)} invoices due or overdue, totalling AED {total:,.2f}.",
            "data": {"items": due[:10], "total": total},
            "chart_type": "bar",
        }

    elif intent == "ap_overdue":
        data = get_ap_summary(db)
        return {
            "query": query,
            "answer": f"Overdue AP amount is AED {data['overdue_amount']:,.2f}.",
            "data": {"overdue_amount": data["overdue_amount"]},
            "chart_type": None,
        }

    elif intent == "vendor_summary":
        vendors = get_vendor_wise_summary(db)[:5]
        return {
            "query": query,
            "answer": f"Top {len(vendors)} vendors by outstanding amount.",
            "data": {"vendors": vendors},
            "chart_type": "bar",
        }

    elif intent == "ar_total":
        data = get_ar_summary(db)
        return {
            "query": query,
            "answer": f"Total Accounts Receivable outstanding is AED {data['total_outstanding']:,.2f} across {data['total_invoices']} invoices from {data['total_customers']} customers. Overdue: {data['overdue_percentage']}%.",
            "data": data,
            "chart_type": None,
        }

    elif intent == "collection_followup":
        items = get_collection_followup(db)
        total = sum(i["outstanding"] for i in items)
        return {
            "query": query,
            "answer": f"{len(items)} invoices require collection follow-up. Total outstanding: AED {total:,.2f}.",
            "data": {"items": items[:10], "total": total},
            "chart_type": "bar",
        }

    elif intent == "ar_ageing":
        buckets = get_ageing_buckets_total(db)
        return {
            "query": query,
            "answer": "AR Ageing breakdown by bucket.",
            "data": {"buckets": buckets},
            "chart_type": "pie",
        }

    elif intent == "summary":
        ap = get_ap_summary(db)
        ar = get_ar_summary(db)
        return {
            "query": query,
            "answer": (
                f"Finance Summary: Payables AED {ap['total_outstanding']:,.2f} | "
                f"Receivables AED {ar['total_outstanding']:,.2f} | "
                f"Overdue AR: {ar['overdue_percentage']}%"
            ),
            "data": {"ap": ap, "ar": ar},
            "chart_type": None,
        }

    else:
        return {
            "query": query,
            "answer": "I couldn't understand that query. Try asking about: total payables, payment due, overdue customers, AR ageing, or a summary.",
            "data": None,
            "chart_type": None,
        }
