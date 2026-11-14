@echo off
title Industrial Safety AI Server
echo ============================================================
echo Starting Industrial Safety AI Server...
echo ============================================================
cd /d "%~dp0"
call .\venv\Scripts\activate.bat
echo URL: http://localhost:8000 (or http://127.0.0.1:8000)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
pause
