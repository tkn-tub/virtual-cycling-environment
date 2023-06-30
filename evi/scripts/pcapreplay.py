#!/usr/bin/env python3
"""
convert ASM messages from pcap recordings to csv files
"""

import argparse
import binascii
import csv
import itertools
import logging
import select
import socket
import time

from evi.util import flex_open

FIELDS = ['src', 'dst', 'sport', 'dport', 'payload']
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
LOG = logging.getLogger(__name__)


def parse_args():
    """build argument parser and parse arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbosity', choices=LOG_LEVELS, default='WARNING',
                        help='Set loging level/verbosity')
    parser_in = parser.add_mutually_exclusive_group(required=True)
    parser_in.add_argument("--pcap-infile")
    parser_in.add_argument("--csv-infile")
    parser.add_argument("--csv-outfile")
    mods = parser.add_argument_group(title="Overrides")
    mods.add_argument("--src", help="override source ip")
    mods.add_argument("--dst", help="override destination ip")
    mods.add_argument("--sport", type=int, help="override source port")
    mods.add_argument("--dport", type=int, help="override destination port")
    replay = parser.add_argument_group(title="Replay")
    replay.add_argument(
        "--replay", action="store_true",
        help="perform replay of read messages",
    )
    # TODO: make the following mutually exclusive
    replay.add_argument(
        "--period", type=float, default=0,
        help="period between two replayed messages (in s)",
    )
    replay.add_argument(
        "--interactive", action="store_true",
        help="wait for user input between each message",
    )
    replay.add_argument(
        "--reactive", action="store_true",
        help="wait for reply from evi between each message",
    )
    replay.add_argument(
        '--range', action='append', nargs=2, metavar=('first', 'last'),
        help=(
            'send messages in this the range [first, last]. '
            'Can be given multiple times. '
            'Multiple ranges are not allowed to overlap. '
            'If no range is given, send all messages.'
        ),
    )
    replay.add_argument(
        '--decode', action="store_true",
        help='decode the message using the ASM protocol',
    )
    return parser.parse_args()


def extract_record(pkt):
    """make dict from scapy packed"""
    return {
        'src': pkt['IP'].src,
        'dst': pkt['IP'].dst,
        'sport': int(pkt['UDP'].sport),
        'dport': int(pkt['UDP'].dport),
        'payload': pkt['Raw'].load,
    }


def import_pcap(pcap_filename):
    """read and convert message records from pcap file"""
    from scapy.all import rdpcap
    LOG.info("Reading from pcap file %s", pcap_filename)
    pcap = rdpcap(pcap_filename)
    for packet in pcap:
        yield extract_record(packet)


def import_csv(csv_filename):
    """import packets from csv"""
    LOG.info("Reading from csv file %s", csv_filename)
    with flex_open(csv_filename, 'rt') as csvfile:
        for record in csv.DictReader(csvfile):
            record['payload'] = binascii.unhexlify(record['payload'])
            record['sport'] = int(record['sport'])
            record['dport'] = int(record['dport'])
            yield record


def export_csv(records, csv_outfile):
    """export packets in pcap to csv_outfile"""
    LOG.info("Wrtiting to csv file %s", csv_outfile)
    rec_nr = -1
    with flex_open(csv_outfile, 'wt', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, FIELDS)
        writer.writeheader()
        for rec_nr, record in enumerate(records):
            row = record.copy()
            row['payload'] = binascii.hexlify(row['payload']).decode('ascii')
            writer.writerow(row)
    LOG.debug("Successfully wrote %d records to csv file", rec_nr)


def override_fields(records, **kwd):
    """override all values given in kwd within all records"""
    overrides = {key: val for key, val in kwd.items() if val is not None}
    LOG.info("Overriding fields %s", overrides)
    for record in records:
        yield {
            key: overrides.get(key, value)
            for key, value in record.items()
        }


def make_sender_socket(src_addr):
    """open and bind an udp socket to src_addr"""
    LOG.info("Opening new sending socket with adress %s:%d", *src_addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(src_addr)
    return sock


def replay_data(
        record_stream,
        period,
        interactive=False,
        reactive=False,
        decode=False
):
    """perform replay of read messages with period seconds in between"""
    if decode or reactive:
        import asmp.asmp_pb2 as asmp
    socks = {}
    LOG.info("Performing replay with %f seconds period beween packets",
             period)
    rec_nr = -1
    first = True
    try:
        for rec_nr, record in record_stream:
            src_addr = (record['src'], record['sport'])
            dst_addr = (record['dst'], record['dport'])
            # get sending socket
            try:
                sock = socks[src_addr]
            except KeyError:
                sock = make_sender_socket(src_addr)
                socks[src_addr] = sock

            if reactive and not first:
                # wait for message from evi
                evi_frame = None
                LOG.debug("Waiting for message from EVI.")
                while not evi_frame:
                    recv, _, _ = select.select([sock], [], [], 0.1)
                    if recv != [sock]:
                        # interrupt this occasionally for error handling
                        continue
                    evi_frame = sock.recv(4096)
                evi_msg = asmp.Message()
                evi_msg.ParseFromString(evi_frame[5:])
                LOG.info(
                    "Got message from EVI of type %s",
                    evi_msg.WhichOneof("message_oneof"),
                )
            first = False

            if interactive:
                input(
                    "Next packet: #{} from {} to {} -> ".format(
                        rec_nr,
                        src_addr,
                        dst_addr,
                    )
                )

            if decode:
                m = asmp.Message()
                m.ParseFromString(record['payload'][5:])
                LOG.debug("Message contents\n%s", m)

            try:
                sock.sendto(record['payload'], dst_addr)
            except OSError as exc:
                LOG.warning(
                    "Error sending packet %d from %s:%d to %s:%d; Message %s",
                    rec_nr,
                    *src_addr,
                    *dst_addr,
                    exc
                )
            else:
                LOG.debug(
                    "Sent packet #%d from %s:%d to %s:%d of %d bytes",
                    rec_nr,
                    *src_addr,
                    *dst_addr,
                    len(record['payload'])
                )

            time.sleep(period)

    except KeyboardInterrupt:
        LOG.warning(
            "Replay interrupted by user after msg nr %d, closing sockets...",
            rec_nr,
        )
        for sock in socks.values():
            sock.close()


def filter_ranges(records, ranges=None):
    """
    Yield only elements in records whose indices are in ranges.

    ranges are sequences of (first, last) tuples.
    last can be None, meaning the range is unlimited.
    """
    def parse(value):
        if value == "None" or value is None:
            return None
        if isinstance(value, int):
            return value
        return int(value)

    if ranges is None:
        ranges = [(0, None)]
    else:
        ranges = [(parse(range_[0]), parse(range_[1])) for range_ in ranges]

    ranges = list(sorted(ranges))
    for nr, record in records:
        if nr < ranges[0][0]:
            # drop messages before next range
            LOG.debug("dropping message nr %d", nr)
            continue
        if ranges[0][1] is not None and nr == ranges[0][1]:
            # remove range after it is finished
            # won't happen for unlimited ranges
            ranges = ranges[1:]
        yield (nr, record)


def main():
    """call me maybe"""
    args = parse_args()
    LOG.setLevel(args.verbosity)
    logging.debug("Configuration: %s", str(args))

    # read data
    if args.pcap_infile:
        data = import_pcap(args.pcap_infile)
    else:
        data = import_csv(args.csv_infile)

    # process / modify data
    data = override_fields(
        data,
        src=args.src,
        dst=args.dst,
        sport=args.sport,
        dport=args.dport,
    )

    # save data
    if args.csv_outfile:
        data = list(data)
        export_csv(data, args.csv_outfile)

    # replay data
    if args.replay:
        record_stream = filter_ranges(enumerate(data), args.range)
        replay_data(
            record_stream,
            args.period,
            args.interactive,
            args.reactive,
            args.decode,
        )
    LOG.info("All done, shutting down.")


if __name__ == "__main__":
    main()
