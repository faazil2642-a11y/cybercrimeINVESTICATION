import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class ThreatSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ThreatStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class ThreatDetection(Base):
    __tablename__ = "threat_detections"

    id = Column(String(36), primary_key=True, default=new_uuid)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("investigation_events.id"), nullable=True)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SAEnum(ThreatSeverity), default=ThreatSeverity.MEDIUM, nullable=False)
    confidence = Column(Float, default=0.5, nullable=False)
    detection_source = Column(String(100), nullable=False)  # e.g. "rule_based", "isolation_forest"
    supporting_evidence = Column(Text, nullable=True)  # JSON list of evidence refs
    status = Column(SAEnum(ThreatStatus), default=ThreatStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_threats_case_id", "case_id"),
        Index("ix_threats_severity", "severity"),
    )
