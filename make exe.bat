@echo off
pyinstaller --onefile --add-data "assets;assets" --icon=assets/icon.ico --clean launcher.pyw
echo "Finished press any key to continue."
pause