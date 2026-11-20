import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class ReportStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id = Column(String(36), primary_key=True, default=new_uuid)
    report_number = Column(String(50), unique=True, nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    report_title = Column(String(500), nullable=False)
    report_path = Column(String(1000), nullable=True)
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    generated_by_name = Column(String(255), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(SAEnum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)

    __table_args__ = (
        Index("ix_reports_case_id", "case_id"),
    )
