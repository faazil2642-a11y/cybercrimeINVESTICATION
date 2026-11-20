import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SAEnum, ForeignKey, Index
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class CollectionType(str, enum.Enum):
    CASE_EVIDENCE = "cybertrace_case_evidence"
    KNOWLEDGE = "cybertrace_knowledge"


class IndexingStatus(str, enum.Enum):
    PENDING = "PENDING"
    INDEXING = "INDEXING"
    INDEXED = "INDEXED"
    FAILED = "FAILED"


class RAGDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(String(36), primary_key=True, default=new_uuid)
    document_name = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=True)
    case_id = Column(String(36), ForeignKey("investigation_cases.id"), nullable=True)
    evidence_id = Column(String(36), ForeignKey("evidence_files.id"), nullable=True)
    collection_type = Column(SAEnum(CollectionType), nullable=False)
    indexing_status = Column(SAEnum(IndexingStatus), default=IndexingStatus.PENDING, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_ragdoc_case_id", "case_id"),
        Index("ix_ragdoc_evidence_id", "evidence_id"),
    )


class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(String(36), primary_key=True, default=new_uuid)
    document_id = Column(String(36), ForeignKey("rag_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    chroma_chunk_id = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_ragchunk_document_id", "document_id"),
    )
