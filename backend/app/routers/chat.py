from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from .. import models, database
from .auth import get_current_user
from ..services import chat_service
import json

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    repository_id: int
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]

class SessionListResponse(BaseModel):
    sessions: List[dict]

@router.post("/send", response_model=ChatResponse)
async def send_message(
    req: ChatRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    repo = db.query(models.Repository).filter(
        models.Repository.id == req.repository_id,
        models.Repository.user_id == current_user.id,
    ).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if req.session_id:
        existing = db.query(models.ChatSession).filter(
            models.ChatSession.id == req.session_id,
            models.ChatSession.user_id == current_user.id,
        ).first()
        if not existing:
            req.session_id = None

    if not req.session_id:
        evidence = None
        jobs = db.query(models.AnalysisJob).filter(
            models.AnalysisJob.repository_id == repo.id,
            models.AnalysisJob.status == models.JobStatus.DONE,
        ).order_by(models.AnalysisJob.id.desc()).all()
        for job in jobs:
            if job.evidence_json:
                try:
                    evidence = json.loads(job.evidence_json)
                except (json.JSONDecodeError, TypeError):
                    evidence = None
                break

        req.session_id = chat_service.create_chat_session(
            db=db,
            user_id=current_user.id,
            repository_id=repo.id,
            repo_name=repo.full_name,
            evidence=evidence,
        )

    reply = await chat_service.get_chat_reply(
        db=db,
        session_id=req.session_id,
        user_message=req.message,
        repo_name=repo.full_name,
    )

    return ChatResponse(session_id=req.session_id, reply=reply)

@router.get("/sessions", response_model=SessionListResponse)
def list_sessions(
    repository_id: int | None = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    query = db.query(models.ChatSession).filter(models.ChatSession.user_id == current_user.id)
    if repository_id:
        query = query.filter(models.ChatSession.repository_id == repository_id)
    sessions = query.order_by(models.ChatSession.created_at.desc()).all()

    result = []
    for s in sessions:
        msg_count = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == s.id).count()
        result.append({
            "id": s.id,
            "repo_name": s.repo_name,
            "repository_id": s.repository_id,
            "message_count": msg_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return SessionListResponse(sessions=result)

@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
def get_history(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = chat_service.get_session_history(db=db, session_id=session_id)
    return ChatHistoryResponse(session_id=session_id, messages=messages)

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db),
):
    session = db.query(models.ChatSession).filter(
        models.ChatSession.id == session_id,
        models.ChatSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    chat_service.delete_session(db=db, session_id=session_id)
    return {"detail": "Session deleted"}
