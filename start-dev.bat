@echo off
title Haven Pet Full-Stack Dev Server
cd /d "%~dp0"
echo ========================================================
echo   Starting Haven Pet (FastAPI :8000 + Vite :5173)
echo ========================================================
npm run dev
pause

