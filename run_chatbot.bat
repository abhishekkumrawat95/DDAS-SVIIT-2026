@echo off
rem run_chatbot.bat – Start the DDAS interactive chatbot (console window)

setlocal

set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%DDAS-Chatbot.exe" (
    echo [DDAS] Starting chatbot (exe) ...
    "%SCRIPT_DIR%DDAS-Chatbot.exe"
    goto :eof
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Neither DDAS-Chatbot.exe nor Python found.
    pause
    exit /b 1
)

echo [DDAS] Starting chatbot (Python source) ...
python "%SCRIPT_DIR%chatbot_cli.py"

endlocal
