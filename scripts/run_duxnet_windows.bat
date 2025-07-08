@echo off
setlocal enabledelayedexpansion

echo ========================================
echo           DuxNet Windows Launcher
echo ========================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo Project root: %PROJECT_ROOT%
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.7+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: %PYTHON_VERSION%
echo.

REM Check if pip is available
echo Checking pip installation...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: pip not found. Installing pip...
    python -m ensurepip --upgrade
)

REM Check for requirements.txt and install dependencies
if exist "%PROJECT_ROOT%\requirements.txt" (
    echo Installing/updating dependencies...
    python -m pip install -r "%PROJECT_ROOT%\requirements.txt"
    if errorlevel 1 (
        echo WARNING: Failed to install some dependencies
        echo Continuing anyway...
    )
    echo.
)

REM Check if the launcher script exists
if not exist "%SCRIPT_DIR%duxnet_launcher_cross_platform.py" (
    echo ERROR: Launcher script not found!
    echo Expected: %SCRIPT_DIR%duxnet_launcher_cross_platform.py
    echo.
    echo Please make sure you downloaded the complete release
    pause
    exit /b 1
)

echo Starting DuxNet services...
echo ========================================
echo.

REM Change to the scripts directory and run the launcher
cd /d "%SCRIPT_DIR%"
python duxnet_launcher_cross_platform.py

set EXIT_CODE=%errorlevel%

if %EXIT_CODE% neq 0 (
    echo.
    echo ========================================
    echo ERROR: DuxNet services failed to start
    echo ========================================
    echo.
    echo Exit code: %EXIT_CODE%
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure all dependencies are installed
    echo 2. Check if ports 8000-8010 are available
    echo 3. Try running individual services manually
    echo 4. Check the error messages above
    echo.
    echo For help, visit: https://github.com/ducks-github/DuxNet/issues
    echo.
) else (
    echo.
    echo ========================================
    echo DuxNet services stopped successfully
    echo ========================================
    echo.
)

echo Press any key to exit...
pause >nul 