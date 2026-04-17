@echo off
rem run_monitor.bat – Start the DDAS file-monitoring service
rem
rem  If the packaged DDAS-Monitor.exe is present (installed or portable),
rem  it is preferred. Otherwise the Python source is used as a fallback.

setlocal

set "SCRIPT_DIR=%~dp0"

rem ── Try compiled executable first ────────────────────────────────────────
if exist "%SCRIPT_DIR%DDAS-Monitor.exe" (
    echo [DDAS] Starting monitor (exe) ...
    start "" "%SCRIPT_DIR%DDAS-Monitor.exe" monitor
    goto :eof
)

rem ── Fallback: run from Python source ─────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Neither DDAS-Monitor.exe nor Python found.
    echo         Please install DDAS or Python 3.10+ first.
    pause
    exit /b 1
)

echo [DDAS] Starting monitor (Python source) ...
python "%SCRIPT_DIR%main.py" monitor

endlocal
