import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.threat import ThreatDetection, ThreatSeverity, ThreatStatus
from app.models.event import InvestigationEvent


def record_threat(
    db: Session,
    case_id: str,
    category: str,
    description: str,
    severity: ThreatSeverity = ThreatSeverity.MEDIUM,
    confidence: float = 0.85,
    detection_source: str = "deterministic_rules",
    event_id: Optional[str] = None,
    supporting_evidence: Optional[List[str]] = None,
    status: ThreatStatus = ThreatStatus.OPEN
) -> ThreatDetection:
    detection = ThreatDetection(
        case_id=case_id,
        event_id=event_id,
        category=category,
        description=description,
        severity=severity,
        confidence=confidence,
        detection_source=detection_source,
        supporting_evidence=json.dumps(supporting_evidence) if supporting_evidence else None,
        status=status
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def get_case_threats(
    db: Session,
    case_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None
) -> List[ThreatDetection]:
    query = db.query(ThreatDetection)
    if case_id:
        query = query.filter(ThreatDetection.case_id == case_id)
    if severity:
        try:
            sev_enum = ThreatSeverity(severity.upper())
            query = query.filter(ThreatDetection.severity == sev_enum)
        except ValueError:
            pass
    if status:
        try:
            status_enum = ThreatStatus(status.upper())
            query = query.filter(ThreatDetection.status == status_enum)
        except ValueError:
            pass
    return query.order_by(desc(ThreatDetection.created_at)).all()


def update_threat_status(
    db: Session,
    threat_id: str,
    status: ThreatStatus
) -> Optional[ThreatDetection]:
    threat = db.query(ThreatDetection).filter(ThreatDetection.id == threat_id).first()
    if not threat:
        return None
    threat.status = status
    db.commit()
    db.refresh(threat)
    return threat
