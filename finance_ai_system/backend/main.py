"""
Finance AI System - Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from database import engine, Base
from routers import upload, ap, ar, reconciliation, reports, ai_query, dashboard, mail


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Finance AI MIS System",
    description="AI-powered Accounts Payable & Receivable Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(ap.router, prefix="/api/ap", tags=["Accounts Payable"])
app.include_router(ar.router, prefix="/api/ar", tags=["Accounts Receivable"])
app.include_router(reconciliation.router, prefix="/api/reconciliation", tags=["Reconciliation"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(ai_query.router, prefix="/api/ai", tags=["AI Query"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(mail.router, prefix="/api/mail", tags=["Mail"])


# Serve frontend
@app.get("/app", include_in_schema=False)
def frontend():
    return FileResponse("index.html")


@app.get("/")
def root():
    return {"message": "Finance AI MIS System is running", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
