@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1 || (echo Python 3.11+ is required.& pause& exit /b 1)
py -3 scripts\run.py
if errorlevel 1 pause
