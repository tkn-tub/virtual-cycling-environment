#!/usr/bin/env bash


# Bash strict mode (http://redsymbol.net/articles/unofficial-bash-strict-mode/):
set -euo pipefail
IFS=$'\n\t'

SCRIPTS_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# ^ from https://stackoverflow.com/a/246128/1018176
VCE_ROOT="$SCRIPTS_ROOT/../"

# --- check dependencies ---
if ! command -v apptainer &> /dev/null; then
    echo "Could not find an installation of Apptainer (https://apptainer.org/)."
    echo "Apptainer is needed to run vce-container."  # or is it…?
    exit 1
fi
if ! command -v wget &> /dev/null; then
    echo "Could not find an installation of wget."
    echo "wget is needed to download the Apptainer vce-container image."
    exit 1
fi

# --- vce-container ---
# Avoid dependency hell by using a pre-built container with
# OMNeT++, Veins, and SUMO pre-installed to the /opt directory.
# File URL from the VCE project on OSF (https://osf.io/vmuwx/):
VCE_CONTAINER_URL="https://osf.io/vmuwx/download"
VCE_CONTAINER_FULL_NAME="vce_container_2023-08-18_omnet-6.0.1_veins5.2_sumo1.18.0_godot3.6.sif"
if [[ ! -f "$VCE_ROOT/$VCE_CONTAINER_FULL_NAME" ]]; then
    echo "Downloading vce-container ($VCE_CONTAINER_FULL_NAME)…"
    wget "$VCE_CONTAINER_URL" -O "$VCE_ROOT/$VCE_CONTAINER_FULL_NAME"
    ln -rsf "$VCE_ROOT/$VCE_CONTAINER_FULL_NAME" "$VCE_ROOT/vce-container.sif"
else
    echo "Skipping downloading vce-container since it already exists."
fi

# --- install subprojects using vce-container ---
apptainer exec "$VCE_ROOT/vce-container.sif" bash -O extglob -c 'export VEINS_ROOT=$(echo /opt/veins/veins-veins*) && export GODOT=$(echo /opt/Godot*/Godot_*.64) && '"$VCE_ROOT/scripts/vce-install-native.sh"
