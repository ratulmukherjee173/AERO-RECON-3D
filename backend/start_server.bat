@echo off
echo.
echo ============================================================
echo  AERO RECON-3D Backend Server
echo ============================================================
echo.
cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
