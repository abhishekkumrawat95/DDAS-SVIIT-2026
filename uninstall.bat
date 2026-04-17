@echo off
rem uninstall.bat – Remove DDAS from this machine
rem
rem  1. If the NSIS uninstaller is present (installed via Setup.exe), run it.
rem  2. Otherwise remove the Windows service and pip packages.

setlocal

echo.
echo  ╔════════════════════════════════════════╗
echo  ║   DDAS – Uninstall                     ║
echo  ╚════════════════════════════════════════╝
echo.

set "SCRIPT_DIR=%~dp0"
set "DEFAULT_INSTALL=%ProgramFiles%\DDAS"

rem ── Option 1: Use the NSIS uninstaller ───────────────────────────────────
if exist "%DEFAULT_INSTALL%\Uninstall DDAS.exe" (
    echo [INFO] Running NSIS uninstaller ...
    start /wait "" "%DEFAULT_INSTALL%\Uninstall DDAS.exe"
    echo [OK]  DDAS uninstalled.
    goto :done
)

rem ── Option 2: Manual cleanup (dev / portable install) ────────────────────
echo [INFO] NSIS uninstaller not found – performing manual cleanup.

rem Stop and remove Windows service if present
sc query DDASMonitor >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Stopping DDAS service ...
    sc stop DDASMonitor >nul 2>&1
    sc delete DDASMonitor >nul 2>&1
    echo [OK]  Service removed.
)

rem Remove data directory (optional – ask user)
set /p REMOVE_DATA="Remove DDAS database and logs from %%PROGRAMDATA%%\DDAS? [y/N] "
if /i "%REMOVE_DATA%"=="y" (
    rmdir /s /q "%PROGRAMDATA%\DDAS" 2>nul
    echo [OK]  Data directory removed.
) else (
    echo [INFO] Data directory preserved.
)

echo.
echo [OK]  DDAS has been removed from this system.

:done
pause
endlocal
