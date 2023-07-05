#!/usr/bin/env python3

import asyncio
import argparse
from evi_connector import EVIProtocol
from env3d_connector import Env3dProtocol

msg_queue_evi = asyncio.Queue()
msg_queue_env3d = asyncio.Queue()
number_of_env3ds = 1

# IMPORTANT: might need to run
#  `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='python'`
#  before starting in case of protobuf error


async def main(env3d_port, evi_port, total_number_of_env3ds):
    print("Started interface")
    shutdown_event = asyncio.Event()

    # setup env3d server
    env3d_protocol = Env3dProtocol(
        env3d_port,
        shutdown_event,
        msg_queue_evi,
        msg_queue_env3d,
        total_number_of_env3ds
    )

    # setup EVI client
    evi_protocol = EVIProtocol(
        evi_port,
        shutdown_event,
        msg_queue_evi,
        msg_queue_env3d
    )

    await asyncio.create_task(
        main_loop(env3d_protocol, evi_protocol, shutdown_event)
    )

    print("Stopped interface")


async def main_loop(env3d_protocol, evi_protocol, shutdown):
    """
    Main loop to run the interface and coordinate the evi_connector
    and env3d_connector
    """

    # starting phase
    await asyncio.create_task(env3d_protocol.serve_intialize())
    await asyncio.create_task(evi_protocol.request())
    await asyncio.create_task(evi_protocol.get_reply())
    await asyncio.create_task(env3d_protocol.reply())

    while not shutdown.is_set():
        await asyncio.create_task(env3d_protocol.serve_only())
        await asyncio.create_task(evi_protocol.request())
        await asyncio.create_task(evi_protocol.get_reply())
        await asyncio.create_task(env3d_protocol.reply())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--env3d-port',
        type=int,
        help='Port of 3DEnv'
    )
    parser.add_argument(
        '--evi-port',
        type=int,
        help='Port of EVI'
    )
    parser.add_argument(
        '--connections',
        type=int,
        help='Number of 3DEnv Entities to connect to'
    )
    args = parser.parse_args()
    asyncio.run(main(
        env3d_port=args.env3d_port,
        evi_port=args.evi_port,
        total_number_of_env3ds=args.connections
    ))
