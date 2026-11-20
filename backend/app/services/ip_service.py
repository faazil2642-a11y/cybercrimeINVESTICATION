import ipaddress
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.event import InvestigationEvent
from app.models.evidence import EvidenceFile
from app.models.case import InvestigationCase


def validate_ip(ip_str: str) -> Tuple[bool, Optional[int]]:
    try:
        obj = ipaddress.ip_address(ip_str.strip())
        return True, obj.version
    except ValueError:
        return False, None


def analyze_ip_activity(
    db: Session,
    ip_str: str,
    case_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search case logs & investigation events for an IP.
    Calculates event counts, associated users, associated evidence files,
    first and last seen timestamps, and cross-case presence if authorized.
    """
    is_valid, ip_ver = validate_ip(ip_str)
    if not is_valid:
        return {
            "ip_address": ip_str,
            "is_valid": False,
            "ip_version": None,
            "total_events": 0,
            "associated_users": [],
            "associated_evidence": [],
            "first_seen": None,
            "last_seen": None,
            "related_cases": [],
            "event_summary": [],
            "note": "Invalid IPv4 or IPv6 address format."
        }

    query = db.query(InvestigationEvent).filter(
        (InvestigationEvent.source_ip == ip_str) | (InvestigationEvent.destination_ip == ip_str)
    )

    if case_id:
        query = query.filter(InvestigationEvent.case_id == case_id)

    events: List[InvestigationEvent] = query.order_by(InvestigationEvent.timestamp.asc()).all()

    users = set()
    evidence_ids = set()
    case_ids = set()

    for ev in events:
        if ev.username:
            users.add(ev.username)
        if ev.evidence_id:
            evidence_ids.add(ev.evidence_id)
        if ev.case_id:
            case_ids.add(ev.case_id)

    # Get evidence names
    evidence_names = []
    if evidence_ids:
        ev_records = db.query(EvidenceFile).filter(EvidenceFile.id.in_(list(evidence_ids))).all()
        evidence_names = [e.original_filename for e in ev_records]

    # Get related case numbers
    related_cases = []
    if case_ids:
        case_records = db.query(InvestigationCase).filter(InvestigationCase.id.in_(list(case_ids))).all()
        related_cases = [f"{c.case_number}: {c.title}" for c in case_records]

    first_seen = events[0].timestamp if events else None
    last_seen = events[-1].timestamp if events else None

    # Summarize event types
    event_summary = []
    summary_counts: Dict[str, int] = {}
    for ev in events:
        summary_counts[ev.event_type] = summary_counts.get(ev.event_type, 0) + 1
    for et, cnt in summary_counts.items():
        event_summary.append({"event_type": et, "count": cnt})

    return {
        "ip_address": ip_str,
        "is_valid": True,
        "ip_version": ip_ver,
        "total_events": len(events),
        "associated_users": sorted(list(users)),
        "associated_evidence": evidence_names,
        "first_seen": first_seen,
        "last_seen": last_seen,
        "related_cases": related_cases,
        "event_summary": event_summary,
        "note": "Deterministic telemetry compiled strictly from observed forensic records. Geolocation/reputation not simulated."
    }
