#!/usr/bin/env bash


# Bash strict mode (http://redsymbol.net/articles/unofficial-bash-strict-mode/):
set -euo pipefail
IFS=$'\n\t'


cleanup() {
    godot_editor_settings="$HOME/.config/godot/editor_settings-3.tres"
    if [ -f "$godot_editor_settings.bak" ]; then
        mv "$godot_editor_settings.bak" "$godot_editor_settings"
    fi
    # TODO: stil required for Godot 4?
    godot_editor_settings="$HOME/.config/godot/editor_settings-4.tres"
    if [ -f "$godot_editor_settings.bak" ]; then
        mv "$godot_editor_settings.bak" "$godot_editor_settings"
    fi
}

trap "cleanup" INT TERM EXIT

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
if command -v bear &> /dev/null; then
    # Use bear to generate a compile_commands.json, which some editors or IDEs can use for better error checking
    bear -- make -j$(nproc)
else
    make -j$(nproc)
fi


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
# We need to install so-called export templates.
# Normally the Godot Editor would prompt you for this, but unfortunately, there seems to be no command-line option. So let us replicate this download functionality here…
mkdir -p "$HOME/.local/share/godot/templates"
# The Strings returned by `godot --version` may look like this:
# - 3.5.1.stable.mono.official.6fed1ffa3
# - 3.6.beta2.mono.official.68c507f59
# For the mirrorlist, we need to cut off after 'mono' (from https://askubuntu.com/a/985779):
set +o pipefail  # Problem: godot --version may return with exit code 255 instead of 0
godot_version=$("$GODOT" --version | awk -F 'mono' '{print $1 FS}')
set -o pipefail
echo "Godot version: $godot_version"
godot_mirrorlist_url="https://godotengine.org/mirrorlist/$godot_version.json"
godot_templates_tpz=$HOME/.local/share/godot/templates.tpz
godot_templates_dir=$HOME/.local/share/godot/templates/${godot_version}
if [ -d "$godot_templates_dir" ]; then
    echo "Skipping download of Godot export templates, directory already exists: $godot_templates_dir."
else
    echo "Downloading Godot export templates…"
    echo "Mirror list URL: $godot_mirrorlist_url"
    godot_template_url=$(curl -s "$godot_mirrorlist_url" | \
        python3 -c "import sys, json; print(json.load(sys.stdin)['mirrors'][0]['url'])")
    echo "Template URL: $godot_template_url"
    wget "$godot_template_url" -O "$godot_templates_tpz"
    unzip -u "$godot_templates_tpz" -d "$HOME/.local/share/godot/templates"
    # templates/ subdir is included in archive, but does not have the required subdir with the correct name itself -> rename:
    mv "$HOME/.local/share/godot/templates/templates" "$godot_templates_dir"
    rm "$godot_templates_tpz"
fi
echo "Exporting 3DEnv to $VCE_ROOT/3denv/build/…"
mkdir -p "$VCE_ROOT/3denv/build"

# Exporting with msbuild currently does not work for unknown reasons -> override editor setting
godot_editor_settings="$HOME/.config/godot/editor_settings-3.tres"
if [ -f "$godot_editor_settings" ]; then
    cp "$godot_editor_settings" "$godot_editor_settings.bak"
fi
# Write our own config:
mkdir -p "$HOME/.config/godot"
cat <<FILE >"$godot_editor_settings"
[gd_resource type="EditorSettings" format=2]

[resource]
mono/builds/build_tool = 3
FILE

$GODOT --no-window --export "Linux/X11" "build/3denv.x86_64" "$VCE_ROOT/3denv/project.godot"


# TODO: esp32 dependencies?
