from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class ChatRequest(BaseModel):
    case_id: str
    session_id: str
    question: str
    top_k: Optional[int] = None
    include_knowledge: bool = True


class SourceCitation(BaseModel):
    document_name: str
    evidence_id: Optional[str]
    chunk_id: str
    page_number: Optional[int]
    line_start: Optional[int]
    line_end: Optional[int]
    relevance_score: float
    excerpt: str


class Finding(BaseModel):
    title: str
    severity: str
    description: str
    evidence_reference: Optional[str]


class ChatResponse(BaseModel):
    answer: str
    case_id: str
    session_id: str
    sources: List[SourceCitation]
    findings: List[Finding]
    limitations: List[str]
    created_at: datetime


class ChatHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    sources: List[Any]
    findings: List[Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeUploadResponse(BaseModel):
    document_id: str
    document_name: str
    indexing_status: str
    message: str


class KnowledgeDocOut(BaseModel):
    id: str
    document_name: str
    document_type: Optional[str]
    indexing_status: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}
