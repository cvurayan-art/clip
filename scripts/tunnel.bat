@echo off
setlocal EnableDelayedExpansion
title AI Clipper - Cloudflare Remote Access Tunnel

echo ======================================================================
echo          AI CLIPPER - FREE REMOTE TUNNEL (FOR VERCEL ACCESS)
echo ======================================================================
echo.
echo This starts a free, encrypted Cloudflare Tunnel to expose your local
echo FastAPI backend (port 8000) so you can connect from Vercel or your laptop!
echo.
echo No account or credit card required.
echo.

:: Try npx cloudflared or local cloudflared
where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting Cloudflare Tunnel...
    cloudflared tunnel --url http://127.0.0.1:8000
) else (
    echo Cloudflared executable not found in PATH. Using npx...
    npx -y cloudflared tunnel --url http://127.0.0.1:8000
)

pause
