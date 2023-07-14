#!/usr/bin/env bash

netgenerate --spider \
    --spider.arm-number 4 \
    --spider.circle-number 1 \
    -o network.net.xml

$SUMO_HOME/tools/randomTrips.py \
    -n network.net.xml \
    -r network.rou.xml \
    --random-depart \
    --period 3 \
    -o network.trip.xml

# We need to have a projection (especially if we expect messages from Veins):
sed -i 's/projParameter="!"/projParameter="+proj=utm +zone=32 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/g' network.net.xml
