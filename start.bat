@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
title Export Yandex Music
cd /d "%~dp0"

echo ============================================================
echo          STARTING YANDEX MUSIC EXPORT
echo ============================================================
echo.

REM Check if venv exists, if not create it
if not exist "venv\Scripts\activate.bat" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    echo [SETUP] Installing dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
)

call venv\Scripts\activate.bat

echo [OK] Virtual environment activated
echo.

REM Run Python in the same console window (interactive mode)
python export_yandex.py

pause
