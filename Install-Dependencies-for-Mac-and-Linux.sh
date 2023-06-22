#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Prompt for continuation
read -rsp "Finished. Press any key to continue." -n1 key
echo