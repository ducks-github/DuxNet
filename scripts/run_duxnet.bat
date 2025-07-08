@echo off
echo ========================================
echo           DuxNet Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found. Starting DuxNet services...
echo.

REM Change to the scripts directory and run the launcher
cd /d "%~dp0"
python duxnet_launcher_cross_platform.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start DuxNet services
    echo Please check the error messages above
    echo.
    echo Troubleshooting:
    echo 1. Make sure all dependencies are installed: pip install -r requirements.txt
    echo 2. Check if all required files are present
    echo 3. Try running the launcher directly: python duxnet_launcher_cross_platform.py
)

echo.
echo Press any key to exit...
pause >nul 