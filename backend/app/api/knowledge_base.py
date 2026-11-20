import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User, UserRole
from app.models.rag_document import RAGDocument, CollectionType, IndexingStatus
from app.schemas.rag import KnowledgeUploadResponse, KnowledgeDocOut
from app.core.security import get_current_user, require_roles
from app.services.document_service import extract_text
from app.rag.retriever import index_document
from app.rag.vector_store import query_collection, KNOWLEDGE_COLLECTION
from app.rag.embeddings import embed_query
from app.config import settings
from app.services.audit_service import log_audit

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])


@router.post("/upload", response_model=KnowledgeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(
    file: UploadFile = File(...),
    category: Optional[str] = Form("Digital Forensics"),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVESTIGATOR)),
    db: Session = Depends(get_db)
):
    content = await file.read()
    temp_dir = Path(settings.TEMP_DIRECTORY) / "knowledge"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / file.filename

    with open(temp_file, "wb") as f:
        f.write(content)

    text = extract_text(str(temp_file), file.filename)

    rag_doc = RAGDocument(
        document_name=file.filename,
        document_type=Path(file.filename).suffix.lower(),
        collection_type=CollectionType.KNOWLEDGE,
        indexing_status=IndexingStatus.INDEXING,
        created_at=datetime.now(timezone.utc)
    )
    db.add(rag_doc)
    db.commit()
    db.refresh(rag_doc)

    try:
        chunk_ids = index_document(
            text=text,
            document_id=rag_doc.id,
            evidence_id="",
            case_id="",
            filename=file.filename,
            collection_name=KNOWLEDGE_COLLECTION
        )
        rag_doc.indexing_status = IndexingStatus.INDEXED
        rag_doc.chunk_count = len(chunk_ids)
        db.commit()
        msg = f"Indexed {len(chunk_ids)} knowledge chunks into {KNOWLEDGE_COLLECTION}."
    except Exception as e:
        rag_doc.indexing_status = IndexingStatus.FAILED
        db.commit()
        msg = f"Indexing failed: {e}"

    try:
        os.remove(temp_file)
    except Exception:
        pass

    log_audit(
        db,
        action="KNOWLEDGE_UPLOADED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type="KNOWLEDGE_DOC",
        resource_id=rag_doc.id,
        details=f"Uploaded knowledge file {file.filename} (Category: {category})"
    )

    return KnowledgeUploadResponse(
        document_id=rag_doc.id,
        document_name=rag_doc.document_name,
        indexing_status=rag_doc.indexing_status.value,
        message=msg
    )


@router.get("/documents", response_model=List[KnowledgeDocOut])
def list_knowledge_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    docs = (
        db.query(RAGDocument)
        .filter(RAGDocument.collection_type == CollectionType.KNOWLEDGE)
        .order_by(RAGDocument.created_at.desc())
        .all()
    )
    return [
        KnowledgeDocOut(
            id=d.id,
            document_name=d.document_name,
            document_type=d.document_type,
            indexing_status=d.indexing_status.value,
            chunk_count=d.chunk_count,
            created_at=d.created_at
        )
        for d in docs
    ]


@router.get("/documents/{doc_id}", response_model=KnowledgeDocOut)
def get_knowledge_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc = db.query(RAGDocument).filter(RAGDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return KnowledgeDocOut(
        id=doc.id,
        document_name=doc.document_name,
        document_type=doc.document_type,
        indexing_status=doc.indexing_status.value,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at
    )


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_document(
    doc_id: str,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    doc = db.query(RAGDocument).filter(RAGDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    db.delete(doc)
    db.commit()
    return None


@router.get("/search")
def search_knowledge_base(
    query: str = Query(..., description="Semantic search query"),
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    q_emb = embed_query(query)
    results = query_collection(
        query_embedding=q_emb,
        collection_name=KNOWLEDGE_COLLECTION,
        n_results=top_k
    )
    return {
        "query": query,
        "results": [
            {
                "chunk_id": r["chunk_id"],
                "content": r["content"],
                "filename": r.get("metadata", {}).get("filename", ""),
                "similarity": r.get("similarity", 0.0)
            }
            for r in results
        ]
    }
