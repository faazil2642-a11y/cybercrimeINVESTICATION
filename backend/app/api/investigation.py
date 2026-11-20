import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import InvestigationCase
from app.models.chat import ChatHistory
from app.schemas.rag import ChatRequest, ChatResponse, ChatHistoryItem
from app.core.security import get_current_user, require_roles
from app.rag import retriever
from app.services.audit_service import log_audit

router = APIRouter(prefix="/investigation", tags=["AI Investigation Assistant"])


@router.post("/chat", response_model=ChatResponse)
def investigation_chat(
    payload: ChatRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == payload.case_id).first()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found.")

    # Retrieve prior chat context for session
    prior_chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.case_id == payload.case_id, ChatHistory.session_id == payload.session_id)
        .order_by(ChatHistory.created_at.asc())
        .limit(4)
        .all()
    )
    history_str = ""
    for pc in prior_chats:
        history_str += f"Investigator: {pc.question}\nCyberTrace: {pc.answer}\n"

    # Execute RAG Pipeline with strictly isolated case_id filter
    rag_result = retriever.run_rag_pipeline(
        question=payload.question,
        case_id=payload.case_id,
        case_number=case.case_number,
        session_id=payload.session_id,
        top_k=payload.top_k,
        include_knowledge=payload.include_knowledge,
        chat_history=history_str
    )

    # Persist in Chat History
    chat_entry = ChatHistory(
        user_id=current_user.id,
        case_id=payload.case_id,
        session_id=payload.session_id,
        question=payload.question,
        answer=rag_result["answer"],
        sources_json=json.dumps(rag_result["sources"]),
        findings_json=json.dumps(rag_result["findings"]),
        created_at=datetime.now(timezone.utc)
    )
    db.add(chat_entry)
    db.commit()

    log_audit(
        db,
        action="AI_INVESTIGATION_QUERY",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="CASE",
        resource_id=payload.case_id,
        details=f"Query: {payload.question[:80]}"
    )

    return rag_result


@router.get("/history/{case_id}", response_model=List[ChatHistoryItem])
def get_case_chat_history(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.case_id == case_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
    res = []
    for r in records:
        sources = json.loads(r.sources_json) if r.sources_json else []
        findings = json.loads(r.findings_json) if r.findings_json else []
        res.append(
            ChatHistoryItem(
                id=r.id,
                question=r.question,
                answer=r.answer,
                sources=sources,
                findings=findings,
                created_at=r.created_at
            )
        )
    return res
