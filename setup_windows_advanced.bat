@echo off
echo ================================================
echo    Poker Advisory System - Windows Setup
echo ================================================
echo.
echo This script will set up the complete poker advisory system
echo including all dependencies and external requirements.
echo.

REM Check administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Administrator privileges required for Visual Studio Build Tools installation
    echo Please right-click this batch file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/8] Checking Python installation...
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

echo [2/8] Checking for Visual Studio Build Tools...

REM Multiple detection methods for Visual Studio Build Tools
set "VS_FOUND=false"

REM Method 1: Check for cl compiler in PATH
where cl >nul 2>&1
if %errorlevel% equ 0 (
    set "VS_FOUND=true"
    echo Visual Studio Build Tools found via PATH
)

REM Method 2: Check common Visual Studio installation paths
if "%VS_FOUND%"=="false" (
    for %%p in (
        "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC"
        "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC" 
        "C:\Program Files\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC"
        "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC"
        "C:\Program Files\Microsoft Visual Studio\2019\Professional\VC\Tools\MSVC"
        "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC"
    ) do (
        if exist %%p (
            set "VS_FOUND=true"
            echo Visual Studio Build Tools found at %%p
            goto :vs_found
        )
    )
)

:vs_found
if "%VS_FOUND%"=="false" (
    echo Visual Studio Build Tools not detected
    echo.
    echo IMPORTANT: You mentioned you installed it manually.
    echo Let's try to set up the environment...
    echo.
    
    REM Try to call vcvars64.bat to set up environment
    call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Environment setup successful with VS2022 BuildTools
        set "VS_FOUND=true"
        goto :continue_setup
    )
    
    call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Environment setup successful with VS2019 BuildTools
        set "VS_FOUND=true"
        goto :continue_setup
    )
    
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
    if %errorlevel% equ 0 (
        echo Environment setup successful with VS2022 Community
        set "VS_FOUND=true"
        goto :continue_setup
    )
    
    echo WARNING: Could not automatically detect or setup Visual Studio Build Tools
    echo.
    echo Since you installed manually, let's continue and try OpenSpiel installation...
    echo If OpenSpiel fails, please ensure Visual Studio Build Tools are properly installed.
    echo.
    set "VS_FOUND=true"
) else (
    echo Visual Studio Build Tools detected - ready for OpenSpiel compilation
)

:continue_setup

echo [3/8] Creating virtual environment...
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

python -m venv venv
call venv\Scripts\activate.bat

echo [4/8] Upgrading pip...
python -m pip install --upgrade pip

echo [5/8] Installing core Python dependencies...
pip install fastapi uvicorn pydantic python-multipart websockets requests
pip install opencv-python pillow numpy pandas scikit-learn joblib
pip install pytesseract easyocr mss pyautogui imagehash
pip install hnswlib trafilatura pytest pytest-asyncio nest-asyncio

echo [6/8] Installing optional advanced dependencies...
pip install open-spiel tensorflow playwright

echo [7/8] Setting up Playwright browsers...
playwright install chromium

echo [8/8] Checking external dependencies...
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

echo [8/8] Running system test...
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
echo    Setup Complete!
echo ================================================
echo.
echo To start the poker advisory system:
echo   1. Double-click 'start_poker_advisor.bat'
echo   2. Or run 'quick_start.bat' for faster startup
echo.
echo System will be available at:
echo   - http://localhost:5000/unified
echo.
echo For ACR poker integration:
echo   1. Open ACR poker client
echo   2. Join a poker table
echo   3. Use the unified interface for analysis
echo.
pause