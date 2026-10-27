@echo off
chcp 65001 >nul
set PYTHONUTF8=1
title Yandex Music Export
cd /d "%~dp0"

echo ============================================================
echo          YANDEX MUSIC EXPORT
echo ============================================================
echo.

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

:MENU
cls
echo ============================================================
echo  MENU:
echo ============================================================
echo  [1] Export from Yandex Music (JSON)
echo  [2] Convert JSON to TXT
echo  [3] Import to Spotify
echo  [0] Exit
echo ============================================================
echo.

set /p choice=Your choice (0-3): 

if "%choice%"=="1" (
    python export_yandex.py
    pause
    goto MENU
)
if "%choice%"=="2" (
    python convert_to_txt.py
    pause
    goto MENU
)
if "%choice%"=="3" (
    python import_to_spotify.py
    pause
    goto MENU
)
if "%choice%"=="0" goto END

echo Invalid choice. Try again.
pause
goto MENU

:END
echo.
echo Exiting...
pause
