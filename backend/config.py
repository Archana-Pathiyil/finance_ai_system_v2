"""
Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# App Settings
APP_NAME = "Finance AI MIS System"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finance_mis.db")

# File Upload
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv", ".pdf"}

# AI Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Optional - falls back to rule-based AI

# Business Rules
AP_PAYMENT_DAYS = int(os.getenv("AP_PAYMENT_DAYS", "45"))  # 45-day payment rule
AR_FOLLOWUP_DAYS = int(os.getenv("AR_FOLLOWUP_DAYS", "30"))  # Flag after 30 days

# Ensure upload dir exists
os.makedirs(UPLOAD_DIR, exist_ok=True)
