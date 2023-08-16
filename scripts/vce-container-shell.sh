#!/usr/bin/env bash

# Enters an interactive shell in the vce-container.sif, if already downloaded.
# Using this script instead of plain `apptainer shell vce-container.sif` has the benefit that the OMNeT++ IDE should also work.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# We need some writable directory outside the container for the OMNeT++ IDE to store its error.log file:
OMNETPP_IDE_LOG=$HOME/omnetpp/log
mkdir -p $OMNETPP_IDE_LOG

CONTAINER=$SCRIPT_DIR/../vce-container.sif
if [[ ! -f "$CONTAINER" ]]; then
    echo "Container image does not exist in the expected location ($CONTAINER)."
    echo "Did you run vce-install-container.sh yet?"
    exit 1
fi

apptainer shell --bind $OMNETPP_IDE_LOG:/log $CONTAINER
