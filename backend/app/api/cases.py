from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.case import InvestigationCase
from app.schemas.case import CaseCreate, CaseUpdate, CaseOut, CaseListResponse
from app.core.security import get_current_user, require_roles
from app.services import case_service
from app.services.audit_service import log_audit

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_new_case(
    payload: CaseCreate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    case = case_service.create_case(
        db=db,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        investigator_id=payload.investigator_id or current_user.id
    )

    log_audit(
        db,
        action="CASE_CREATED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="CASE",
        resource_id=case.id,
        details=f"Case {case.case_number} created: {case.title}"
    )
    return case


@router.get("", response_model=CaseListResponse)
def list_cases(
    search: Optional[str] = Query(None, description="Search term for case number, title, description"),
    status: Optional[str] = Query(None, description="Filter by status (ACTIVE, UNDER_REVIEW, CLOSED, ARCHIVED)"),
    priority: Optional[str] = Query(None, description="Filter by priority (LOW, MEDIUM, HIGH, CRITICAL)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    assigned_to_me: Optional[bool] = Query(False, description="Filter to cases assigned to current user"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investigator_id = current_user.id if assigned_to_me else None
    items, total = case_service.get_cases(
        db=db,
        search=search,
        status=status,
        priority=priority,
        category=category,
        investigator_id=investigator_id,
        page=page,
        per_page=per_page
    )
    return CaseListResponse(
        items=[CaseOut.model_validate(c) for c in items],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = case_service.get_case_by_id(db, case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found.")
    return case


@router.put("/{case_id}", response_model=CaseOut)
def update_case_details(
    case_id: str,
    payload: CaseUpdate,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    updated = case_service.update_case(
        db=db,
        case_id=case_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        status=payload.status,
        investigator_id=payload.investigator_id
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found.")

    log_audit(
        db,
        action="CASE_UPDATED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="CASE",
        resource_id=case_id
    )
    return updated


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    success = case_service.delete_case(db, case_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found.")

    log_audit(
        db,
        action="CASE_DELETED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="CASE",
        resource_id=case_id
    )
    return None
