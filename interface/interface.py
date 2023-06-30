import asyncio
from email import message
from typing import Sequence
import argparse
from queue import Queue
from zmq.asyncio import Context, Socket
from evi_connector import EVIProtocol
from unity_connector import UnityProtocol
from time import sleep, perf_counter

msg_queue_evi = asyncio.Queue()
msg_queue_unity = asyncio.Queue()
number_of_unities = 1

# IMPORTANT: might need to run export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION='python' before starting in case of protobuf error
    
async def main(unity_port, evi_port, total_number_of_unities):
    
    print("Started interface")
    shutdown_event = asyncio.Event()
    
    # setup unity server
    unity_protocol = UnityProtocol(
            unity_port, shutdown_event, msg_queue_evi, msg_queue_unity, total_number_of_unities
    )
    
    # setup EVI client
    evi_protocol = EVIProtocol(
            evi_port, shutdown_event, msg_queue_evi, msg_queue_unity
    )
    
    await asyncio.create_task(main_loop(unity_protocol,evi_protocol,shutdown_event) )
    
    print("Stopped interface")   

# Main loop to run the interface and coordinate the evi_connector and unity_connector   
async def main_loop(unity_protocol,evi_protocol,shutdown):
    
    # starting phase
    await asyncio.create_task(unity_protocol.serve_intialize())
    await asyncio.create_task(evi_protocol.request())
    await asyncio.create_task(evi_protocol.get_reply())
    await asyncio.create_task(unity_protocol.reply())
    
    while not shutdown.is_set():
        
        await asyncio.create_task(unity_protocol.serve_only())
        await asyncio.create_task(evi_protocol.request())
        await asyncio.create_task(evi_protocol.get_reply())
        await asyncio.create_task(unity_protocol.reply())

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--unity-port', dest='unityport', type=int, help='Port of unity')
    parser.add_argument('--evi-port', dest='eviport', type=int, help='Port of evi')
    parser.add_argument('--unity-connections', dest='numberOfUnities', type=int, help='Number of Unity Entities to connect to')
    args = parser.parse_args()
    asyncio.run(main(unity_port=args.unityport, evi_port=args.eviport, total_number_of_unities=args.numberOfUnities))
    

