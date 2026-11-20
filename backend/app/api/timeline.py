from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.schemas.investigation import TimelineResponse, TimelineEvent
from app.core.security import get_current_user
from app.services.timeline_service import get_case_timeline

router = APIRouter(prefix="/timeline", tags=["Incident Timeline"])


@router.get("/{case_id}", response_model=TimelineResponse)
def get_timeline(
    case_id: str,
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    events = get_case_timeline(
        db=db,
        case_id=case_id,
        event_type=event_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        ascending=True
    )

    timeline_events = [
        TimelineEvent(
            id=ev.id,
            timestamp=ev.timestamp,
            event_type=ev.event_type,
            description=ev.description,
            source_ip=ev.source_ip,
            username=ev.username,
            severity=ev.severity.value,
            source_reference=ev.source_reference,
            evidence_id=ev.evidence_id
        )
        for ev in events
    ]

    return TimelineResponse(
        case_id=case_id,
        events=timeline_events,
        total=len(timeline_events)
    )
