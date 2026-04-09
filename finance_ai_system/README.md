# 💹 Finance AI MIS System

**AI-powered Accounts Payable & Receivable Management Platform**

A production-grade full-stack system with FastAPI backend, React frontend, and intelligent finance automation.

---

## 🗂 Project Structure

```
finance_ai_system/
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── config.py                       # Environment configuration
│   ├── database.py                     # SQLAlchemy + SQLite setup
│   ├── models/
│   │   └── models.py                   # DB table definitions
│   ├── schemas/
│   │   └── schemas.py                  # Pydantic request/response models
│   ├── routers/
│   │   ├── upload.py                   # File upload endpoints
│   │   ├── ap.py                       # Accounts Payable API
│   │   ├── ar.py                       # Accounts Receivable API
│   │   ├── reconciliation.py           # Reconciliation API
│   │   ├── reports.py                  # Excel report downloads
│   │   ├── ai_query.py                 # AI NLP query endpoint
│   │   └── dashboard.py               # Dashboard KPI aggregation
│   ├── services/
│   │   ├── ingestion_service.py        # File parsing & DB storage
│   │   ├── ap_service.py               # AP logic (45-day rule, summaries)
│   │   ├── ar_service.py               # AR logic (ageing, collection)
│   │   ├── reconciliation_service.py   # ERP vs SOA matching
│   │   ├── report_service.py           # Excel generation (openpyxl)
│   │   └── ai_service.py               # Rule-based NLP query engine
│   ├── utils/
│   │   ├── file_parser.py              # Excel/CSV parsing & validation
│   │   └── date_utils.py              # Due date & ageing calculations
│   └── requirements.txt
├── frontend/
│   └── index.html                      # Complete React SPA (no build step)
├── data_samples/
│   ├── generate_samples.py             # Generate test Excel files
│   ├── vendor_ledger.xlsx              # (generated)
│   ├── customer_ledger.xlsx            # (generated)
│   ├── soa_vendor.xlsx                 # (generated)
│   └── soa_customer.xlsx               # (generated)
└── README.md
```

---

## ⚡ Quick Start

### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API will be live at: **http://localhost:8000**  
Swagger docs: **http://localhost:8000/docs**

### 3. Open the Frontend

Simply open `frontend/index.html` in your browser.  
*(No npm install, no build step — it runs directly)*

### 4. Generate Sample Data (Optional)

```bash
cd data_samples
pip install pandas openpyxl
python generate_samples.py
```

Then upload via **Upload Center** in the UI.

---

## 🔌 API Endpoints

### Upload
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload/vendor-ledger` | Upload vendor ledger Excel |
| POST | `/api/upload/customer-ledger` | Upload customer ledger Excel |
| POST | `/api/upload/soa?party_type=vendor` | Upload SOA (vendor/customer) |
| POST | `/api/upload/preview/vendor-ledger` | Preview without saving |
| GET  | `/api/upload/history` | Upload history log |

### Accounts Payable
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ap/summary` | AP KPIs |
| GET | `/api/ap/payment-due` | 45-day payment schedule |
| GET | `/api/ap/vendors` | Vendor-wise outstanding |
| GET | `/api/ap/invoices?vendor=<name>` | All invoices (filtered) |
| GET | `/api/ap/cash-outflow-trend` | Monthly chart data |

### Accounts Receivable
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ar/summary` | AR KPIs |
| GET | `/api/ar/ageing` | Customer ageing table |
| GET | `/api/ar/ageing-buckets` | Aggregate bucket data |
| GET | `/api/ar/collection-followup` | Invoices >30 days overdue |
| GET | `/api/ar/customers` | Customer-wise summary |

### Reconciliation
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/reconciliation/run/ap` | Run AP reconciliation |
| POST | `/api/reconciliation/run/ar` | Run AR reconciliation |
| GET  | `/api/reconciliation/results/ap` | Saved AP results |
| GET  | `/api/reconciliation/results/ar` | Saved AR results |

### Reports (Excel Download)
| Method | Endpoint | Filename |
|--------|----------|----------|
| GET | `/api/reports/ap-outstanding` | ap_outstanding.xlsx |
| GET | `/api/reports/payment-due` | payment_due.xlsx |
| GET | `/api/reports/ar-ageing` | ar_ageing.xlsx |
| GET | `/api/reports/collection-followup` | collection_followup.xlsx |
| GET | `/api/reports/reconciliation/ap` | reconciliation_ap.xlsx |
| GET | `/api/reports/reconciliation/ar` | reconciliation_ar.xlsx |

### AI Query
| Method | Endpoint | Body |
|--------|----------|------|
| POST | `/api/ai/query` | `{"query": "Total payable this month"}` |

**Supported queries:**
- "Total payable / receivable"
- "Payment due this month"
- "Top overdue customers"
- "AR ageing breakdown"
- "Finance summary overview"
- "Upcoming payments due"
- "Vendor / customer summary"

---

## 📊 UI Pages

| Page | Description |
|------|-------------|
| 🏠 Dashboard | KPI cards, cash outflow chart, ageing pie chart, top vendors |
| 📤 Accounts Payable | Vendor summary, payment due schedule, all invoices |
| 📥 Accounts Receivable | Customer ageing, bucket analysis, collection follow-up |
| ⚖️ Reconciliation | Run ERP vs SOA matching, filter by status, export |
| 📊 Reports | One-click Excel downloads for all reports |
| ⬆ Upload Center | Drag-drop upload, file preview, upload history |
| 🤖 AI Assistant | Natural language finance queries with charts |

---

## 📋 Required Excel Column Names

### Vendor Ledger
| Column | Required |
|--------|----------|
| Vendor Name | ✅ |
| Invoice No | ✅ |
| Invoice Date | ✅ |
| Amount | ✅ |
| Vendor Code | Optional |
| Due Date | Optional |
| Paid Amount | Optional |
| Currency | Optional (default: AED) |

### Customer Ledger
| Column | Required |
|--------|----------|
| Customer Name | ✅ |
| Invoice No | ✅ |
| Invoice Date | ✅ |
| Amount | ✅ |
| Customer Code | Optional |
| Due Date | Optional |
| Received Amount | Optional |
| Currency | Optional (default: AED) |

### SOA
| Column | Required |
|--------|----------|
| Party Name | ✅ |
| Invoice No | ✅ |
| Amount | ✅ |
| Invoice Date | Optional |
| Currency | Optional |

---

## ⚙️ Environment Variables (.env)

```env
DATABASE_URL=sqlite:///./finance_mis.db
DEBUG=true
AP_PAYMENT_DAYS=45
AR_FOLLOWUP_DAYS=30
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=50
```

---

## 🔮 Extending the System

### Add LLM-powered AI queries
In `services/ai_service.py`, replace the rule-based engine with an Anthropic/OpenAI API call:
```python
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### Switch to PostgreSQL
Update `.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/finance_mis
```

### Add JWT Authentication
Install `python-jose` and `passlib`, add auth middleware to `main.py`.

### ERP Integration (SAP)
Replace mock data ingestion in `services/ingestion_service.py` with SAP RFC/REST calls.

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 + FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (swap to PostgreSQL) |
| Data Processing | Pandas |
| Excel Generation | openpyxl |
| Frontend | React 18 (CDN, no build) |
| Charts | Recharts |
| Fonts | DM Sans + DM Mono |

---

**Built for finance teams managing AP/AR at scale.**
