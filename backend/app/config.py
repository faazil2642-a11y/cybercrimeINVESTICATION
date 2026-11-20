import os
import secrets
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CyberTrace AI"
    APP_VERSION: str = "2.4.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # Database (uses /tmp if on Vercel and using SQLite)
    DATABASE_URL: str = "sqlite:////tmp/cybertrace.db" if os.environ.get("VERCEL") else "sqlite:///./cybertrace.db"

    # AI / LLM
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ChromaDB & Storage (auto-detect Vercel serverless /tmp environment)
    CHROMA_PERSIST_DIRECTORY: str = "/tmp/chroma_db" if os.environ.get("VERCEL") else "./chroma_db"
    UPLOAD_DIRECTORY: str = "/tmp/storage/evidence" if os.environ.get("VERCEL") else "./storage/evidence"
    REPORT_DIRECTORY: str = "/tmp/storage/reports" if os.environ.get("VERCEL") else "./storage/reports"
    TEMP_DIRECTORY: str = "/tmp/storage/temporary" if os.environ.get("VERCEL") else "./storage/temporary"
    MAX_UPLOAD_SIZE_MB: int = 50

    # RAG
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.3
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
