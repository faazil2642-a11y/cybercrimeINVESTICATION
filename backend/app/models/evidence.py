import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class ProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class IntegrityStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id = Column(String(36), primary_key=True, default=new_uuid)
    evidence_number = Column(String(50), unique=True, nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    sha256_hash = Column(String(64), nullable=True, index=True)
    storage_path = Column(String(1000), nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    processing_status = Column(SAEnum(ProcessingStatus), default=ProcessingStatus.UPLOADED, nullable=False)
    integrity_status = Column(SAEnum(IntegrityStatus), default=IntegrityStatus.PENDING, nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    chunk_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_evidence_case_id", "case_id"),
        Index("ix_evidence_status", "processing_status"),
    )
