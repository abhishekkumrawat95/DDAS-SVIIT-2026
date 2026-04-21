@echo off
rem =========================================================================
rem  build.bat - One-click build script for DDAS Windows installer
rem
rem  What it does:
rem    1. Activates or creates a Python virtual environment
rem    2. Installs / updates all dependencies
rem    3. Runs build_installer.py (which invokes PyInstaller then NSIS)
rem    4. Prints the artefacts produced in dist\
rem
rem  Requirements:
rem    * Python 3.10+ on PATH   (python --version)
rem    * NSIS 3.x on PATH       (makensis --version)  [optional - for Setup.exe]
rem    * Internet access for pip (first run only)
rem =========================================================================

setlocal enabledelayedexpansion

echo.
echo  ========================================
echo    DDAS - Windows Installer Build Script
echo    Data Download Duplication Alert System
echo  ========================================
echo.

rem -- Locate Python --------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

python --version >nul 2>&1
echo [INFO]  Python version detected (use python --version to check).

rem -- Create / activate virtual environment ---------------------------
if not exist ".venv\Scripts\activate.bat" (
    echo [INFO]  Creating virtual environment (.venv) ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
echo [INFO]  Virtual environment activated.

rem -- Install / update dependencies -------------------------------------
echo [INFO]  Installing dependencies from requirements.txt ...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)
echo [OK]    Dependencies installed.

rem -- Run Python build script -------------------------------------------
echo [INFO]  Starting build ...
python build_installer.py %*
if errorlevel 1 (
    echo [ERROR] Build failed. Check the output above for details.
    pause
    exit /b 1
)

rem -- Summary -------------------------------------------------------
echo.
echo  Build complete! Artefacts in dist\
echo  ================================================
if exist "dist\DDAS-Setup.exe"    echo    * dist\DDAS-Setup.exe    (Windows installer)
if exist "dist\DDAS-Portable.zip" echo    * dist\DDAS-Portable.zip (Portable archive)
if exist "dist\DDAS\"             echo    * dist\DDAS\             (Extracted folder)
echo.

pause
endlocal
