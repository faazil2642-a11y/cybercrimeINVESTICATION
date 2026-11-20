from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class LogAnalysisRequest(BaseModel):
    case_id: Optional[str] = None
    log_format: Optional[str] = "auto"  # auto, syslog, windows_csv, json, generic


class LogFinding(BaseModel):
    finding_id: str
    category: str
    severity: str
    description: str
    source_ip: Optional[str]
    username: Optional[str]
    timestamp: Optional[datetime]
    event_count: int
    evidence_lines: List[str]
    detection_method: str


class LogAnalysisResponse(BaseModel):
    file_name: str
    total_lines: int
    parsed_events: int
    findings: List[LogFinding]
    summary: str
    events_stored: int


class IPAnalysisRequest(BaseModel):
    ip_address: str
    case_id: Optional[str] = None


class IPAnalysisResponse(BaseModel):
    ip_address: str
    is_valid: bool
    ip_version: Optional[int]
    total_events: int
    associated_users: List[str]
    associated_evidence: List[str]
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    related_cases: List[str]
    event_summary: List[dict]
    note: str


class TimelineEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    description: str
    source_ip: Optional[str]
    username: Optional[str]
    severity: str
    source_reference: Optional[str]
    evidence_id: Optional[str]


class TimelineResponse(BaseModel):
    case_id: str
    events: List[TimelineEvent]
    total: int


class ThreatOut(BaseModel):
    id: str
    case_id: str
    category: str
    description: str
    severity: str
    confidence: float
    detection_source: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportRequest(BaseModel):
    case_id: str
    report_title: Optional[str] = None
    include_chat_history: bool = True


class ReportOut(BaseModel):
    id: str
    report_number: str
    case_id: str
    report_title: str
    generated_by_name: Optional[str]
    generated_at: datetime
    status: str

    model_config = {"from_attributes": True}
