from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User, UserRole
from app.models.threat import ThreatDetection, ThreatSeverity, ThreatStatus
from app.schemas.investigation import ThreatOut
from app.core.security import get_current_user, require_roles
from app.services import threat_service

router = APIRouter(prefix="/threats", tags=["Threat Detection"])


class StatusUpdatePayload(BaseModel):
    status: str


@router.get("", response_model=List[ThreatOut])
def list_threats(
    case_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    items = threat_service.get_case_threats(db, case_id=case_id, severity=severity, status=status)
    return [ThreatOut.model_validate(t) for t in items]


@router.get("/{threat_id}", response_model=ThreatOut)
def get_threat_detail(
    threat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(ThreatDetection).filter(ThreatDetection.id == threat_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat record not found.")
    return ThreatOut.model_validate(item)


@router.put("/{threat_id}/status", response_model=ThreatOut)
def update_threat(
    threat_id: str,
    payload: StatusUpdatePayload,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    try:
        status_enum = ThreatStatus(payload.status.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status value.")

    updated = threat_service.update_threat_status(db, threat_id, status_enum)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat record not found.")
    return ThreatOut.model_validate(updated)
