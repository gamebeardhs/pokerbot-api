@echo off
echo ================================================
echo    Poker Advisory System - Windows Launcher
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/6] Python detected - checking version...
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python 3.8+ required. Please upgrade Python.
    pause
    exit /b 1
)

echo [2/6] Creating virtual environment (if needed)...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)

echo [3/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo [4/6] Checking and installing dependencies...
echo Installing core dependencies...
pip install --quiet fastapi uvicorn pydantic python-multipart websockets requests

echo Installing computer vision dependencies...
pip install --quiet opencv-python pillow numpy

echo Installing OCR dependencies...
pip install --quiet pytesseract easyocr

echo Installing poker analysis dependencies...
pip install --quiet scikit-learn pandas joblib hnswlib

echo Installing screen capture dependencies...
pip install --quiet mss pyautogui imagehash

echo Installing optional dependencies...
pip install --quiet playwright trafilatura pytest pytest-asyncio nest-asyncio tensorflow

echo Installing OpenSpiel (advanced GTO - may fail without Visual Studio Build Tools)...
pip install --quiet open-spiel 2>nul
if %errorlevel% neq 0 (
    echo WARNING: OpenSpiel installation failed - advanced GTO features disabled
    echo System will use database fallback for GTO recommendations
    echo To enable full GTO: Install Visual Studio Build Tools, then run setup_windows_advanced.bat
)

echo [5/6] Installing Playwright browsers (if needed)...
playwright install chromium --with-deps >nul 2>&1

echo [6/6] Checking system requirements...
echo Checking Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Tesseract OCR not found in PATH
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo The system will use EasyOCR as fallback
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