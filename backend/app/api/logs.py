from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User, UserRole
from app.models.event import InvestigationEvent, EventSeverity
from app.models.threat import ThreatDetection, ThreatSeverity, ThreatStatus
from app.schemas.investigation import LogAnalysisResponse, LogFinding
from app.core.security import get_current_user, require_roles
from app.services.log_analyzer import parse_log_file, detect_threats
from app.services.audit_service import log_audit

router = APIRouter(prefix="/logs", tags=["Log Analyzer"])


@router.post("/analyze", response_model=LogAnalysisResponse)
async def analyze_log_file(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    log_format: Optional[str] = Form("auto"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    content_bytes = await file.read()
    try:
        content_text = content_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read text log: {e}")

    lines = content_text.splitlines()
    events = parse_log_file(content_text, log_format=log_format or "auto")
    findings_raw = detect_threats(events)

    stored_count = 0
    # If case_id is provided, store structured events and threats into database
    if case_id:
        for ev in events:
            # Store significant events
            if ev.get("is_failed") or ev.get("is_sudo") or ev.get("is_success"):
                sev = EventSeverity.HIGH if ev.get("is_sudo") else (EventSeverity.MEDIUM if ev.get("is_failed") else EventSeverity.INFO)
                db_event = InvestigationEvent(
                    case_id=case_id,
                    timestamp=ev.get("timestamp") or datetime.now(timezone.utc),
                    event_type="AUTH_LOG_EVENT",
                    description=ev.get("message", "")[:400],
                    source_ip=ev.get("source_ip"),
                    username=ev.get("username"),
                    severity=sev,
                    source_reference=f"{file.filename}:{ev.get('line_number', 0)}",
                    raw_line=ev.get("raw", "")[:500]
                )
                db.add(db_event)
                stored_count += 1

        # Store threat detections
        for f in findings_raw:
            try:
                th_sev = ThreatSeverity(f.get("severity", "MEDIUM").upper())
            except ValueError:
                th_sev = ThreatSeverity.MEDIUM

            db_threat = ThreatDetection(
                case_id=case_id,
                category=f.get("category", "ANOMALY"),
                description=f.get("description", ""),
                severity=th_sev,
                confidence=0.88,
                detection_source=f.get("detection_method", "deterministic_rules"),
                status=ThreatStatus.OPEN
            )
            db.add(db_threat)

        db.commit()

    log_findings = [
        LogFinding(
            finding_id=f.get("finding_id", ""),
            category=f.get("category", ""),
            severity=f.get("severity", "MEDIUM"),
            description=f.get("description", ""),
            source_ip=f.get("source_ip"),
            username=f.get("username")[0] if isinstance(f.get("username"), list) and f.get("username") else (f.get("username") if isinstance(f.get("username"), str) else None),
            timestamp=f.get("timestamp"),
            event_count=f.get("event_count", 0),
            evidence_lines=f.get("evidence_lines", []),
            detection_method=f.get("detection_method", "rule_based")
        )
        for f in findings_raw
    ]

    log_audit(
        db,
        action="LOG_ANALYSIS_EXECUTED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="LOG_FILE",
        details=f"Analyzed {file.filename}: {len(events)} events parsed, {len(log_findings)} findings"
    )

    return LogAnalysisResponse(
        file_name=file.filename,
        total_lines=len(lines),
        parsed_events=len(events),
        findings=log_findings,
        summary=f"Parsed {len(events)} events across {len(lines)} lines. Identified {len(log_findings)} potential threat indicators.",
        events_stored=stored_count
    )
