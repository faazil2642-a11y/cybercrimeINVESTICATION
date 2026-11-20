from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pathlib import Path

from app.database import get_db
from app.models.user import User, UserRole
from app.models.evidence import EvidenceFile, ProcessingStatus, IntegrityStatus
from app.models.chain_of_custody import ChainOfCustody
from app.schemas.evidence import (
    EvidenceOut, EvidenceListResponse, HashVerifyResponse,
    CustodyRecord, EvidencePreview
)
from app.core.security import get_current_user, require_roles
from app.services import evidence_service
from app.services.hash_service import compute_sha256_bytes, verify_file_integrity
from app.services.document_service import extract_text
from app.services.audit_service import log_audit

router = APIRouter(prefix="/evidence", tags=["Evidence Management"])


@router.post("/upload", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    background_tasks: BackgroundTasks,
    case_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    # Read bytes
    content = await file.read()
    file_size = len(content)

    # Validate file type and size limit
    evidence_service.validate_upload(file.filename, file_size)

    # Calculate SHA-256 hash immediately upon byte acquisition
    sha256 = compute_sha256_bytes(content)

    # Store file immutably in designated case vault directory
    storage_path = evidence_service.store_evidence_file(
        file_bytes=content,
        original_filename=file.filename,
        case_id=case_id
    )

    # Detect extension
    ext = Path(file.filename).suffix.lower()

    # Record in database
    evidence = evidence_service.create_evidence_record(
        db=db,
        case_id=case_id,
        original_filename=file.filename,
        stored_filename=Path(storage_path).name,
        storage_path=storage_path,
        file_size=file_size,
        sha256_hash=sha256,
        file_type=ext.lstrip("."),
        uploaded_by=current_user.id
    )

    # Chain of custody record for acquisition
    evidence_service.add_custody_record(
        db=db,
        evidence_id=evidence.id,
        action="EVIDENCE_ACQUIRED",
        performed_by=current_user.id,
        performed_by_name=current_user.full_name,
        details=f"File ingested: {file.filename} ({file_size} bytes). SHA-256 seal: {sha256}"
    )

    # Queue asynchronous background text extraction and RAG chunk indexing
    background_tasks.add_task(
        evidence_service.process_evidence_background,
        evidence_id=evidence.id,
        storage_path=storage_path,
        original_filename=file.filename,
        case_id=case_id
    )

    log_audit(
        db,
        action="EVIDENCE_UPLOADED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="EVIDENCE",
        resource_id=evidence.id,
        details=f"Uploaded {file.filename} ({evidence.evidence_number})"
    )

    return evidence


@router.get("", response_model=EvidenceListResponse)
def list_evidence(
    case_id: Optional[str] = None,
    processing_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(EvidenceFile)
    if case_id:
        query = query.filter(EvidenceFile.case_id == case_id)
    if processing_status:
        try:
            status_enum = ProcessingStatus(processing_status.upper())
            query = query.filter(EvidenceFile.processing_status == status_enum)
        except ValueError:
            pass

    items = query.order_by(EvidenceFile.upload_timestamp.desc()).all()
    return EvidenceListResponse(
        items=[EvidenceOut.model_validate(e) for e in items],
        total=len(items)
    )


@router.get("/{evidence_id}", response_model=EvidenceOut)
def get_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence artifact not found.")
    return evidence


@router.get("/{evidence_id}/preview", response_model=EvidencePreview)
def get_evidence_preview(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence artifact not found.")

    text = extract_text(evidence.storage_path, evidence.original_filename)
    preview = text[:2500] if text else "No text extracted."
    return EvidencePreview(
        evidence_id=evidence.id,
        filename=evidence.original_filename,
        preview_text=preview,
        total_chars=len(text) if text else 0
    )


@router.get("/{evidence_id}/hash", response_model=HashVerifyResponse)
def verify_evidence_hash(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence artifact not found.")

    is_intact = verify_file_integrity(evidence.storage_path, evidence.sha256_hash)
    evidence.integrity_status = IntegrityStatus.VERIFIED if is_intact else IntegrityStatus.MISMATCH
    db.commit()

    return HashVerifyResponse(
        evidence_id=evidence.id,
        original_hash=evidence.sha256_hash or "",
        current_hash=evidence.sha256_hash if is_intact else "MISMATCH_DETECTED",
        match=is_intact,
        verified_at=datetime.now(timezone.utc)
    )


@router.get("/{evidence_id}/custody", response_model=List[CustodyRecord])
def get_chain_of_custody(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(ChainOfCustody)
        .filter(ChainOfCustody.evidence_id == evidence_id)
        .order_by(ChainOfCustody.timestamp.asc())
        .all()
    )
    return [CustodyRecord.model_validate(r) for r in records]


@router.get("/{evidence_id}/status")
def get_processing_status(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence artifact not found.")
    return {
        "evidence_id": evidence.id,
        "processing_status": evidence.processing_status.value,
        "chunk_count": evidence.chunk_count,
        "error_message": evidence.error_message
    }
