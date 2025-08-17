@echo off
echo 🃏 Poker Advisory App - Windows Quick Start
echo ==========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Run Windows setup if needed
if not exist "windows_setup_complete.flag" (
    echo 🔧 Running Windows setup...
    python WINDOWS_SETUP_OPTIMIZED.py
    if not errorlevel 1 echo setup_complete > windows_setup_complete.flag
    echo.
)

REM Start the application
echo 🚀 Starting Poker Advisory App...
python start_app.py

pause