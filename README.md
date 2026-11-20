# CyberTrace AI — Digital Forensics & Cybercrime Investigation Platform

An enterprise-grade, AI-assisted digital forensics and cybercrime investigation platform using **Retrieval-Augmented Generation (RAG)**, automated log analysis, cryptographic evidence vaults, and court-admissible forensic reporting.

---

## 1. System Architecture

```
cybertrace_ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint, CORS, lifespan, static mounting
│   │   ├── config.py                # Environment configuration (pydantic-settings)
│   │   ├── database.py              # SQLAlchemy 2.x engine, session, Base
│   │   ├── models/                  # Relational database models (10 tables)
│   │   │   ├── user.py              # Users & roles (ADMIN, INVESTIGATOR, VIEWER)
│   │   │   ├── case.py              # Investigation case dossiers & priorities
│   │   │   ├── evidence.py          # Evidence files with SHA-256 tracking
│   │   │   ├── chain_of_custody.py  # Chained cryptographic custody audit trail
│   │   │   ├── event.py             # Reconstructed investigation events
│   │   │   ├── threat.py            # Threat indicators & confidence scores
│   │   │   ├── rag_document.py      # Indexed documents and chunk records
│   │   │   ├── chat.py              # Investigation chat history & citations
│   │   │   ├── report.py            # Formal forensic examination reports
│   │   │   └── audit.py             # System audit logs
│   │   ├── schemas/                 # Pydantic validation schemas
│   │   ├── api/                     # REST API routers (/api/*)
│   │   │   ├── auth.py              # Registration, JWT login, profile, RBAC
│   │   │   ├── dashboard.py         # Real-time metrics & telemetry
│   │   │   ├── cases.py             # Case CRUD & filtering
│   │   │   ├── evidence.py          # File upload, SHA-256 verify, custody trail
│   │   │   ├── investigation.py     # Case-isolated RAG chat & citations
│   │   │   ├── logs.py              # Multi-format log parser & anomaly detection
│   │   │   ├── ip_intelligence.py   # Observed IP profiler
│   │   │   ├── timeline.py          # Chronological incident reconstruction
│   │   │   ├── threats.py           # Threat detection list & triage
│   │   │   ├── knowledge_base.py    # Reference corpus ingestion & search
│   │   │   ├── reports.py           # ReportLab PDF report generation & download
│   │   │   ├── settings.py          # Platform parameters & vector stats
│   │   │   └── health.py            # Comprehensive subsystem health check
│   │   ├── services/                # Business logic & domain services
│   │   │   ├── hash_service.py      # Non-destructive chunk-based SHA-256 hashing
│   │   │   ├── document_service.py  # Working-copy text extraction (PDF, DOCX, CSV, TXT, LOG, JSON)
│   │   │   ├── evidence_service.py  # Acquisition, immutable storage, async RAG trigger
│   │   │   ├── log_analyzer.py      # Syslog, Windows CSV, IsolationForest anomaly detection
│   │   │   ├── ip_service.py        # Case evidence IP profiling
│   │   │   ├── timeline_service.py  # Chronological event tracking
│   │   │   ├── threat_service.py    # Threat detection registry
│   │   │   ├── report_service.py    # NumberedCanvas ReportLab PDF builder
│   │   │   └── audit_service.py     # Append-only system audit logger
│   │   ├── core/                    # Security, JWT, permissions, exceptions
│   │   └── rag/                     # RAG pipeline implementation
│   │       ├── chunking.py          # Overlapping chunker with line metadata
│   │       ├── embeddings.py        # sentence-transformers/all-MiniLM-L6-v2
│   │       ├── vector_store.py      # ChromaDB collections with case_id filtering
│   │       ├── prompts.py           # Grounded, anti-hallucination forensic prompt
│   │       ├── generator.py         # Google Gemini LLM API integration
│   │       └── retriever.py         # Retrieval orchestration & citation parser
│   ├── sample_data/                 # Demonstration logs, CSVs, and seed script
│   ├── tests/                       # Complete Pytest test suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
└── frontend/                        # Preserved Stitch Obsidian Forensics UI (SPA)
    ├── index.html                   # Unified dashboard, cases, vault, RAG assistant
    └── js/
        ├── api.js                   # Centralized API service client
        └── app.js                   # Reactive state, telemetry, and event handlers
```

---

## 2. Technology Stack

- **Backend Framework:** FastAPI with Uvicorn
- **ORM & Database:** SQLAlchemy 2.x with Alembic migrations
- **Databases:** PostgreSQL (production / Docker) with SQLite zero-config fallback
- **AI & RAG:** LangChain-style pipeline, ChromaDB (persistent vector store), SentenceTransformers (`all-MiniLM-L6-v2`), Google Gemini API (`gemini-1.5-flash`)
- **Document Processing:** PyMuPDF (PDF), python-docx (DOCX), Pandas (CSV), JSON & syslog parsers
- **Machine Learning:** Scikit-learn (IsolationForest anomaly detection)
- **Report Generation:** ReportLab (multi-page PDF with running headers/footers)
- **Frontend:** Vanilla HTML5 + Tailwind CSS (Stitch Obsidian Dark theme) + Vanilla JavaScript (Fetch API)

---

## 3. Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Git

### Step 1: Clone & Configure
```powershell
cd backend
copy .env.example .env
```
Edit `.env` if you wish to configure your Google Gemini API key:
```ini
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*(Note: If no key is provided, all non-AI features—including evidence hashing, custody logs, log parsing, case management, and PDF report generation—work completely out of the box).*

### Step 2: Create Virtual Environment & Install Dependencies
```powershell
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Seed Database with Demonstration Forensic Data
```powershell
python sample_data/seed_db.py
```
This initializes:
- Default Admin: `admin@cybertrace.ai` / `CyberTrace2026!`
- Default Investigator: `chen@cybertrace.ai` / `Forensics2026!`
- Demonstration Cases: `CT-2026-001`, `CT-2026-002`, `CT-2026-003`
- Pre-seeded evidence files, timeline events, and threat detections.

### Step 4: Run Application
```powershell
uvicorn app.main:app --reload --port 8000
```

Open your browser:
- **Application Web UI:** [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Subsystem Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 4. Running with Docker Compose (PostgreSQL + Persistent ChromaDB)

```powershell
docker-compose up -d --build
```
This spins up:
- PostgreSQL 15 on port `5432`
- CyberTrace AI Backend on port `8000`
- Volume mappings for `/app/storage` and `/app/chroma_db`

---

## 5. End-to-End Workflows

1. **Workflow 1: Case Creation**  
   Investigator logs in → Creates a case → Stored in database with auto-generated case number (`CT-2026-XXX`) → Overview metrics dynamically increment.
2. **Workflow 2: Digital Evidence Ingestion**  
   Investigator uploads a forensic log or PDF → File is stored in write-blocked storage → SHA-256 is computed instantly → Chain-of-custody ledger records acquisition.
3. **Workflow 3: Asynchronous RAG Indexing**  
   Background worker extracts text from working copy → Chunks with line-level start/end tracking → Generates dense vector embeddings → Inserts into ChromaDB tagged with `case_id`.
4. **Workflow 4: AI Investigation (Strict Case Isolation)**  
   Investigator queries the AI co-processor → ChromaDB filters vectors with `where={"case_id": active_case_id}` → Relevant excerpts retrieved → Gemini formulates grounded response with bracketed source citations `[auth_server.log:142]`.
5. **Workflow 5: Forensic Log Analysis**  
   Investigator uploads raw auth log → Parser segments events → Heuristic engine flags brute force (>5 attempts in 10m) and privilege escalation → IsolationForest identifies statistical IP anomalies.
6. **Workflow 6: Incident Timeline**  
   Chronological event reconstruction aggregates authentication anomalies, file ingestions, and detections into an audit trail with timezone-aware UTC timestamps.
7. **Workflow 7: Forensic PDF Report Generation**  
   Investigator triggers export → ReportLab compiles executive summary, SHA-256 evidence digests, timeline traces, and RAG findings into a court-ready document with running page numbers.
8. **Workflow 8: Case Isolation Guarantee**  
   RAG semantic retrieval and database queries enforce case-level isolation, ensuring Case A never retrieves evidence from Case B.

---

## 6. Running Automated Tests

```powershell
pytest tests/ -v
```
All unit and integration tests cover authentication, case CRUD, evidence hashing, log analysis rules, RAG chunking, and PDF generation.
#   c y b e r c r i m e I N V E S T I C A T I O N  
 #   c y b e r c r i m e I N V E S T I C A T I O N  
 