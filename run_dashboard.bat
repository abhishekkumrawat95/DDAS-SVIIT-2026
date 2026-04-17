@echo off
rem run_dashboard.bat – Launch the DDAS Tkinter dashboard

setlocal

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%DDAS-Dashboard.exe" (
    echo [DDAS] Opening dashboard (exe) ...
    start "" "%SCRIPT_DIR%DDAS-Dashboard.exe"
    goto :eof
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Neither DDAS-Dashboard.exe nor Python found.
    pause
    exit /b 1
)

echo [DDAS] Opening dashboard (Python source) ...
start "" python "%SCRIPT_DIR%ddas_dashboard.py"

endlocal
