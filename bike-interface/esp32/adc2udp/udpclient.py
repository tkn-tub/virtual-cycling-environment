#!/usr/bin/env python3

import argparse
import socket
import sys
import time
import typing
import csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log-csv',
        type=argparse.FileType('w')
    )
    args = parser.parse_args()

    receive(log_file=args.log_csv)


def receive(log_file: typing.TextIO):
    # try:
    family_addr = socket.AF_INET
    sock = socket.socket(family_addr, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 4022))
    t_start_s = time.time()
    csv_writer = None
    if log_file is not None:
        csv_writer = csv.DictWriter(
            f=log_file,
            fieldnames=['time_s', 'spokes_per_s'],
        )
        csv_writer.writeheader()

    while True:
        try:
            reply = sock.recv(128)
            if not reply:
                break
            log_data = dict(
                time_s=time.time() - t_start_s,
                spokes_per_s=float(
                    reply.decode('ascii').replace("\n", "")
                )
            )
            if csv_writer is not None:
                csv_writer.writerow(log_data)
            print(
                f"t={log_data['time_s']:03.3f} s, "
                f"spokes per second = {log_data['spokes_per_s']:02.2f}"
            )
        except socket.error as msg:
            print('Error Code : ' + str(msg[0]) + ' Message: ' + msg[1])
            sys.exit()


if __name__ == '__main__':
    main()
