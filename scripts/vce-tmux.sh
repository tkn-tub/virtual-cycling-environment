#!/usr/bin/env bash


# Bash strict mode (http://redsymbol.net/articles/unofficial-bash-strict-mode/):
set -euo pipefail
IFS=$'\n\t'

SCRIPTS_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# ^ from https://stackoverflow.com/a/246128/1018176
VCE_ROOT="$SCRIPTS_ROOT/../"


show_help() {
echo "Opens tmux with one pane for each of the following VCE components:
EVI, Veins-EVI, and Bike-Interface.
For each component, the corresponding Python environment will automatically be
opened if available.

Usage:
 ./$(basename $0) <environment>

Positional arguments:
 environment: Either \"container\" or \"native\".
    If \"container\" is selected, all environments will be opened
    using vce-container.sif.
"
exit 2
} # show_help


if [ "$#" -ne 1 ]; then
    echo "environment must be set."
    echo
    show_help
else
    if [ "$1" != "container" ] && [ "$1" != "native" ]; then
        show_help
    fi
fi


# cf. this answer for the `--init-file` approach: https://serverfault.com/a/586272
enter_evi_env="cd $VCE_ROOT/evi && poetry shell"  # export PS1='evi >'
enter_veins_evi_env="cd $VCE_ROOT/veins-evi"
enter_bicycle_model_env="cd $VCE_ROOT/bike-interface/bicycle-model/bikeToEvi && poetry shell"

if [ $1 == "container" ]; then
    enter_evi_env="
        apptainer exec $VCE_ROOT/vce-container.sif \
            bash --init-file <(echo '$enter_evi_env')
    "
    enter_veins_evi_env="
        apptainer exec $VCE_ROOT/vce-container.sif \
            bash --init-file <(echo '$enter_veins_evi_env')
    "
    enter_bicycle_model_env="
        apptainer exec $VCE_ROOT/vce-container.sif \
            bash --init-file <(echo '$enter_bicycle_model_env')
    "
fi

# Start tmux!
#
# new-session:
# -s: session name
# -n: window name

# `bash -c` is needed for compatibility with fish as the default shell in tmux.

tmux new-session -s 'VCE' -n 'vce-run' \; \
    send-keys "bash -c \"$enter_evi_env\"" C-m \; \
    split-window -v \; \
    send-keys "bash -c \"$enter_veins_evi_env\"" C-m \; \
    split-window -h \; \
    send-keys "bash -c \"$enter_bicycle_model_env\"" C-m \;
