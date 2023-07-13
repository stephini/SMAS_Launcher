@echo off

REM Install dependencies
rem python -m venv venv
rem venv\Scripts\activate.bat
pip install -r win.requirements.txt

REM Prompt for continuation
echo "Finished press any key to continue."
pause
