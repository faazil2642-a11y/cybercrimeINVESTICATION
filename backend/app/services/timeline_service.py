from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.models.event import InvestigationEvent, EventSeverity


def get_case_timeline(
    db: Session,
    case_id: str,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ascending: bool = True
) -> List[InvestigationEvent]:
    query = db.query(InvestigationEvent).filter(InvestigationEvent.case_id == case_id)

    if event_type:
        query = query.filter(InvestigationEvent.event_type == event_type)

    if severity:
        try:
            sev_enum = EventSeverity(severity.upper())
            query = query.filter(InvestigationEvent.severity == sev_enum)
        except ValueError:
            pass

    if start_date:
        query = query.filter(InvestigationEvent.timestamp >= start_date)

    if end_date:
        query = query.filter(InvestigationEvent.timestamp <= end_date)

    if ascending:
        query = query.order_by(asc(InvestigationEvent.timestamp))
    else:
        query = query.order_by(desc(InvestigationEvent.timestamp))

    return query.all()


def record_investigation_event(
    db: Session,
    case_id: str,
    event_type: str,
    description: str,
    timestamp: datetime,
    evidence_id: Optional[str] = None,
    source_ip: Optional[str] = None,
    destination_ip: Optional[str] = None,
    username: Optional[str] = None,
    hostname: Optional[str] = None,
    severity: EventSeverity = EventSeverity.INFO,
    source_reference: Optional[str] = None,
    raw_line: Optional[str] = None
) -> InvestigationEvent:
    event = InvestigationEvent(
        case_id=case_id,
        evidence_id=evidence_id,
        timestamp=timestamp,
        event_type=event_type,
        description=description,
        source_ip=source_ip,
        destination_ip=destination_ip,
        username=username,
        hostname=hostname,
        severity=severity,
        source_reference=source_reference,
        raw_line=raw_line
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
