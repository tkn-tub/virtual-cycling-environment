#!/bin/bash
# wait until a given port is open or time out with an error

set -eu

PORT=$1
TIMEOUT=30

for I in $(seq $TIMEOUT); do
	if (ss -lun | grep 12346 > /dev/null) ; then
		echo "Port is open, continuing"
		exit 0
	fi
	# echo "waiting for port to open"
	sleep 1
done

echo "Waiting for port to open timed out."
exit 1
