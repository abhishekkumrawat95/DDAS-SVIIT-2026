@echo off
echo Testing...
if not exist ".venv\Scripts\activate.bat" (
    echo Hello
)
echo Done.
