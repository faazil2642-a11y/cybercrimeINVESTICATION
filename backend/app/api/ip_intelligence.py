from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.schemas.investigation import IPAnalysisRequest, IPAnalysisResponse
from app.core.security import get_current_user
from app.services.ip_service import analyze_ip_activity
from app.services.audit_service import log_audit

router = APIRouter(prefix="/ip", tags=["IP Intelligence"])


@router.post("/analyze", response_model=IPAnalysisResponse)
def analyze_ip(
    payload: IPAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = analyze_ip_activity(db, payload.ip_address, payload.case_id)

    log_audit(
        db,
        action="IP_INVESTIGATION",
        user_id=current_user.id,
        user_email=current_user.email,
        details=f"Analyzed IP: {payload.ip_address}"
    )

    return IPAnalysisResponse(
        ip_address=result["ip_address"],
        is_valid=result["is_valid"],
        ip_version=result["ip_version"],
        total_events=result["total_events"],
        associated_users=result["associated_users"],
        associated_evidence=result["associated_evidence"],
        first_seen=result["first_seen"],
        last_seen=result["last_seen"],
        related_cases=result["related_cases"],
        event_summary=result["event_summary"],
        note=result["note"]
    )
