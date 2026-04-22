"""
File Parser Utility - Handles Excel, CSV, and PDF parsing
"""
import pandas as pd
import io
from typing import Tuple, List
from fastapi import UploadFile, HTTPException
from config import ALLOWED_EXTENSIONS
import os


VENDOR_LEDGER_COLUMNS = {
    "required": ["Invoice No", "Invoice Date", "Amount", "Vendor Name"],
    "optional": ["Vendor Code", "Due Date", "Paid Amount", "Outstanding", "Currency", "Description"],
}

CUSTOMER_LEDGER_COLUMNS = {
    "required": ["Invoice No", "Invoice Date", "Amount", "Customer Name"],
    "optional": ["Customer Code", "Due Date", "Received Amount", "Outstanding", "Currency", "Description"],
}

SOA_COLUMNS = {
    "required": ["Invoice No", "Amount", "Party Name"],
    "optional": ["Invoice Date", "Currency"],
}


def validate_extension(filename: str) -> str:
    """Validate file extension and return it."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {ALLOWED_EXTENSIONS}",
        )
    return ext


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: strip whitespace, title case."""
    df.columns = [str(c).strip().title() for c in df.columns]
    return df


def parse_excel_or_csv(content: bytes, filename: str) -> pd.DataFrame:
    """Parse Excel or CSV file into a DataFrame. Auto-detects header row."""
    ext = os.path.splitext(filename)[1].lower()
    try:
        if ext in (".xlsx", ".xls"):
            # Try row 0 first, if required cols not found try rows 1-6
            for header_row in range(7):
                try:
                    df = pd.read_excel(io.BytesIO(content), header=header_row)
                    df_norm = normalize_columns(df)
                    # Accept if at least 3 real columns found (not Unnamed)
                    real_cols = [c for c in df_norm.columns if not str(c).startswith("Unnamed")]
                    if len(real_cols) >= 3:
                        return df_norm
                except Exception:
                    continue
            # Fallback to row 0
            df = pd.read_excel(io.BytesIO(content), header=0)
        elif ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
        return normalize_columns(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")


def validate_columns(df: pd.DataFrame, required_cols: List[str]) -> Tuple[bool, List[str]]:
    """Check that all required columns exist in the DataFrame."""
    missing = [col for col in required_cols if col not in df.columns]
    return len(missing) == 0, missing


def parse_vendor_ledger(content: bytes, filename: str) -> pd.DataFrame:
    """Parse and validate vendor ledger file."""
    df = parse_excel_or_csv(content, filename)
    valid, missing = validate_columns(df, VENDOR_LEDGER_COLUMNS["required"])
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=f"Vendor Ledger missing required columns: {missing}",
        )
    df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Paid Amount"] = pd.to_numeric(df.get("Paid Amount", 0), errors="coerce").fillna(0)
    df["Outstanding"] = df["Amount"] - df["Paid Amount"]
    return df


def parse_customer_ledger(content: bytes, filename: str) -> pd.DataFrame:
    """Parse and validate customer ledger file."""
    df = parse_excel_or_csv(content, filename)
    valid, missing = validate_columns(df, CUSTOMER_LEDGER_COLUMNS["required"])
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=f"Customer Ledger missing required columns: {missing}",
        )
    df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    df["Received Amount"] = pd.to_numeric(df.get("Received Amount", 0), errors="coerce").fillna(0)
    df["Outstanding"] = df["Amount"] - df["Received Amount"]
    return df


def parse_soa(content: bytes, filename: str) -> pd.DataFrame:
    """Parse and validate SOA file."""
    df = parse_excel_or_csv(content, filename)
    valid, missing = validate_columns(df, SOA_COLUMNS["required"])
    if not valid:
        raise HTTPException(
            status_code=400,
            detail=f"SOA missing required columns: {missing}",
        )
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df


def get_preview(df: pd.DataFrame, rows: int = 10) -> dict:
    """Return a JSON-serializable preview of the DataFrame."""
    preview_df = df.head(rows).copy()
    # Convert dates to strings for JSON serialization
    for col in preview_df.select_dtypes(include=["datetime64[ns]"]).columns:
        preview_df[col] = preview_df[col].dt.strftime("%Y-%m-%d")
    return {
        "columns": list(preview_df.columns),
        "rows": preview_df.fillna("").to_dict(orient="records"),
        "total_rows": len(df),
    }
