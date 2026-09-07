@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   AERO RECON-3D - Local Application Launcher
echo ============================================
echo.

REM --- Check node_modules exists ---
if not exist "node_modules\" (
    echo [INFO] node_modules not found. Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Please check Node.js installation.
        pause
        exit /b 1
    )
    echo.
)

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

REM --- Check if server is already running on 4173 ---
powershell -Command "try { if ((Invoke-WebRequest -Uri http://localhost:4173 -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Server is already running on port 4173. Reusing it...
    start http://localhost:4173
    echo [INFO] Opened browser. Keep the existing server window open.
    pause
    exit /b 0
)

echo [INFO] Starting web server on http://localhost:4173 ...

REM --- Check Python ---
python --version >nul 2>&1
if not errorlevel 1 (
    start /B python -m http.server 4173 --directory dist >nul 2>&1
) else (
    echo [INFO] Python not found. Falling back to Node/Vite preview server...
    start /B npm run preview -- --port 4173 >nul 2>&1
)

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
powershell -Command "try { if ((Invoke-WebRequest -Uri http://localhost:4173 -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
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
