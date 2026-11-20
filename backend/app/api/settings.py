from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, UserRole
from app.core.security import get_current_user, require_roles
from app.rag.vector_store import get_collection_stats

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("")
def get_system_settings(current_user: User = Depends(get_current_user)):
    stats = get_collection_stats()
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "gemini_model": settings.GEMINI_MODEL,
        "ai_configured": bool(settings.GEMINI_API_KEY),
        "embedding_model": settings.EMBEDDING_MODEL,
        "chunk_size": settings.CHUNK_SIZE,
        "chunk_overlap": settings.CHUNK_OVERLAP,
        "rag_top_k": settings.RAG_TOP_K,
        "similarity_threshold": settings.RAG_SIMILARITY_THRESHOLD,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "chroma_persist_directory": settings.CHROMA_PERSIST_DIRECTORY,
        "vector_collections": stats
    }
