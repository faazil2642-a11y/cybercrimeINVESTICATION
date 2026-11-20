import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class CaseStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class CasePriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseCategory(str, enum.Enum):
    AUTH_EXPLOIT = "AUTH_EXPLOIT"
    FIN_FRAUD = "FIN_FRAUD"
    INTEL = "INTEL"
    MALWARE = "MALWARE"
    PHISHING = "PHISHING"
    DATA_EXFIL = "DATA_EXFIL"
    NETWORK_INTRUSION = "NETWORK_INTRUSION"
    INSIDER_THREAT = "INSIDER_THREAT"
    OTHER = "OTHER"


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(String(36), primary_key=True, default=new_uuid)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(CaseCategory), default=CaseCategory.OTHER, nullable=False)
    priority = Column(SAEnum(CasePriority), default=CasePriority.MEDIUM, nullable=False)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.ACTIVE, nullable=False)
    investigator_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("ix_cases_status", "status"),
        Index("ix_cases_priority", "priority"),
        Index("ix_cases_investigator", "investigator_id"),
    )
