@echo off
cd /d "%~dp0"

echo ============================================
echo   AERO RECON-3D — Local Application Launcher
echo ============================================
echo.

REM --- Check dist exists ---
if not exist "dist\index.html" (
    echo [INFO] Compiled frontend not found. Building project...
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Build failed. Please check Node.js installation.
        pause
        exit /b 1
    )
    echo.
)

REM --- Kill any stale servers on port 4173 ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":4173 " ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)

REM --- Start a fresh server ---
echo [INFO] Starting web server on http://localhost:4173 ...
start /B python -m http.server 4173 --directory dist >nul 2>&1

REM --- Wait for server to become ready ---
echo [INFO] Waiting for server...
set RETRIES=0
:WAIT_LOOP
if %RETRIES% GEQ 10 (
    echo [ERROR] Server failed to start after 10 seconds.
    pause
    exit /b 1
)
timeout /t 1 /nobreak >nul
powershell -Command "try { (Invoke-WebRequest -Uri http://localhost:4173 -UseBasicParsing -TimeoutSec 2).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /a RETRIES+=1
    goto WAIT_LOOP
)

echo [INFO] Server is ready.
echo [INFO] Opening browser...
start http://localhost:4173

echo.
echo ============================================
echo   Application running at:
echo   http://localhost:4173
echo.
echo   Keep this window OPEN.
echo   Close this window to stop the server.
echo ============================================
echo.
pause >nul
