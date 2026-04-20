@echo off
echo STARTING
where python
if %ERRORLEVEL% NEQ 0 (
    echo PYTHON MISSING
    exit /b 1
)
echo PYTHON FOUND
if not exist ".venv\Scripts\activate.bat" (
    echo VENV MISSING
)
echo DONE
