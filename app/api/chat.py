from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.claude_service import generate_recommendation
from app.services.vector_store import search_cafes


class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    recommendation: str
    cafes_found: int
    session_id: str


router = APIRouter(prefix="/chat")


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        cafes = search_cafes(db, request.query, limit=3)
        recommendation = generate_recommendation(
            user_query=request.query,
            retrieved_cafes=cafes,
        )

        return ChatResponse(
            recommendation=recommendation,
            cafes_found=len(cafes),
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation: {exc}",
        ) from exc
