#!/bin/bash

# sudo apt update
# sudo apt-get update
# sudo apt install -y python3
# sudo apt install -y python3-venv


# create virtual environment for python if not created
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
