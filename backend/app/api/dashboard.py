from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.database import get_db
from app.models.case import InvestigationCase, CaseStatus
from app.models.evidence import EvidenceFile, ProcessingStatus, IntegrityStatus
from app.models.threat import ThreatDetection, ThreatSeverity
from app.models.event import InvestigationEvent
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview")
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_cases = db.query(InvestigationCase).count()
    active_cases = db.query(InvestigationCase).filter(InvestigationCase.status == CaseStatus.ACTIVE).count()
    under_review = db.query(InvestigationCase).filter(InvestigationCase.status == CaseStatus.UNDER_REVIEW).count()
    closed_cases = db.query(InvestigationCase).filter(InvestigationCase.status == CaseStatus.CLOSED).count()

    total_evidence = db.query(EvidenceFile).count()
    indexed_evidence = db.query(EvidenceFile).filter(EvidenceFile.processing_status == ProcessingStatus.INDEXED).count()
    verified_evidence = db.query(EvidenceFile).filter(EvidenceFile.integrity_status == IntegrityStatus.VERIFIED).count()

    threat_count = db.query(ThreatDetection).count()
    active_threats = db.query(ThreatDetection).filter(ThreatDetection.severity.in_([ThreatSeverity.HIGH, ThreatSeverity.CRITICAL])).count()

    integrity_pct = (verified_evidence / total_evidence * 100) if total_evidence > 0 else 100.0

    # Cases created today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cases_today = db.query(InvestigationCase).filter(InvestigationCase.created_at >= today_start).count()

    return {
        "total_cases": total_cases,
        "cases_today": cases_today,
        "active_cases": active_cases,
        "under_review_cases": under_review,
        "closed_cases": closed_cases,
        "total_evidence": total_evidence,
        "indexed_evidence": indexed_evidence,
        "verified_evidence": verified_evidence,
        "integrity_percent": round(integrity_pct, 1),
        "threat_indicators": threat_count,
        "active_threats": active_threats
    }


@router.get("/analytics")
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Threat category breakdown
    threat_cats = (
        db.query(ThreatDetection.category, func.count(ThreatDetection.id))
        .group_by(ThreatDetection.category)
        .all()
    )
    total_th = sum(cnt for _, cnt in threat_cats)
    threat_distribution = []
    colors_map = {
        "BRUTE_FORCE": "#52A8FF",
        "PHISHING": "#E2E2E2",
        "MALWARE": "#8A919D",
        "UNAUTHORIZED_ACCESS": "#7CDB8B",
        "DATA_EXFIL": "#C0C7D3",
        "SUSPICIOUS_LOGIN": "#52A8FF",
        "PRIVILEGE_ESCALATION": "#FFB4AB"
    }

    for cat, cnt in threat_cats:
        pct = round((cnt / total_th * 100) if total_th > 0 else 0, 1)
        threat_distribution.append({
            "category": cat.replace("_", " ").title(),
            "count": cnt,
            "percentage": pct,
            "color": colors_map.get(cat.upper(), "#9FCAFF")
        })

    # Hourly event velocity (last 24 hours)
    now = datetime.now(timezone.utc)
    hourly_telemetry = []
    for h in range(12, 0, -2):
        slot_time = now - timedelta(hours=h)
        slot_label = slot_time.strftime("%H:00")
        cnt = db.query(InvestigationEvent).filter(
            InvestigationEvent.timestamp >= slot_time - timedelta(hours=2),
            InvestigationEvent.timestamp < slot_time
        ).count()
        hourly_telemetry.append({"time": slot_label, "events": cnt})

    return {
        "threat_distribution": threat_distribution,
        "total_threats_logged": total_th,
        "hourly_telemetry": hourly_telemetry
    }


@router.get("/recent-activity")
def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recent_cases = (
        db.query(InvestigationCase)
        .order_by(InvestigationCase.created_at.desc())
        .limit(5)
        .all()
    )

    recent_events = (
        db.query(InvestigationEvent)
        .order_by(InvestigationEvent.timestamp.desc())
        .limit(6)
        .all()
    )

    cases_out = []
    for c in recent_cases:
        cases_out.append({
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "category": c.category.value,
            "priority": c.priority.value,
            "status": c.status.value,
            "created_at": c.created_at
        })

    events_out = []
    for ev in recent_events:
        events_out.append({
            "id": ev.id,
            "timestamp": ev.timestamp.strftime("%H:%M:%S"),
            "event_type": ev.event_type,
            "severity": ev.severity.value,
            "source_ip": ev.source_ip,
            "description": ev.description
        })

    return {
        "recent_cases": cases_out,
        "recent_events": events_out
    }
