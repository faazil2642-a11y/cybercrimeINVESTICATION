import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    id = Column(String(36), primary_key=True, default=new_uuid)
    evidence_id = Column(String(36), ForeignKey("evidence_files.id"), nullable=False)
    action = Column(String(200), nullable=False)
    performed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    performed_by_name = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    details = Column(Text, nullable=True)
    previous_record_hash = Column(String(64), nullable=True)
    record_hash = Column(String(64), nullable=True)

    __table_args__ = (
        Index("ix_custody_evidence_id", "evidence_id"),
    )
