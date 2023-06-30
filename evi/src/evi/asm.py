"""
Sumo-ASM Coordination Protocol (client)
"""

import asyncio
import binascii
import logging
import struct
from typing import Optional, Sequence, Tuple

import asmp.asmp_pb2 as asmp

from . import util
from .defaultconfig import MAX_MSG_SIZE
from .request_handlers import RequestDispatcher

LOG = logging.getLogger(__name__)
PROTO = logging.getLogger("proto." + __name__)

# TODO: time offsetting; either in vehicle handler or in the protocol


class ASMCodec:
    """
    Encoder/Decoder for the ASM Protocol.
    """

    PREFIX_CHARS = "!BI"  # network-encoded (unsigned byte, unsigned int32)
    PREFIX_LENGTH = 5  # one byte for the type, four for the length

    message_class_to_type = {
        asmp.Message: 0,
    }
    message_type_to_class = {v: k for k, v in message_class_to_type.items()}

    def decode(self, data: bytes) -> Sequence[asmp.Message]:
        """
        Decode message bytes into message objects.

        The passed data *must* start with prefix / new message.
        Currently only supports a single message.
        """
        prefix = struct.unpack(self.PREFIX_CHARS, data[: self.PREFIX_LENGTH])
        message_type, message_length = prefix
        data = data[self.PREFIX_LENGTH :]
        if len(data) < message_length:
            raise ValueError(
                f"Buffer ({len(data)}) to short for message ({message_length})"
            )
        assert len(data) == message_length
        message_object = self.message_type_to_class[message_type]()
        message_object.ParseFromString(bytes(data[:message_length]))
        return [message_object]

    def encode(self, messages: Sequence[asmp.Message]) -> bytes:
        """
        Encode message objects to a binary string and prefix.

        Currently only supports a single message.
        """
        assert len(messages) == 1
        message_object = messages[0]
        message_type = self.message_class_to_type[message_object.__class__]
        message_string = message_object.SerializeToString()
        message_length = len(message_string)
        message_prefix = struct.pack(
            self.PREFIX_CHARS, message_type, message_length
        )
        serialized_message = message_prefix + message_string
        return serialized_message


class ASMProtocol(asyncio.Protocol):
    """
    Asynchronous session protocol to interact with ASM.

    This class itelf is responsible to:
    - receive incoming requests
    - decode and deserialize data frames into message objects
    - pass request message objects to the appropriate handlers
    - collect replies from said handlers
    - serialize and encode replies
    - send back reply messages

    The actual en/decoding and (de)seriralization is delegated to a codex.
    Each request is run in its own task to allow asynchronous processing.

    Shutdown can be triggered externaly or by a connection_lost event.
    In both cases, the shutdown_event passed at construction will be set.
    This will abort all active requests and shut down the transport.
    """

    codec: ASMCodec
    dispatcher: RequestDispatcher
    transport: Optional[asyncio.BaseTransport]
    shutdown_event: asyncio.Event
    _current_id: int
    _remote_addr: Optional[Tuple[str, int]]
    _override_remote_port: int
    _override_remote_host: str

    def __init__(
        self,
        codec: ASMCodec,
        dispatcher: RequestDispatcher,
        shutdown_event: asyncio.Event,
        override_remote_port: int = -1,
        override_remote_host: str = "",
    ) -> None:
        """Set up protocol encoding with codec and deferring to handlers"""
        self.codec = codec
        self.dispatcher = dispatcher
        self.transport = None
        self.shutdown_event = shutdown_event
        self._current_id = 0
        self._remote_addr = None
        self._override_remote_port = override_remote_port
        self._override_remote_host = override_remote_host

    # Protocol handler callbacks

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        LOG.info("Connection to ASM established.")
        sock = transport.get_extra_info("socket")
        assert util.is_datagram_socket(sock) or util.is_stream_socket(sock)
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if not exc:
            LOG.debug("Closed ASM connection")
        else:
            LOG.exception("ASM connection lost due to error: %s", exc)
        self.shutdown_event.set()

    def datagram_received(self, data: bytes, address: Tuple[str, int]) -> None:
        """
        Callback for received UDP datagrams.
        """
        util.TRACER.begin("receive", tid="asm")
        if self._remote_addr is None:
            assert address is not None
            self._remote_addr = address
            LOG.info("Established connection to remote address %s", address)
            if self._override_remote_host:
                self._remote_addr = (
                    self._override_remote_host,
                    self._remote_addr[1],
                )
                LOG.info(
                    "Overriding remote host to %s", self._override_remote_host
                )
            if self._override_remote_port > 0:
                self._remote_addr = (
                    self._remote_addr[0],
                    self._override_remote_port,
                )
                LOG.info(
                    "Overriding remote port to %d", self._override_remote_port
                )
        elif self._remote_addr != address:
            host_unexpected = (
                self._remote_addr[0] != address[0]
                and not self._override_remote_host
            )
            port_unexpected = (
                self._remote_addr[1] != address[1]
                and self._override_remote_port != -1
            )
            if host_unexpected or port_unexpected:
                LOG.warning(
                    "Received message from different remote adress. "
                    "Expected: %s; Received from: %s",
                    self._remote_addr,
                    address,
                )
        PROTO.debug("fromASM,%s", binascii.hexlify(data).decode("ascii"))
        util.TRACER.begin("decode", tid="asm")
        messages = self.codec.decode(data)
        util.TRACER.end("decode", tid="asm")
        for message in messages:
            asyncio.create_task(
                self.dispatcher.process(message, self._send_replies)
            )
        util.TRACER.end(
            "receive", tid="asm", args={"num_messages": len(messages)}
        )

    def error_received(self, exc: Exception) -> None:
        """
        Callback for errors in the concext of receiving.
        """
        LOG.exception(
            "Protocol error in %s.", self.__class__.__name__, exc_info=exc
        )

    # Internal functions

    def _send_replies(self, replies: Sequence[asmp.Message]) -> None:
        """Sends the message to ASM."""
        util.TRACER.begin("reply", tid="asm")
        for reply in replies:
            reply.id = self._current_id
            self._current_id += 1
        with util.TRACER.complete("encode", tid="asm"):
            serialized_message = self.codec.encode(replies)
        if len(serialized_message) > MAX_MSG_SIZE:
            LOG.warning(
                "message exceeds maximum message size (%d of %d bytes)",
                len(serialized_message),
                MAX_MSG_SIZE,
            )
        with util.TRACER.complete("protoDump", tid="asm"):
            PROTO.debug(
                "toASM,%s",
                binascii.hexlify(serialized_message).decode("ascii"),
            )
        assert self._remote_addr is not None and self.transport is not None
        with util.TRACER.complete(
            "sendWithTransport",
            tid="asm",
            args={"msgLength": len(serialized_message)},
        ):
            self.transport.sendto(  # type: ignore
                serialized_message, self._remote_addr
            )
        util.TRACER.end("reply", tid="asm")
