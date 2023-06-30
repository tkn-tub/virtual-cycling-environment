#!/bin/bash

# create python virtual environment
python3 -mvenv .venv

# enter virtual environment
source .venv/bin/activate

# install / update installation tools
python -mpip install --upgrade pip wheel

# install requirements / libraries for evi
# includes installation of evi in live/editable mode
python -mpip install -r requirements.txt
python -mpip install -e .
