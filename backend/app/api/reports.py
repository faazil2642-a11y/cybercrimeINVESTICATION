import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.report import InvestigationReport
from app.schemas.investigation import ReportRequest, ReportOut
from app.core.security import get_current_user, require_roles
from app.services.report_service import generate_forensic_report_pdf
from app.services.audit_service import log_audit

router = APIRouter(prefix="/reports", tags=["Forensic Reports"])


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportRequest,
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    try:
        report = generate_forensic_report_pdf(
            db=db,
            case_id=payload.case_id,
            report_title=payload.report_title,
            generated_by_id=current_user.id,
            generated_by_name=current_user.full_name
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"PDF generation error: {e}")

    log_audit(
        db,
        action="REPORT_GENERATED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="REPORT",
        resource_id=report.id,
        details=f"Generated report {report.report_number} for case {payload.case_id}"
    )

    return ReportOut(
        id=report.id,
        report_number=report.report_number,
        case_id=report.case_id,
        report_title=report.report_title,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        status=report.status.value
    )


@router.get("", response_model=List[ReportOut])
def list_reports(
    case_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(InvestigationReport)
    if case_id:
        query = query.filter(InvestigationReport.case_id == case_id)
    items = query.order_by(InvestigationReport.generated_at.desc()).all()
    return [
        ReportOut(
            id=r.id,
            report_number=r.report_number,
            case_id=r.case_id,
            report_title=r.report_title,
            generated_by_name=r.generated_by_name,
            generated_at=r.generated_at,
            status=r.status.value
        )
        for r in items
    ]


@router.get("/{report_id}", response_model=ReportOut)
def get_report_meta(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(InvestigationReport).filter(InvestigationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report record not found.")
    return ReportOut(
        id=report.id,
        report_number=report.report_number,
        case_id=report.case_id,
        report_title=report.report_title,
        generated_by_name=report.generated_by_name,
        generated_at=report.generated_at,
        status=report.status.value
    )


@router.get("/{report_id}/download")
def download_report_pdf(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(InvestigationReport).filter(InvestigationReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    if not report.report_path or not os.path.exists(report.report_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report PDF file not found on disk.")

    log_audit(
        db,
        action="REPORT_DOWNLOADED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="REPORT",
        resource_id=report.id,
        details=f"Downloaded report {report.report_number}"
    )

    return FileResponse(
        path=report.report_path,
        filename=f"{report.report_number}.pdf",
        media_type="application/pdf"
    )
