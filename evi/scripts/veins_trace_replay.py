#!/usr/bin/env python3
"""
Replay a reproduction trace recorded by evi to veins.

Used to reproduce simulations in veins with all vehicles known to evi.
Not just the once that were filtered for real-time feasibility.

Saves the resulting answers from veins to another trace file.
"""

import argparse
import base64
import csv
import sys

import zmq

# increase csv field size limit to support long encoded messages
csv.field_size_limit(sys.maxsize)


VEINS_MODULE_IDENTIFIER = "proto.evi.veins"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_file", help="Protocol trace written by EVI.")
    parser.add_argument(
        "answers_file", help="File to write Veins' answers to."
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host or IP of veins server."
    )
    parser.add_argument(
        "--port", default="12347", help="Port of Veins server."
    )
    return parser.parse_args()


def read_trace(file_name):
    """Yield messages of reproduction trace from protocol trace file."""
    with open(file_name, "r") as trace_file:
        reader = csv.DictReader(trace_file, dialect=csv.unix_dialect)
        for record in reader:
            if record["module"] != VEINS_MODULE_IDENTIFIER:
                continue
            yield base64.b64decode(record["message"])


def stream_trace_messages(socket, trace_stream):
    """Yield responses to sent messages to Veins."""
    first = True
    for message in trace_stream:
        # receive answer before every message except the first
        if not first:
            yield socket.recv_multipart()
        first = False
        socket.send_multipart([message])


def save_answers(file_name, answers):
    """Save Veins' answers to CSV file."""
    with open(file_name, "w") as answers_file:
        writer = csv.writer(answers_file, dialect=csv.unix_dialect)
        writer.writerow(["step_nr", "message_1", "message_2", "message_3"])
        for step, answer_set in enumerate(answers):
            writer.writerow(
                ["{:d}".format(step)]
                + [
                    base64.b64encode(answer).decode("ascii")
                    for answer in answer_set
                ]
            )


def main():
    """Run the replay."""
    args = parse_args()

    context = zmq.Context()
    veins_address = "tcp://{}:{}".format(args.host, args.port)
    socket = context.socket(zmq.REQ)
    socket.connect(veins_address)

    trace_stream = read_trace(args.trace_file)
    answer_stream = stream_trace_messages(socket, trace_stream)
    save_answers(args.answers_file, answer_stream)

    socket.close()
    context.destroy()


if __name__ == "__main__":
    main()
