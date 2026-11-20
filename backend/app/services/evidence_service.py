"""
Evidence service: handles upload, storage, hashing, chain-of-custody,
and triggers async document processing.
"""
import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.models.evidence import EvidenceFile, ProcessingStatus, IntegrityStatus
from app.models.chain_of_custody import ChainOfCustody
from app.models.rag_document import RAGDocument, CollectionType, IndexingStatus
from app.services.hash_service import compute_sha256, compute_record_hash
from app.services.document_service import extract_text, is_supported
from app.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".log", ".docx", ".csv", ".json"
}
MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _new_evidence_number(db: Session) -> str:
    count = db.query(EvidenceFile).count()
    return f"EV-{count + 1:04d}"


def validate_upload(filename: str, file_size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not supported. Allowed: {sorted(ALLOWED_EXTENSIONS)}"
        )
    if file_size > MAX_SIZE_BYTES:
        raise ValidationError(
            f"File size {file_size / 1024 / 1024:.1f} MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB"
        )


def store_evidence_file(file_bytes: bytes, original_filename: str, case_id: str) -> str:
    """Store the original evidence file immutably. Returns absolute storage path."""
    ext = Path(original_filename).suffix.lower()
    stored_name = f"{uuid.uuid4()}{ext}"
    dest_dir = Path(settings.UPLOAD_DIRECTORY) / case_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / stored_name

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    return str(dest_path)


def create_evidence_record(
    db: Session,
    case_id: str,
    original_filename: str,
    stored_filename: str,
    storage_path: str,
    file_size: int,
    sha256_hash: str,
    file_type: str,
    uploaded_by: str,
) -> EvidenceFile:
    evidence = EvidenceFile(
        evidence_number=_new_evidence_number(db),
        case_id=case_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_type,
        file_size=file_size,
        sha256_hash=sha256_hash,
        storage_path=storage_path,
        processing_status=ProcessingStatus.UPLOADED,
        integrity_status=IntegrityStatus.VERIFIED,
        uploaded_by=uploaded_by,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def add_custody_record(
    db: Session,
    evidence_id: str,
    action: str,
    performed_by: str,
    performed_by_name: str,
    details: str = "",
) -> ChainOfCustody:
    # Get last record hash for chain linking
    last = (
        db.query(ChainOfCustody)
        .filter(ChainOfCustody.evidence_id == evidence_id)
        .order_by(ChainOfCustody.timestamp.desc())
        .first()
    )
    previous_hash = last.record_hash if last else ""
    record_content = f"{evidence_id}:{action}:{performed_by}:{datetime.now(timezone.utc).isoformat()}"
    record_hash = compute_record_hash(record_content, previous_hash)

    record = ChainOfCustody(
        evidence_id=evidence_id,
        action=action,
        performed_by=performed_by,
        performed_by_name=performed_by_name,
        details=details,
        previous_record_hash=previous_hash,
        record_hash=record_hash,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def process_evidence_background(evidence_id: str, storage_path: str, original_filename: str, case_id: str):
    """
    Background task: extract text → chunk → embed → index into ChromaDB.
    Updates processing_status at each step.
    """
    from app.database import SessionLocal
    from app.rag.retriever import index_document
    from app.models.rag_document import RAGDocument, CollectionType, IndexingStatus

    db = SessionLocal()
    try:
        evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
        if not evidence:
            return

        # Step 1: Copy to temporary working directory
        temp_dir = Path(settings.TEMP_DIRECTORY) / case_id
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = str(temp_dir / Path(storage_path).name)
        shutil.copy2(storage_path, temp_path)

        # Step 2: Extract text from working copy
        evidence.processing_status = ProcessingStatus.PROCESSING
        db.commit()

        text = extract_text(temp_path, original_filename)

        evidence.processing_status = ProcessingStatus.EXTRACTED
        db.commit()

        if not text.strip() or text.startswith("["):
            # Extraction failed or unsupported
            evidence.processing_status = ProcessingStatus.FAILED
            evidence.error_message = text[:500] if text.startswith("[") else "Empty content after extraction"
            db.commit()
            return

        # Step 3: Create RAG document record
        rag_doc = RAGDocument(
            document_name=original_filename,
            document_type=Path(original_filename).suffix.lower(),
            case_id=case_id,
            evidence_id=evidence_id,
            collection_type=CollectionType.CASE_EVIDENCE,
            indexing_status=IndexingStatus.INDEXING,
        )
        db.add(rag_doc)
        db.commit()
        db.refresh(rag_doc)

        # Step 4: Index into ChromaDB
        chunk_ids = index_document(
            text=text,
            document_id=rag_doc.id,
            evidence_id=evidence_id,
            case_id=case_id,
            filename=original_filename,
        )

        # Step 5: Update records
        rag_doc.indexing_status = IndexingStatus.INDEXED
        rag_doc.chunk_count = len(chunk_ids)
        evidence.processing_status = ProcessingStatus.INDEXED
        evidence.chunk_count = len(chunk_ids)
        db.commit()

        # Clean up temp file
        try:
            os.remove(temp_path)
        except Exception:
            pass

    except Exception as e:
        try:
            evidence = db.query(EvidenceFile).filter(EvidenceFile.id == evidence_id).first()
            if evidence:
                evidence.processing_status = ProcessingStatus.FAILED
                evidence.error_message = str(e)[:500]
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
