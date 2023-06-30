"""
Unity3D visualization interface.
"""

import asyncio
import logging
from typing import Sequence

import zmq
from zmq.asyncio import Context, Socket

import asmp.asmp_pb2 as asmp

from .request_handlers import RequestDispatcher

LOG = logging.getLogger(__name__)


class UnityProtocol:
    """
    Connection to Unity.
    """

    dispatcher: RequestDispatcher
    shutdown_event: asyncio.Event
    context: Context
    connection: Socket
    current_id: int

    def __init__(
        self,
        dispatcher: RequestDispatcher,
        shutdown_event: asyncio.Event,
        evi_port: int,
    ) -> None:
        self.dispatcher = dispatcher
        self.shutdown_event = shutdown_event
        self.context = Context.instance()
        local_address = f"tcp://0.0.0.0:{evi_port}"
        self.connection = self.context.socket(zmq.ROUTER)
        self.connection.bind(local_address)
        self.current_id = 0
        self.clientAdress = ""
        self.ego_ids = []


    # serve from before Multiplayer Extension
    async def serve_old(self):
        """Serve requests until the shutdown_event is triggered."""
        while True:
            # FIXME: react to shutdown_event
            # TODO: use recv_mulitpart instead
            message_bytes = await self.connection.recv()

            # decode
            message = asmp.Message()
            message.ParseFromString(message_bytes)
            LOG.debug("Got Message from Unity: %s", message)

            # dispatch
            asyncio.create_task(
                self.dispatcher.process(message, self._send_replies)
            )
            
            
    async def serve(self):
        """Serve requests until the shutdown_event is triggered."""
        while True:
            # FIXME: react to shutdown_event
            # because of Multiplayer design: use recv_multipart instead
            message_bytes = await self.connection.recv_multipart()
            
            self.clientAdress = message_bytes[0]
            LOG.debug("Got Adress from Unity: %s", self.clientAdress)
           
            i = 0
            for frame in message_bytes:
                 
                # skip client adress field in message
                i += 1
                
                # skip seperating messages
                if len(frame.strip())>5:
                      
                    # decode
                    message = asmp.Message()
                    message.ParseFromString(frame)
                    
                    LOG.debug("Got Message from Unity: %s", message)
    
                    # dispatch
                    asyncio.create_task(
                        self.dispatcher.process(message, self._send_replies)
                    ) 

    def _send_replies(self, replies: Sequence[asmp.Message]) -> None:
        """Sends the message to Unity."""
        message_strings = []
        message_strings.append(self.clientAdress)
        message_strings.append(b'') 
        for reply in replies:
            reply.id = self.current_id
            self.current_id += 1
            message_strings.append(reply.SerializeToString())
        # TODO: proto dumping/tracing
        LOG.debug(
            "Unity protocol sending message with %d replies", len(replies)
        )
        asyncio.create_task(self._send_message_set(message_strings))

    async def _send_message_set(self, message_strings):
        await self.connection.send_multipart(message_strings)
