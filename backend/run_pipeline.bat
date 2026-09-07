@echo off
echo.
echo ============================================================
echo  AERO RECON-3D - Run Reconstruction Pipeline
echo ============================================================
echo.
if "%~1"=="" (
    echo Usage: run_pipeline.bat path\to\video.mp4 [job_id]
    echo.
    echo Example:
    echo   run_pipeline.bat data\samples\test_drone.mp4 my_test_job
    exit /b 1
)
cd /d "%~dp0"
set VIDEO=%~1
set JOB=%~2
if "%JOB%"=="" (
    python -m app.pipeline.runner --video "%VIDEO%"
) else (
    python -m app.pipeline.runner --video "%VIDEO%" --job "%JOB%"
)
