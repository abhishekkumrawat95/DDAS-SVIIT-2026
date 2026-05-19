@echo off
setlocal enabledelayedexpansion

echo.
echo  ========================================
echo    DDAS - Windows Installer Build Script
echo    Data Download Duplication Alert System
echo  ========================================
echo.

where python >nul 2>&1
if errorlevel 1 goto :error_no_python

echo [INFO]  Python detected.

if exist ".venv\Scripts\activate.bat" goto :activate_venv

echo [INFO]  Creating virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 goto :error_venv_create

:activate_venv
call .venv\Scripts\activate.bat
echo [INFO]  Virtual environment activated.

echo [INFO]  Installing dependencies from requirements.txt...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 goto :error_pip

echo [OK]    Dependencies installed.

echo [INFO]  Starting build...
python build_installer.py %*
if errorlevel 1 goto :error_build

echo.
echo  Build complete! Artifacts in dist\
echo  ================================================
if exist "dist\DDAS-Setup.exe" echo    * dist\DDAS-Setup.exe (Windows installer)
if exist "dist\DDAS-Portable.zip" echo    * dist\DDAS-Portable.zip (Portable archive)
if exist "dist\DDAS\" echo    * dist\DDAS\ (Extracted folder)
echo.

pause
goto :eof

:error_no_python
echo [ERROR] Python not found. Install Python 3.10+ and add to PATH.
pause
exit /b 1

:error_venv_create
echo [ERROR] Failed to create virtual environment.
pause
exit /b 1

:error_pip
echo [ERROR] pip install failed.
pause
exit /b 1

:error_build
echo [ERROR] Build failed. Check output above.
pause
exit /b 1
