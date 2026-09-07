@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   AERO RECON-3D - Local Backend Server
echo ============================================
echo.

REM --- Check if Python is installed ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM --- Navigate to backend folder ---
if not exist "backend\app\main.py" (
    echo [ERROR] Backend folder or main.py not found!
    pause
    exit /b 1
)

REM --- Check if virtual environment exists ---
if not exist "venv_mesh\Scripts\activate.bat" (
    echo [INFO] Virtual environment 'venv_mesh' not found.
    echo Please make sure you have created the backend virtual environment and installed requirements.txt
    pause
    exit /b 1
)

REM --- Activate virtual environment and run Uvicorn ---
echo [INFO] Activating virtual environment...
call "venv_mesh\Scripts\activate.bat"

echo [INFO] Starting FastAPI Backend on http://127.0.0.1:8000 ...
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
