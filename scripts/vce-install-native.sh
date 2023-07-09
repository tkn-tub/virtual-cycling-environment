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
fi
echo "OMNeT++ path: $__omnetpp_root_dir"
if [ -z ${VEINS_ROOT+x} ]; then
    echo "Variable VEINS_ROOT is not set."
    echo "The 'setenv' script of Veins does not provide this itself, so please set it manually before running this script."
    exit 1
fi
echo "Veins path: $VEINS_ROOT"
if [ -z ${GODOT+x} ]; then
    if ! command -v godot &> /dev/null; then
        echo "Could not find an installation of Godot."
        echo "Export the variable GODOT to specify a path."
        exit 1
    fi
    GODOT=godot
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
cd "$VCE_ROOT/veins-evi"
./configure --veins "$VEINS_ROOT"
make -j$(nproc)


# --- bike-interface ---
echo
echo "Installing bike-interface/bicycle-model/bikeToEvi/"
echo
cd "$VCE_ROOT/bike-interface/bicycle-model/bikeToEvi"
poetry install
# For the Tacx ANT+ dongle to work, drivers will still have to
# be installed manually with root privileges.
# Please read the VCE documentation page on the Bicycle Interface for details.


# --- 3denv ---
echo
echo "Installing 3denv/"
echo
mkdir -p "$HOME/.local/share/godot/templates"
godot_version=$($GODOT --version | cut -d '.' -f 1-3)
godot_stage=$($GODOT --version | cut -d '.' -f 4)  # e.g., "stable"
godot_templates_tpz=$HOME/.local/share/godot/templates.tpz
godot_templates_dir=$HOME/.local/share/godot/templates/${godot_version}.${godot_stage}.mono
if [ -d "$godot_templates_dir" ]; then
    echo "Skipping download of Godot export templates, directory already exists: $godot_templates_dir."
else
    echo "Downloading Godot export templates…"
    wget "https://github.com/godotengine/godot/releases/download/${godot_version}-${godot_stage}/Godot_v${godot_version}-${godot_stage}_mono_export_templates.tpz" \
        -O "$godot_templates_tpz"
    unzip -u "$godot_templates_tpz" -d "$HOME/.local/share/godot/templates"
    # templates/ subdir is included in archive, but doesn't have the required subdir with the correct name itself -> rename:
    mv "$HOME/.local/share/godot/templates/templates" "$godot_templates_dir"
    rm "$godot_templates_tpz"
fi
echo "Exporting 3DEnv to $VCE_ROOT/build/…"
$GODOT --no-window --export "Linux/X11" "build/3denv.x86_64" "$VCE_ROOT/3denv/project.godot"


# TODO: esp32 dependencies?
