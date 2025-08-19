@echo off
echo ================================================
echo    Poker Advisory - Quick Start (No Checks)
echo ================================================
echo.
echo Activating environment and starting server...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set environment token
set INGEST_TOKEN=test-token-123

REM Start server immediately
echo Starting at http://localhost:5000/unified
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000 --reload

pause