@echo off
echo ================================================
echo    Visual Studio Build Tools Installer
echo ================================================
echo.
echo This script will download and install Visual Studio Build Tools
echo Required for OpenSpiel (advanced GTO features)
echo.

REM Check administrator privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Administrator privileges required
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Checking if Visual Studio Build Tools already installed...

REM Multiple detection methods
set "VS_FOUND=false"

REM Check for cl compiler in PATH
where cl >nul 2>&1
if %errorlevel% equ 0 (
    set "VS_FOUND=true"
    echo Visual Studio Build Tools found via PATH
)

REM Check common installation paths
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
            goto :already_installed
        )
    )
)

if "%VS_FOUND%"=="true" (
    :already_installed
    echo Visual Studio Build Tools already installed!
    echo You can now run setup_windows_advanced.bat
    pause
    exit /b 0
)

echo [1/3] Downloading Visual Studio Build Tools...
echo This may take a few minutes depending on internet speed...
powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vs_buildtools.exe' -OutFile 'vs_buildtools.exe'"

if not exist "vs_buildtools.exe" (
    echo ERROR: Download failed
    echo Please check internet connection and try again
    pause
    exit /b 1
)

echo [2/3] Installing Visual Studio Build Tools...
echo This will take 10-20 minutes - please be patient...
echo Installing C++ build tools and Windows SDK...
vs_buildtools.exe --quiet --wait --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK.19041

if %errorlevel% neq 0 (
    echo WARNING: Installation may have failed
    echo Check if Visual Studio Installer opened - complete installation manually
    echo.
    pause
)

echo [3/3] Cleaning up...
del vs_buildtools.exe

echo.
echo ================================================
echo    Installation Complete!
echo ================================================
echo.
echo Visual Studio Build Tools should now be installed.
echo.
echo Next steps:
echo 1. Restart your computer (recommended)
echo 2. Run setup_windows_advanced.bat to install OpenSpiel
echo.
echo If installation failed, manually download from:
echo https://visualstudio.microsoft.com/downloads/
echo.
pause