@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Prefer the normal python command because Python 3.13 may be installed
rem without the Windows Python Launcher (py.exe). Fall back to py -3.
set "PYTHON_CMD="
where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (
    where py >nul 2>&1 && set "PYTHON_CMD=py -3"
)

if not defined PYTHON_CMD (
    echo Python 3.11 or newer is required, but no usable Python command was found.
    echo Install Python 3.13 and enable "Add Python to PATH" during installation.
    pause
    exit /b 1
)

rem Validate the interpreter itself instead of testing for the presence of py.exe.
%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo Python 3.11 or newer is required.
    echo Detected interpreter:
    %PYTHON_CMD% --version
    pause
    exit /b 1
)

%PYTHON_CMD% --version
%PYTHON_CMD% scripts\run.py
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo.
    echo AndroidNova exited with code %EXIT_CODE%.
    pause
)
exit /b %EXIT_CODE%
