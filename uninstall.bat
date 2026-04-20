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

rem Kill any running DDAS processes
echo [INFO] Stopping any running DDAS processes ...
taskkill /F /IM DDAS-Monitor.exe   /T >nul 2>&1
taskkill /F /IM DDAS-Launcher.exe  /T >nul 2>&1
taskkill /F /IM DDAS-Dashboard.exe /T >nul 2>&1
taskkill /F /IM DDAS-Chatbot.exe   /T >nul 2>&1
echo [OK]  Processes terminated (if any were running).

rem Stop and remove Windows service if present
sc query DDASMonitor >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Stopping DDAS service ...
    sc stop DDASMonitor >nul 2>&1
    timeout /t 3 /nobreak >nul
    sc delete DDASMonitor >nul 2>&1
    echo [OK]  Service removed.
)

rem Remove auto-start registry entry (added by manual / portable install)
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "DDASMonitor" /f >nul 2>&1

rem Remove Start Menu shortcuts (all-users)
set "START_MENU=%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\DDAS"
if exist "%START_MENU%" (
    rmdir /s /q "%START_MENU%" 2>nul
    echo [OK]  Start Menu shortcuts removed.
)

rem Remove Desktop shortcut
if exist "%PUBLIC%\Desktop\DDAS Launcher.lnk"   del /f /q "%PUBLIC%\Desktop\DDAS Launcher.lnk"   2>nul
if exist "%USERPROFILE%\Desktop\DDAS Launcher.lnk" del /f /q "%USERPROFILE%\Desktop\DDAS Launcher.lnk" 2>nul

rem Remove the installation directory (C:\Program Files\DDAS or wherever it lives)
if exist "%DEFAULT_INSTALL%" (
    echo [INFO] Removing installation directory: %DEFAULT_INSTALL%
    rmdir /s /q "%DEFAULT_INSTALL%" 2>nul
    if exist "%DEFAULT_INSTALL%" (
        echo [WARN] Could not fully remove %DEFAULT_INSTALL%. Close any open files and retry.
    ) else (
        echo [OK]  Installation directory removed.
    )
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
