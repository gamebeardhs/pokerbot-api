@echo off
echo ================================================
echo    Quick Start - Poker Advisory System
echo ================================================
echo.
echo Starting system with existing configuration...
echo (No dependency checks - fastest startup)
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found
    echo Please run setup_windows_basic.bat or setup_windows_advanced.bat first
    pause
    exit /b 1
)

echo.
echo ================================================
echo    Starting Poker Advisory System...
echo ================================================
echo.
echo System will be available at:
echo   - Main Interface: http://localhost:5000/unified
echo   - Auto Advisory: http://localhost:5000/auto-advisory
echo   - API Docs: http://localhost:5000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Set environment token for local testing
set INGEST_TOKEN=test-token-123

REM Start the server
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 5000 --reload

echo.
echo Server stopped. Press any key to exit...
pause >nul