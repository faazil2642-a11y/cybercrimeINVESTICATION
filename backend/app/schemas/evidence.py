from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.evidence import ProcessingStatus, IntegrityStatus


class EvidenceOut(BaseModel):
    id: str
    evidence_number: str
    case_id: str
    original_filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    sha256_hash: Optional[str]
    upload_timestamp: datetime
    processing_status: ProcessingStatus
    integrity_status: IntegrityStatus
    chunk_count: int
    uploaded_by: Optional[str]

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: List[EvidenceOut]
    total: int


class HashVerifyResponse(BaseModel):
    evidence_id: str
    original_hash: str
    current_hash: str
    match: bool
    verified_at: datetime


class CustodyRecord(BaseModel):
    id: str
    action: str
    performed_by_name: Optional[str]
    timestamp: datetime
    details: Optional[str]
    record_hash: Optional[str]

    model_config = {"from_attributes": True}


class EvidencePreview(BaseModel):
    evidence_id: str
    filename: str
    preview_text: str
    total_chars: int
