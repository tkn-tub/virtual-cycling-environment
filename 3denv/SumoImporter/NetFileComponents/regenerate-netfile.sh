#!/usr/bin/env bash
if [[ -z "${SUMO_HOME}" ]]; then
    echo "SUMO_HOME is not set."
    exit 1
fi

OUT_PATH=${PWD}
SCHEMAS=(net_file additional_file)
XSD_FILES=("${SCHEMAS[@]/%/.xsd}")
echo "${XSD_FILES[@]}"
echo

cd "${SUMO_HOME}/data/xsd/" || exit

xsd "${XSD_FILES[@]}" \
    /classes \
    /namespace:Env3d.SumoImporter.NetFileComponents \
    /outputdir:"${OUT_PATH}"

mv "${OUT_PATH}/$(IFS=_ ; echo "${SCHEMAS[*]}").cs" "${OUT_PATH}/NetFile.cs"
echo "Renamed to ${OUT_PATH}/NetFile.cs"
