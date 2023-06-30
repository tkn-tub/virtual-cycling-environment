#!/usr/bin/env python3

import argparse
import base64
import bz2
import contextlib
import csv
import gzip
import hashlib
import lzma
import os
import sys

import asmp.asmp_pb2 as asmp

# increase csv field size for long fields containing encoded messages
csv.field_size_limit(sys.maxsize)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hash-file", help="write hash of decoded message to this file."
    )
    parser.add_argument(
        "--dump-file",
        default="/dev/null",
        help="dump decoded messages to this file.",
    )
    parser.add_argument(
        "--call-name",
        default="allTraffic",
        help="label to identify repro messages in trace.",
    )
    parser.add_argument("trace_file", help="reproduction trace to read")
    return parser.parse_args()


@contextlib.contextmanager
def flex_open(fname, *arg, **kwd):
    """
    Open a possibly compressed file transparently based on the file extension.

    Currently supports bz2, xz, and gzip compressed files.
    Everything else is opened using the builtin open.
    """
    openers = {
        ".gz": gzip.open,
        ".bz2": bz2.open,
        ".xz": lzma.open,
    }
    opener = openers.get(os.path.splitext(fname)[1], open)
    with opener(fname, *arg, **kwd) as open_file:
        yield open_file


def process_trace(file_name):
    with flex_open(file_name, "rt") as trace_file:
        reader = csv.DictReader(trace_file, dialect=csv.unix_dialect)
        veins_records = (
            record
            for record in reader
            if record["module"] == "proto.evi.veins"
        )
        yield from veins_records


def extract_messages(records):
    for record in records:
        yield base64.b64decode(record["message"])


def dump_trace(
    trace_file_name, dump_file_name="/dev/null", call_name="allTraffic"
):
    messages = extract_messages(
        record
        for record in process_trace(trace_file_name)
        if record["callName"] == call_name
    )
    rolling_hash = hashlib.md5()
    with open(dump_file_name, "w") as dump_file:
        for msg_nr, msg_bytes in enumerate(messages):
            msg = asmp.Message()
            msg.ParseFromString(msg_bytes)
            rolling_hash.update(str(msg).encode("utf-8"))
            if dump_file_name != "/dev/null":
                dump_file.write(str(msg))
    return rolling_hash.hexdigest()


def main():
    args = parse_args()
    dump_hash = dump_trace(args.trace_file, args.dump_file, args.call_name)
    if args.hash_file:
        with flex_open(args.hash_file, "wt") as hash_file:
            hash_file.write(dump_hash)


if __name__ == "__main__":
    main()
