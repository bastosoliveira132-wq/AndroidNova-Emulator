@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "LOG=%CD%\build_windows.log"
set "EXITCODE=1"

echo ============================================================
echo AndroidNova Windows diagnostic build
echo ============================================================
echo Working directory: %CD%
echo Log: %LOG%
echo.

echo AndroidNova diagnostic build started %DATE% %TIME%> "%LOG%"
echo Working directory: %CD%>> "%LOG%"

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python launcher ^(py^) was not found.
    echo [ERROR] Python launcher ^(py^) was not found.>> "%LOG%"
    goto :failed
)
py --version >> "%LOG%" 2>&1
if errorlevel 1 goto :failed
py --version

py -m PyInstaller --version >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller is not installed for this Python.
    goto :failed
)
py -m PyInstaller --version

echo.
echo [1/3] Running Windows build script...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0packaging\build_windows.ps1"
if errorlevel 1 (
    echo [ERROR] Build failed. See %LOG%
    goto :failed
)

echo.
echo [2/3] Checking executables...
if not exist "%CD%\dist\AndroidNova\AndroidNova.exe" (
    echo [ERROR] Normal EXE was not created.
    goto :failed
)
if not exist "%CD%\dist\AndroidNova-debug\AndroidNova-debug.exe" (
    echo [ERROR] Diagnostic EXE was not created.
    goto :failed
)
echo Normal:      dist\AndroidNova\AndroidNova.exe
echo Diagnostic: dist\AndroidNova-debug\AndroidNova-debug.exe

echo.
echo [3/3] Launching diagnostic EXE. Its console must remain visible.
cd /d "%CD%\dist\AndroidNova-debug"
AndroidNova-debug.exe
set "EXITCODE=%ERRORLEVEL%"
echo.
echo AndroidNova-debug.exe exit code: %EXITCODE%
cd /d "%~dp0"
echo Diagnostic EXE exit code: %EXITCODE%>> "%LOG%"
if not "%EXITCODE%"=="0" (
    echo [ERROR] Diagnostic EXE exited with a non-zero code.
    goto :failed
)

echo.
echo Diagnostic run completed. Check androidnova.log beside the EXE if needed.
echo Build log: %LOG%
goto :done

:failed
echo.
echo ============================================================
echo DIAGNOSTIC FAILED - keep this window open and inspect the log.
echo ============================================================
set "EXITCODE=1"

:done
pause
exit /b %EXITCODE%
