#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

sudo apptainer build "$SCRIPT_DIR/../vce-container.sif" "$SCRIPT_DIR/../vce-container.def"
