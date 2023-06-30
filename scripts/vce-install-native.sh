#!/usr/bin/env bash


# Bash strict mode (http://redsymbol.net/articles/unofficial-bash-strict-mode/):
set -euo pipefail
IFS=$'\n\t'

SCRIPTS_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# ^ from https://stackoverflow.com/a/246128/1018176
VCE_ROOT="$SCRIPTS_ROOT/../"

# --- check dependencies ---
if [ -z ${__omnetpp_root_dir+x} ]; then
    echo "Variable __omnetpp_root_dir is not set."
    echo "This would typically be done by OMNeT++'s 'setenv' script."
    exit 1
else
    echo "OMNeT++ path: $__omnetpp_root_dir"
fi
if [ -z ${VEINS_ROOT+x} ]; then
    echo "Variable VEINS_ROOT is not set."
    echo "The 'setenv' script of Veins does not provide this itself, so please set it manually before running this script."
    exit 1
else
    echo "Veins path: $VEINS_ROOT"
fi
if ! command -v poetry &> /dev/null; then
    echo "Could not find an installation of Poetry."
    echo "Poetry is needed to manage the virtualenvs of Python subprojects."
    exit 1
fi


# --- evi ---
echo
echo "Installing evi/"
echo
cd $VCE_ROOT/evi
poetry install
#     &&
#     poetry run bash -c \"cd $VCE_ROOT/evi-asm-protocol && python setup.py build && python setup.py install\" &&
#     cd $VCE_ROOT/evi &&
#     poetry install
# "
# ^ Workaround for evi-asm-protocol, which as of now can't easily be installed with Poetry:
# We expect the first `poetry install` to set up the virtual environment,
# but possibly fail when trying to install veins-evi.
# The second `poetry install` should succeed.
# Status 2022-11-23: Seems to not be necessary anymore?


# --- veins-evi ---
echo
echo "Installing veins-evi/"
echo
cd $VCE_ROOT/veins-evi
./configure --veins $VEINS_ROOT
make -j$(nproc)


# --- bike-interface ---
echo
echo "Installing bike-interface/bicycle-model/bikeToEvi/"
echo
cd $VCE_ROOT/bike-interface/bicycle-model/bikeToEvi
poetry install
# For the Tacx ANT+ dongle to work, drivers will still have to
# be installed manually with root privileges.
# Please read the VCE documentation page on the Bicycle Interface for details.

# TODO: esp32 dependencies?
