@echo off
echo ================================================
echo    Poker Advisory System - Basic Windows Setup
echo ================================================
echo.
echo This script installs core dependencies without OpenSpiel
echo (OpenSpiel provides advanced GTO but requires Visual Studio Build Tools)
echo.

REM Check administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Running without administrator privileges
    echo Some installations may require elevated permissions
    echo.
)

echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo.
    echo Please install Python 3.8+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

python -c "import sys; print(f'Python {sys.version}')"

echo [2/6] Creating virtual environment...
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

python -m venv venv
call venv\Scripts\activate.bat

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip

echo [4/6] Installing core dependencies...
echo Installing FastAPI and web framework...
pip install fastapi uvicorn pydantic python-multipart websockets requests

echo Installing computer vision libraries...
pip install opencv-python pillow numpy pandas scikit-learn joblib

echo Installing OCR engines...
pip install pytesseract easyocr

echo Installing screen capture and utilities...
pip install mss pyautogui imagehash hnswlib trafilatura

echo Installing testing framework...
pip install pytest pytest-asyncio nest-asyncio

echo [5/6] Checking external dependencies...
echo.
echo Checking Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Tesseract OCR not found
    echo.
    echo Please download and install Tesseract:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Installation instructions:
    echo 1. Download tesseract-ocr-w64-setup-v5.3.1.20230401.exe
    echo 2. Install to default location: C:\Program Files\Tesseract-OCR
    echo 3. Add to Windows PATH: C:\Program Files\Tesseract-OCR
    echo.
    echo The system will work with EasyOCR as fallback if Tesseract is unavailable
    echo.
) else (
    echo Tesseract OCR found and working
)

echo [6/6] Running system test...
echo Testing basic imports...
python -c "
import fastapi
import cv2
import numpy as np
import easyocr
print('✓ All core dependencies working')
"

if %errorlevel% neq 0 (
    echo ERROR: Some dependencies failed to import
    pause
    exit /b 1
)

echo.
echo ================================================
echo    Basic Setup Complete!
echo ================================================
echo.
echo IMPORTANT: This is the basic version without OpenSpiel GTO engine
echo.
echo The system includes:
echo ✓ Computer vision (OpenCV)
echo ✓ Dual OCR engines (EasyOCR + Tesseract) 
echo ✓ Screen capture (MSS)
echo ✓ Web interface (FastAPI)
echo ✓ Database with 6,757+ poker scenarios
echo.
echo Missing advanced features:
echo - OpenSpiel CFR solver (requires Visual Studio Build Tools)
echo - Advanced GTO computations
echo.
echo To start the poker advisory system:
echo   1. Double-click 'start_poker_advisor.bat'
echo   2. Or run 'quick_start.bat' for faster startup
echo.
echo System will be available at:
echo   - http://localhost:5000/unified
echo.
echo For full GTO features, install Visual Studio Build Tools first,
echo then run 'setup_windows_advanced.bat'
echo.
pause