#!/bin/bash
# announce that EVI is running by opening a TCP port
#
# in contrast to UDP ports, TCP ports can be scanned remotely

set -eu

if (scripts/port_waiter.sh 12346) ; then
	echo "EVI started, opening port"
	python3 -m http.server --bind 0.0.0.0 9999
else
	echo "Timeout, exiting"
	exit 1
fi
