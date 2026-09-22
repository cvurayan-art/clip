@echo off
setlocal EnableDelayedExpansion
title AI Video Clipper - Launcher

echo ======================================================================
echo                  AI VIDEO CLIPPER - LOCAL LAUNCHER
echo ======================================================================
echo.

cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv" (
    echo [INFO] Virtual environment not found. Running installer first...
    call install.bat
)

:: Activate Python environment
call .venv\Scripts\activate.bat

:: Start FastAPI Backend Server
echo [1/2] Starting Backend API Server (http://127.0.0.1:8000)...
start "AI Clipper - Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && call ..\.venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Start Next.js Frontend Server
echo [2/2] Starting Frontend UI Server (http://localhost:3000)...
start "AI Clipper - Frontend (Next.js)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: Wait 3 seconds for servers to initialize
timeout /t 3 /nobreak >nul

:: Launch default web browser
echo Launching application in browser...
start http://localhost:3000

echo.
echo ======================================================================
echo   AI Clipper is now running!
echo   Frontend: http://localhost:3000
echo   Backend:  http://127.0.0.1:8000
echo.
echo   Keep the two background terminal windows open while using the app.
echo   To stop the application, simply close the terminal windows.
echo ======================================================================
echo.
pause
