@echo off
title ChainFLIP Multichain Startup
color 0A

echo ===============================================
echo    ChainFLIP Multichain Authentication System
echo    Starting on Windows with E: Drive MongoDB
echo ===============================================
echo.

echo [1/6] Creating MongoDB directory on E: drive...
if not exist "E:\data\db" (
    mkdir E:\data\db
    echo     ✓ Created E:\data\db
) else (
    echo     ✓ E:\data\db already exists
)
echo.

echo [2/6] Starting MongoDB in new window...
start "ChainFLIP-MongoDB" cmd /k "echo Starting MongoDB on E:\data\db && mongod --dbpath E:\data\db"
echo     ✓ MongoDB starting in separate window...
echo.

echo [3/6] Waiting 8 seconds for MongoDB to initialize...
timeout /t 8 /nobreak >nul
echo     ✓ MongoDB should be ready
echo.

echo [4/6] Starting ChainFLIP Backend...
start "ChainFLIP-Backend" cmd /k "title ChainFLIP Backend && cd /d %~dp0backend && echo Starting FastAPI Backend... && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
echo     ✓ Backend starting in separate window...
echo.

echo [5/6] Waiting 12 seconds for backend to initialize...
timeout /t 12 /nobreak >nul
echo     ✓ Backend should be ready
echo.

echo [6/6] Initializing Admin Account...
echo     Attempting to create admin account...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8001/api/auth/admin/initialize' -Method Get; Write-Host '     ✓ Admin Account Response:'; Write-Host \"       Email: $($response.admin_email)\"; Write-Host \"       Password: $($response.admin_password)\"; Write-Host \"       Message: $($response.message)\" } catch { Write-Host '     ✗ Failed to initialize admin. Backend may not be ready yet.' }"
echo.

echo ===============================================
echo    ChainFLIP Services Started Successfully!
echo ===============================================
echo.
echo MongoDB:    Running on E:\data\db
echo Backend:     http://localhost:8001
echo API Docs:    http://localhost:8001/docs
echo Admin:       admin@chainflip.com / ChainFLIP2025!
echo.
echo ===============================================
echo    Optional: Start Frontend
echo ===============================================
echo.
set /p frontend="Do you want to start the React frontend? (y/n): "
if /i "%frontend%"=="y" (
    echo.
    echo Starting React Frontend...
    start "ChainFLIP-Frontend" cmd /k "title ChainFLIP Frontend && cd /d %~dp0frontend && echo Starting React Frontend... && npm start"
    echo     ✓ Frontend starting in separate window...
    echo     ✓ Frontend will be available at: http://localhost:3000
)

echo.
echo ===============================================
echo    Startup Complete!
echo ===============================================
echo.
echo All services are running in separate windows.
echo You can close this window safely.
echo.
echo To test the system:
echo 1. Open browser to: http://localhost:8001/docs
echo 2. Test admin login with: admin@chainflip.com / ChainFLIP2025!
echo 3. Register new users and approve them via admin dashboard
echo.
