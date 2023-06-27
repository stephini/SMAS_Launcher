#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Run the .pyw script in the background
python3 launcher.pyw &

# Close the terminal window gracefully
disown -a && exit