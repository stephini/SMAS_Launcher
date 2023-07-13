@echo off

REM Activate the virtual environment
rem call venv\Scripts\activate.bat

REM Run the .pyw script in the background
start "" python launcher.pyw

pause
REM Close the terminal window gracefully
#exit
