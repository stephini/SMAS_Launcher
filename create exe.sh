#!/bin/bash

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r pipinstaller
pyinstaller --onefile --add-data "assets;assets" --icon=assets/icon.icns --clean launcher.pyw

# Prompt for continuation
read -rsp "Finished. Press any key to continue." -n1 key
echo