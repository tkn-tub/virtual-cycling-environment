#!/usr/bin/env python3

import argparse
import subprocess
import time
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Wait for one or more conditions before returning. ",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--poll-interval',
        type=float,
        help="Interval in seconds with which to check conditions.",
        default=0.5,
    )
    parser.add_argument(
        '--port-open',
        nargs='*',
        type=int,
        help="Wait until the given ports are open.",
    )
    parser.add_argument(
        '--wait-message',
        help="Text to show while waiting.",
        default="Waiting for ports {ports}…",
    )
    args = parser.parse_args()

    if not shutil.which("netstat"):
        sys.exit("Could not find an installation of `netstat`.")
    if not shutil.which("grep"):
        sys.exit("Could not find an installation of `grep`.")

    print(
        args.wait_message.format(ports=args.port_open)
    )
    while True:
        ok = True
        for port in (args.port_open if args.port_open else ()):
            ok &= check_port_in_use(port)
        if ok:
            break
        time.sleep(args.poll_interval)


def check_port_in_use(port: int) -> bool:
    proc = subprocess.run(
        f"netstat -tulpn | grep -E ':{port}\\s'",
        capture_output=True,
        shell=True,
        check=False,
    )
    return proc.stdout != b""


if __name__ == '__main__':
    main()
