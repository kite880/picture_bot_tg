@echo off
REM Start Picture Bot script for Windows

setlocal enabledelayedexpansion

echo.
echo ===============================================================
echo   Picture Bot - Telegram Bot Launcher
echo ===============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo Checking Python version...
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install/Update dependencies
echo Installing dependencies...
pip install --quiet -r requirements.txt
echo Dependencies installed
echo.

REM Check configuration
echo Checking configuration...
python check_config.py
echo.

REM Run the bot
echo Starting Picture Bot...
echo Press Ctrl+C to stop the bot
echo.

python main.py

pause
