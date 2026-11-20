import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.config import settings
from app.rag.vector_store import get_collection_stats

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. Database check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {str(e)[:100]}"

    # 2. Vector DB check
    vector_status = "ok"
    vector_stats = {}
    try:
        vector_stats = get_collection_stats()
    except Exception as e:
        vector_status = f"error: {str(e)[:100]}"

    # 3. AI Provider check
    ai_status = "configured" if bool(settings.GEMINI_API_KEY) else "unconfigured (GEMINI_API_KEY missing)"

    # 4. Storage availability
    evidence_dir = os.path.exists(settings.UPLOAD_DIRECTORY)
    reports_dir = os.path.exists(settings.REPORT_DIRECTORY)
    storage_status = "available" if (evidence_dir and reports_dir) else "missing_directories"

    return {
        "status": "healthy" if db_status == "ok" else "degraded",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "vector_database": {
            "status": vector_status,
            "collections": vector_stats
        },
        "ai_provider": {
            "provider": settings.LLM_PROVIDER,
            "model": settings.GEMINI_MODEL,
            "status": ai_status
        },
        "storage": {
            "status": storage_status,
            "evidence_dir": settings.UPLOAD_DIRECTORY,
            "reports_dir": settings.REPORT_DIRECTORY
        }
    }
