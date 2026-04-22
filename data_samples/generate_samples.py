"""
Generate Sample Excel Templates for testing the Finance AI System.
Run: python generate_samples.py
"""
import pandas as pd
from datetime import date, timedelta
import random
import os

random.seed(42)
os.makedirs("data_samples", exist_ok=True)

TODAY = date.today()

def rand_date(days_back=120):
    return TODAY - timedelta(days=random.randint(0, days_back))

def rand_amount(lo=5000, hi=250000):
    return round(random.uniform(lo, hi), 2)

# ── Vendor Ledger ─────────────────────────────────────────────────
vendors = [
    ("V001", "Al Futtaim Trading LLC"),
    ("V002", "Emirates Steel Industries"),
    ("V003", "Dubai Contracting Co"),
    ("V004", "Galadari Brothers Group"),
    ("V005", "Nakheel Properties"),
    ("V006", "Emaar Facilities Mgmt"),
    ("V007", "DEWA Supply Corp"),
    ("V008", "Abu Dhabi Distribution"),
]

vendor_rows = []
for code, name in vendors:
    for _ in range(random.randint(3, 8)):
        inv_date = rand_date(120)
        amount = rand_amount()
        paid = round(random.uniform(0, amount * 0.8), 2)
        vendor_rows.append({
            "Vendor Code": code,
            "Vendor Name": name,
            "Invoice No": f"INV-{random.randint(10000, 99999)}",
            "Invoice Date": inv_date.strftime("%Y-%m-%d"),
            "Due Date": (inv_date + timedelta(days=45)).strftime("%Y-%m-%d"),
            "Amount": amount,
            "Paid Amount": paid,
            "Outstanding": round(amount - paid, 2),
            "Currency": "AED",
            "Description": "Goods/Services supplied",
        })

vendor_df = pd.DataFrame(vendor_rows)
vendor_df.to_excel("data_samples/vendor_ledger.xlsx", index=False)
print(f"✅ vendor_ledger.xlsx — {len(vendor_df)} rows")

# ── Customer Ledger ───────────────────────────────────────────────
customers = [
    ("C001", "Majid Al Futtaim Retail"),
    ("C002", "Lulu Hypermarket LLC"),
    ("C003", "Carrefour UAE"),
    ("C004", "Spinneys Distribution"),
    ("C005", "Union Coop Society"),
    ("C006", "Abu Dhabi Co-Op"),
    ("C007", "Sharjah Co-Op"),
    ("C008", "Choithrams Supermarkets"),
    ("C009", "Waitrose UAE"),
]

customer_rows = []
for code, name in customers:
    for _ in range(random.randint(3, 9)):
        inv_date = rand_date(150)
        amount = rand_amount()
        received = round(random.uniform(0, amount * 0.7), 2)
        customer_rows.append({
            "Customer Code": code,
            "Customer Name": name,
            "Invoice No": f"SI-{random.randint(10000, 99999)}",
            "Invoice Date": inv_date.strftime("%Y-%m-%d"),
            "Due Date": (inv_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            "Amount": amount,
            "Received Amount": received,
            "Outstanding": round(amount - received, 2),
            "Currency": "AED",
            "Description": "Sales invoice",
        })

customer_df = pd.DataFrame(customer_rows)
customer_df.to_excel("data_samples/customer_ledger.xlsx", index=False)
print(f"✅ customer_ledger.xlsx — {len(customer_df)} rows")

# ── SOA — Vendor (partial, some mismatches for demo) ──────────────
soa_vendor_rows = []
for _, row in vendor_df.sample(frac=0.75, random_state=1).iterrows():
    # Occasionally introduce a small discrepancy
    soa_amount = row["Amount"] if random.random() > 0.15 else round(row["Amount"] * random.uniform(0.95, 1.05), 2)
    vendor_name = vendors[[v[0] for v in vendors].index(row["Vendor Code"])][1]
    soa_vendor_rows.append({
        "Party Name": vendor_name,
        "Invoice No": row["Invoice No"],
        "Invoice Date": row["Invoice Date"],
        "Amount": soa_amount,
        "Currency": "AED",
    })

soa_vendor_df = pd.DataFrame(soa_vendor_rows)
soa_vendor_df.to_excel("data_samples/soa_vendor.xlsx", index=False)
print(f"✅ soa_vendor.xlsx — {len(soa_vendor_df)} rows")

# ── SOA — Customer ────────────────────────────────────────────────
soa_customer_rows = []
for _, row in customer_df.sample(frac=0.7, random_state=2).iterrows():
    soa_amount = row["Amount"] if random.random() > 0.12 else round(row["Amount"] * random.uniform(0.96, 1.04), 2)
    customer_name = customers[[c[0] for c in customers].index(row["Customer Code"])][1]
    soa_customer_rows.append({
        "Party Name": customer_name,
        "Invoice No": row["Invoice No"],
        "Invoice Date": row["Invoice Date"],
        "Amount": soa_amount,
        "Currency": "AED",
    })

soa_customer_df = pd.DataFrame(soa_customer_rows)
soa_customer_df.to_excel("data_samples/soa_customer.xlsx", index=False)
print(f"✅ soa_customer.xlsx — {len(soa_customer_df)} rows")

print("\n🎉 All sample files generated in ./data_samples/")
print("   Upload them via the Upload Center in the UI.")
