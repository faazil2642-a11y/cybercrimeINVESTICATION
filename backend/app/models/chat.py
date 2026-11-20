import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=True)
    session_id = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources_json = Column(Text, nullable=True)   # JSON-encoded source citations
    findings_json = Column(Text, nullable=True)  # JSON-encoded findings
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_chat_case_id", "case_id"),
        Index("ix_chat_session_id", "session_id"),
        Index("ix_chat_user_id", "user_id"),
    )
