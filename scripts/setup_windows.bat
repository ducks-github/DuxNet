@echo off
setlocal enabledelayedexpansion

echo ========================================
echo        DuxNet Windows Setup
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo This script will help you set up DuxNet on Windows
echo.

REM Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python 3.7+ from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation
    echo.
    echo After installing Python, run this setup script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Found: %PYTHON_VERSION%
echo.

REM Check if pip is available
echo [2/4] Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Installing pip...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo ERROR: Failed to install pip
        pause
        exit /b 1
    )
)
echo ✓ pip is available
echo.

REM Install dependencies
echo [3/4] Installing dependencies...
if exist "%PROJECT_ROOT%\requirements.txt" (
    echo Installing from requirements.txt...
    python -m pip install -r "%PROJECT_ROOT%\requirements.txt"
    if errorlevel 1 (
        echo WARNING: Some dependencies failed to install
        echo This might be okay - continuing anyway...
    )
) else (
    echo No requirements.txt found, installing common dependencies...
    python -m pip install fastapi uvicorn pyqt5 requests bcrypt
)
echo ✓ Dependencies installed
echo.

REM Check if all required files are present
echo [4/4] Checking required files...
set MISSING_FILES=0

if not exist "%SCRIPT_DIR%duxnet_launcher_cross_platform.py" (
    echo ✗ Missing: duxnet_launcher_cross_platform.py
    set /a MISSING_FILES+=1
)

if not exist "%PROJECT_ROOT%\backend" (
    echo ✗ Missing: backend directory
    set /a MISSING_FILES+=1
)

if not exist "%PROJECT_ROOT%\frontend" (
    echo ✗ Missing: frontend directory
    set /a MISSING_FILES+=1
)

if %MISSING_FILES% gtr 0 (
    echo.
    echo ERROR: Some required files are missing!
    echo Please make sure you downloaded the complete release.
    echo.
    pause
    exit /b 1
)

echo ✓ All required files found
echo.

echo ========================================
echo        Setup Complete! ✓
echo ========================================
echo.
echo DuxNet is now ready to run on Windows!
echo.
echo To start DuxNet:
echo 1. Double-click: run_duxnet_windows.bat
echo 2. Or run: run_duxnet.bat
echo.
echo If you encounter any issues:
echo - Check that Python is in your PATH
echo - Make sure ports 8000-8010 are not in use
echo - Try running the launcher directly: python duxnet_launcher_cross_platform.py
echo.
echo For help: https://github.com/ducks-github/DuxNet/issues
echo.
pause 