"""
AI Query Router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.ai_service import handle_query
from schemas.schemas import AIQueryRequest

router = APIRouter()

@router.post("/query")
def ai_query(request: AIQueryRequest, db: Session = Depends(get_db)):
    return handle_query(db, request.query)
