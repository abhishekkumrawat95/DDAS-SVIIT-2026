@echo off
rem install.bat – Quick DDAS installer helper
rem
rem  Runs the NSIS-generated DDAS-Setup.exe if it exists in the same
rem  directory, otherwise falls back to running the Python source
rem  in-place by creating a desktop shortcut to launcher.py.

setlocal

set "SCRIPT_DIR=%~dp0"

echo.
echo  ╔════════════════════════════════════════╗
echo  ║   DDAS – Quick Install                 ║
echo  ╚════════════════════════════════════════╝
echo.

rem ── Option 1: Run the NSIS installer (preferred) ─────────────────────────
if exist "%SCRIPT_DIR%DDAS-Setup.exe" (
    echo [INFO] Found DDAS-Setup.exe – launching installer wizard ...
    start /wait "" "%SCRIPT_DIR%DDAS-Setup.exe"
    echo [OK]  Installation complete.
    goto :done
)

rem ── Option 2: Install Python dependencies only (dev/portable mode) ────────
echo [INFO] DDAS-Setup.exe not found. Installing Python dependencies ...

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.10+ is required but was not found on PATH.
    echo         Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

pip install -r "%SCRIPT_DIR%requirements.txt"
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [OK]  Dependencies installed successfully.
echo [OK]  Run launcher.py to start DDAS:
echo       python "%SCRIPT_DIR%launcher.py"
echo.

:done
pause
endlocal
