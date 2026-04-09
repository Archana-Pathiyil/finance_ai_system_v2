#!/bin/bash
pip install uvicorn[standard] gunicorn fastapi sqlalchemy pandas openpyxl python-multipart python-dotenv pdfplumber aiofiles
python -m uvicorn main:app --host 0.0.0.0 --port 8000
