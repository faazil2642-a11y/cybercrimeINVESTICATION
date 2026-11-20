import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import create_tables
from app.api import (
    auth, dashboard, cases, evidence, investigation,
    logs, ip_intelligence, timeline, threats,
    knowledge_base, reports, settings as sys_settings, health
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure all storage directories exist
    for dir_path in [
        settings.UPLOAD_DIRECTORY,
        settings.REPORT_DIRECTORY,
        settings.TEMP_DIRECTORY,
        settings.CHROMA_PERSIST_DIRECTORY,
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Initialize SQLite or Postgres database tables
    try:
        create_tables()
    except Exception as e:
        print(f"[Startup Warning] Could not initialize tables automatically: {e}")
    yield



app = FastAPI(
    title="CyberTrace AI — Digital Forensics & Cybercrime Investigation Platform",
    description="Automated AI-assisted digital forensics, evidence chain-of-custody, and RAG-grounded cybercrime investigation platform.",
    version="2.4.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# CORS configuration
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Allows local dev and testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
api_v1_prefix = "/api"
app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(dashboard.router, prefix=api_v1_prefix)
app.include_router(cases.router, prefix=api_v1_prefix)
app.include_router(evidence.router, prefix=api_v1_prefix)
app.include_router(investigation.router, prefix=api_v1_prefix)
app.include_router(logs.router, prefix=api_v1_prefix)
app.include_router(ip_intelligence.router, prefix=api_v1_prefix)
app.include_router(timeline.router, prefix=api_v1_prefix)
app.include_router(threats.router, prefix=api_v1_prefix)
app.include_router(knowledge_base.router, prefix=api_v1_prefix)
app.include_router(reports.router, prefix=api_v1_prefix)
app.include_router(sys_settings.router, prefix=api_v1_prefix)

# Serve Frontend static assets for local development (Vercel serves them directly at CDN edge)
frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if not os.environ.get("VERCEL") and frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


