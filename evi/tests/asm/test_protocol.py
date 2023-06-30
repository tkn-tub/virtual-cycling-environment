"""
End-to-End testing of the EVI using the push-based ASMProtocol.
"""

import asyncio
import socket
import unittest.mock as mock

import pytest

import asmp.asmp_pb2 as asmp
from evi.asm import ASMCodec, ASMProtocol
from evi.request_handlers import RequestDispatcher

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# helpers


async def return_helper_coro(return_value):
    """
    Helper to return for async Mocks.

    mock.AsyncMock is only available since python 3.8.
    """
    return return_value


async def awaitable_helper_coro(event):
    """Coroutine that sets event and then waits forever."""
    never_ending = asyncio.Event()
    event.set()
    await never_ending.wait()


def triggering_returner(event, return_value):
    """Build a callable that triggers event and then returns a value."""

    def returner():
        event.set()
        return return_value

    return returner


# fixtures


@pytest.fixture
def fake_socket():
    fake_socket = mock.Mock()
    fake_socket.type = socket.SOCK_DGRAM
    return fake_socket


@pytest.fixture
def remote_addr():
    return ("127.0.0.1", 9999)


@pytest.fixture
def fake_transport(fake_socket):
    def side_effect(name):
        if name == "socket":
            return fake_socket
        raise RuntimeError()

    fake_transport = mock.Mock()
    fake_transport.get_extra_info = mock.Mock(side_effect=side_effect)
    fake_transport.sendto = mock.Mock()
    return fake_transport


@pytest.fixture
def valid_message_bytes():
    return b"\x00\x00\x00\x00\x0e\x08\x01\xaa\x06\t\t\x00\x00\x00\x00\x00\x00\xf0?"


@pytest.fixture
def valid_message_object():
    msg_obj = asmp.Message()
    msg_obj.id = 1
    msg_obj.vehicle.time_s = 1.0
    return msg_obj


@pytest.fixture
def responsible_process_hanndler(valid_message_object):
    handler = mock.Mock()
    handler.is_responsible = mock.Mock(return_value=True)
    return_coro = return_helper_coro(
        [valid_message_object]
    )  # FIXME: use reply
    handler.process = mock.Mock(return_value=return_coro)
    return handler


@pytest.fixture
def fake_codec(valid_message_bytes, valid_message_object):
    codec = mock.Mock()
    codec.decode = mock.Mock(return_value=[valid_message_object])
    codec.encode = mock.Mock(return_value=valid_message_bytes)
    return codec


@pytest.fixture
def fake_dispatcher(valid_message_object):
    fake_dispatcher = mock.Mock()
    return_coro = return_helper_coro([valid_message_object])
    fake_dispatcher.process = mock.Mock(return_value=return_coro)
    return fake_dispatcher


# Tests


def test_codec_decodes_valid_message(
    valid_message_bytes, valid_message_object
):
    codec = ASMCodec()
    decoded = codec.decode(valid_message_bytes)
    assert decoded
    assert len(decoded) == 1
    assert decoded[0] == valid_message_object


def test_coded_encodes_valid_message(
    valid_message_bytes, valid_message_object
):
    codec = ASMCodec()
    encoded = codec.encode([valid_message_object])
    assert encoded
    assert encoded == valid_message_bytes


async def test_protocol_decodes_request_with_codec(
    fake_codec,
    fake_dispatcher,
    fake_transport,
    remote_addr,
    valid_message_bytes,
):
    protocol = ASMProtocol(fake_codec, fake_dispatcher, asyncio.Event())
    protocol.connection_made(fake_transport)
    protocol.datagram_received(valid_message_bytes, remote_addr)

    fake_codec.decode.assert_called_with(valid_message_bytes)


async def test_protocol_encodes_reply_with_encoder(
    fake_codec,
    fake_transport,
    remote_addr,
    responsible_process_hanndler,
    valid_message_bytes,
    valid_message_object,
):
    event = asyncio.Event()
    dispatcher = RequestDispatcher([responsible_process_hanndler], event)
    protocol = ASMProtocol(fake_codec, dispatcher, event)
    protocol.connection_made(fake_transport)
    protocol.datagram_received(valid_message_bytes, remote_addr)

    await asyncio.sleep(0.01)  # not ideal, but it works

    assert fake_codec.encode.called
    fake_codec.encode.assert_called_once_with([valid_message_object])


async def test_protocol_sends_encoded_reply_via_transport(
    fake_codec,
    fake_transport,
    remote_addr,
    responsible_process_hanndler,
    valid_message_bytes,
):
    """End-to-end test with only networking and decoding faked."""
    event = asyncio.Event()
    dispatcher = RequestDispatcher([responsible_process_hanndler], event)
    protocol = ASMProtocol(fake_codec, dispatcher, event)
    protocol.connection_made(fake_transport)
    protocol.datagram_received(valid_message_bytes, remote_addr)

    await asyncio.sleep(0.01)  # not ideal, but it works

    assert fake_transport.sendto.called
    assert fake_transport.sendto.called_once_with(
        valid_message_bytes, addr=remote_addr
    )


async def test_dispatcher_forwards_request_to_correct_handler(
    valid_message_object,
    responsible_process_hanndler,
):
    event = asyncio.Event()
    fake_send_function = mock.Mock()
    dispatcher = RequestDispatcher([responsible_process_hanndler], event)

    await dispatcher.process(valid_message_object, fake_send_function)

    assert fake_send_function.called

# TODO: more tests
# - message ids are unique and increasing
