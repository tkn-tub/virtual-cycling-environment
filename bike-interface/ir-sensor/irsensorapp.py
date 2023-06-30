#!/usr/bin/env python3
"""
IR Speed Sensor App for CCS Bicyle Simulator.

Sends speed values obtained from ir sensor to bicycle model via UDP.

This script is supposed to be run on a raspberry pi.
"""

import argparse
import logging
import socket
import time

import RPi.GPIO as GPIO

# Pin connected to the ir sensor (in BCM numbering).
DEFAULT_PIN = 7
# Flank to tick on
DEFAULT_FLANK = GPIO.FALLING
# Debounce time on pin in milliseconds
DEFAULT_BOUNCETIME = 1


class IRTickHandler:
    def __init__(self, sock):
        self.sock = sock
        self.ticknr = 0
        self.last_tick_time = 0

    def __call__(self, channel_nr):
        new_tick_time = time.perf_counter()
        delta_time = new_tick_time - self.last_tick_time
        self.last_tick_time = new_tick_time
        self.ticknr += 1
        logging.debug(
            "Tick %08d after interval of %.08f seconds",
            self.ticknr,
            delta_time,
        )
        self.sock.send(
            bytes("{:08d},{:.08f}\n".format(self.ticknr, delta_time), "ascii")
        )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("host", help="Host running the bicycle model.")
    parser.add_argument(
        "--port", "-p", default=4022, help="Port of the bicycle model."
    )
    parser.add_argument(
        "--pin", default=DEFAULT_PIN, help="GPIO pin connected to the sensor.", type=int
    )
    parser.add_argument(
        "--rising",
        action="store_true",
        help="Use rising instead of falling flank to detect tick.",
    )
    parser.add_argument(
        "--bouncetime",
        type=int,
        default=DEFAULT_BOUNCETIME,
        help="(De-)Bouncetime for tick detection in ms.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Output values on console.",
    )
    return parser.parse_args()


def main():
    """Run IR Sensor App."""
    # use port numbering as in the wiki
    GPIO.setmode(GPIO.BCM)
    # parse input
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level="DEBUG")
    target_address = (args.host, args.port)
    flank = GPIO.RISING if args.rising else GPIO.FALLING
    # open sending socket
    sock = socket.socket(type=socket.SOCK_DGRAM)
    sock.connect(target_address)
    # prepare callback
    tickhandler = IRTickHandler(sock)
    # configure gpio pin
    GPIO.setup(args.pin, GPIO.IN, GPIO.PUD_OFF)
    GPIO.add_event_detect(
        args.pin,
        flank,
        callback=tickhandler,
        bouncetime=args.bouncetime,
    )
    # run (wait for abort)
    try:
        while True:
            print("Press CRTL+C to close program.")
            input()
    finally:
        pass
    # cleanup and exit
    GPIO.cleanup()
    sock.close()


if __name__ == "__main__":
    main()
