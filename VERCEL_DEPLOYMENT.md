# CyberTrace AI — Vercel Deployment Guide

This guide details how to deploy **CyberTrace AI** to Vercel.

---

## 1. What Has Been Pre-Configured for Vercel

All required files for Vercel have already been generated in your project root:
- [`vercel.json`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/vercel.json): Configures automatic routing so the frontend is served at `/` and all `/api/*` calls are routed to the Python serverless function.
- [`api/index.py`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/api/index.py): Serverless ASGI adapter linking FastAPI directly to Vercel's Python runtime.
- [`requirements.txt`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/requirements.txt): Optimized dependencies for Vercel's serverless build environment.
- [`.vercelignore`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/.vercelignore): Excludes local virtual environments (`venv`), local test caches, and temp files from being uploaded.
- [`backend/app/config.py`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/backend/app/config.py): Auto-detects Vercel's read-only environment and routes file operations to `/tmp`.

---

## 2. Deploying via GitHub & Vercel Web Dashboard (Recommended)

This method requires **no command line tools** on your machine.

### Step 1: Upload to GitHub
1. Go to [github.com](https://github.com) and create a new repository (e.g., `cybertrace-ai`).
2. Upload the project files (or use GitHub Desktop if installed).

### Step 2: Import into Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** → **"Project"**.
3. Under **Import Git Repository**, select your `cybertrace-ai` repository.
4. In the Project Configuration:
   - **Framework Preset:** Leave as *Other*.
   - **Root Directory:** `./` (default).
5. Open **Environment Variables** and add:
   - `SECRET_KEY`: any long random string (e.g. `cybertrace-secure-jwt-key-prod-2026`).
   - `GEMINI_API_KEY`: your Google Gemini API key (optional, for RAG chat).
   - `DATABASE_URL`: *(Recommended for production)* A free PostgreSQL connection string from [Neon.tech](https://neon.tech) or [Supabase](https://supabase.com). If left blank, it uses a local SQLite fallback in `/tmp`.
6. Click **Deploy**.

---

## 3. Important Notes on Serverless Architecture

Vercel functions run in a **serverless, ephemeral environment**:
1. **Local Filesystem:** On Vercel, the only writable directory is `/tmp`. Any files written to `/tmp` (such as local SQLite or evidence uploads) reset when the serverless function cold-starts.
2. **For Permanent Data Persistence:**
   - Use a free cloud Postgres database like [Neon Serverless Postgres](https://neon.tech) and set `DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require` in your Vercel Environment Variables.
   - For uploaded evidence files, connect cloud object storage (e.g. AWS S3, Supabase Storage, or Cloudinary).
3. **Alternative Dual-Host Architecture (Optional):**
   - Host the **Frontend on Vercel** (global edge CDN).
   - Host the **Backend on Render or Railway** using the included [`backend/Dockerfile`](file:///c:/Users/hp/Downloads/stitch_cybertrace_ai_forensics_platform/backend/Dockerfile) with a persistent disk for ChromaDB and files.
   - In your Vercel project settings, set an environment variable `NEXT_PUBLIC_API_URL` or define `window.CYBERTRACE_API_URL = "https://your-backend.onrender.com"` in `frontend/index.html`.
