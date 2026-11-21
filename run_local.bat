@echo off
title CyberTrace AI - Local Server
echo ===================================================
echo Starting CyberTrace AI Digital Forensics Platform
echo ===================================================
echo.

cd /d "%~dp0backend"

if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found. Creating venv...
    py -m venv venv
    call venv\Scripts\activate.bat
    echo [*] Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not exist "cybertrace.db" (
    echo [*] Initializing database and demo forensic cases...
    python sample_data\seed_db.py
)

echo.
echo [*] Starting CyberTrace AI on http://localhost:8000 ...
echo [*] Open your browser at: http://localhost:8000
echo [*] Press Ctrl+C to stop the server.
echo.

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
