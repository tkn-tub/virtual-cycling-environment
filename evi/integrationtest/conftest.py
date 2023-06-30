"""
common fixtures for working with sumo
"""

import contextlib
import socket

import pytest
import traci

from evi.defaultconfig import DEFAULT_SUMO_OPTS
from evi.state import Position, Vehicle
from evi.util import launch_sumo


def _unused_udp_port():
    """Find an unused localhost UDP port from 1024-65535 and return it."""
    sock = socket.socket(type=socket.SOCK_DGRAM)
    with contextlib.closing(sock):
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


@pytest.fixture
def unused_udp_port():
    """Find an unused localhost UDP port from 1024-65535 and return it."""
    return _unused_udp_port()


@pytest.fixture
def sumo_config():
    """return a path to a sumo config file suitable for testing"""
    return 'networks/circle-scenario/circle.sumo.cfg'


@pytest.fixture
def unused_sumo_port(unused_tcp_port_factory):
    """Get a free port for sumo."""
    return unused_tcp_port_factory()


@pytest.fixture
def ego_vehicle_id():
    """return a sumo string id for an ego vehicle"""
    return "some-ego-vehicle"


@pytest.fixture
def valid_position():
    """return a valid vehicle Position record"""
    return Position(
        road_id="1/1to1024/1",
        s_frac=5.10 / 785.40,
        lane_id=0,
        x=1.65,
        y=250.0,
        angle=0.61,
        height=0,
        slope=0,
    )


@pytest.fixture
def valid_vtype():
    """return a valid Sumo vehicle type for the ego vehicle"""
    return 'ego-type'


@pytest.fixture
def valid_route_name():
    """return a valid name for a route of the ego vehicle"""
    return 'ego-route'


@pytest.fixture
def valid_ego_vehicle(ego_vehicle_id, valid_position, valid_route_name, valid_vtype):
    """return a valid state of an ego vehicle"""
    return Vehicle(
        id=ego_vehicle_id,
        position=valid_position,
        speed=0.0,
        route=valid_route_name,
        signals=frozenset(),
        veh_type=valid_vtype,
        stop_states=frozenset(),
    )


@pytest.fixture
async def sumo_instance(unused_sumo_port, sumo_config):
    """launch an instance of sumo suitable for testing and return process handle"""
    try:
        proc = await launch_sumo(
            config=sumo_config,
            port=unused_sumo_port,
            extra_opts=DEFAULT_SUMO_OPTS,
        )
        yield proc
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()  # so the loop will not be destroyed


@pytest.fixture
async def traci_connection(unused_sumo_port, sumo_instance):
    """get a traci connection backed by a running sumo instance."""
    try:
        con = traci.connect(port=unused_sumo_port, numRetries=0)
        yield con
    finally:
        if hasattr(con, '_socket'):  # not closed yet
            con.close()
