import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class EventSeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationEvent(Base):
    __tablename__ = "investigation_events"

    id = Column(String(36), primary_key=True, default=new_uuid)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    evidence_id = Column(String(36), ForeignKey("evidence_files.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    username = Column(String(255), nullable=True)
    hostname = Column(String(255), nullable=True)
    severity = Column(SAEnum(EventSeverity), default=EventSeverity.INFO, nullable=False)
    source_reference = Column(String(500), nullable=True)
    raw_line = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_events_case_id", "case_id"),
        Index("ix_events_source_ip", "source_ip"),
    )
