@echo off
setlocal EnableDelayedExpansion
title AI Video Clipper - Installation & Dependency Setup

echo ======================================================================
echo           AI VIDEO CLIPPER - WINDOWS AUTOMATED INSTALLER
echo ======================================================================
echo.

cd /d "%~dp0"

:: 1. Check Python
echo [1/6] Checking Python installation...
set "PY_CMD="
python --version >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD (
    py -0 >nul 2>&1 && set "PY_CMD=py"
)

if not defined PY_CMD (
    echo [MISSING] Python is not installed or not in PATH!
    echo Please install Python 3.10 or 3.11 from https://www.python.org/downloads/
    echo IMPORTANT: Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('%PY_CMD% --version 2^>^&1') do echo [OK] Found: %%v
)

:: 2. Check Node.js and NPM
echo.
echo [2/6] Checking Node.js and NPM...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [MISSING] Node.js is not installed or not in PATH!
    echo Please install Node.js LTS (v18 or v20) from https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%v in ('node --version') do echo [OK] Node.js: %%v
    for /f "tokens=*" %%v in ('npm --version') do echo [OK] NPM: v%%v
)

:: 3. Check FFmpeg
echo.
echo [3/6] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg is not found in PATH!
    echo Recommended: Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
    echo and add its bin folder to your system PATH.
    echo (You can also install via: winget install Gyan.FFmpeg)
    echo.
) else (
    echo [OK] FFmpeg is installed and accessible.
)

:: 4. Check Ollama
echo.
echo [4/6] Checking Ollama for local LLMs...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Ollama is not installed or not in PATH.
    echo You can install Ollama from https://ollama.ai/ to use local Qwen LLM.
    echo The app will automatically use its built-in local NLP engine if Ollama is not running.
) else (
    echo [OK] Ollama is installed. To pull recommended model, run: ollama pull qwen2.5:7b
)

:: 5. Create Python Virtual Environment & Install Requirements
echo.
echo [5/6] Setting up Python virtual environment (.venv)...
if not exist ".venv" (
    %PY_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Activating .venv and installing Python packages...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Some pip dependencies encountered warnings.
)

:: 6. Setup Frontend NPM Dependencies
echo.
echo [6/6] Installing Next.js frontend dependencies...
cd frontend
call npm install
cd ..

:: Ensure directories exist
if not exist "downloads" mkdir downloads
if not exist "output" mkdir output
if not exist "temp" mkdir temp
if not exist "models" mkdir models

echo.
echo ======================================================================
echo                  INSTALLATION COMPLETED SUCCESSFULLY!
echo ======================================================================
echo.
echo To launch the application at any time, run:
echo    start.bat
echo.
pause
