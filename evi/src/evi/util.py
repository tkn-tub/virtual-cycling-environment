""""
EVI Utility collection
"""
import asyncio
import bz2
import collections
import contextlib
import gzip
import hashlib
import itertools
import logging
import os
import socket
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import (
    IO,
    Iterable,
    Iterator,
    List,
    Optional,
    TypeVar,
    Hashable,
    Any,
)

import psutil
import sumolib
import numpy as np

try:
    import pyproj

    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


SomeType = TypeVar("SomeType")

# setup trace level logging
LOGLEVEL_TRACE = 5
logging.addLevelName(LOGLEVEL_TRACE, "TRACE")


def trace(self, message, *args, **kws):
    """
    Log 'msg % args' with severity 'TRACE'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.debug("Houston, we have a %s", "thorn-shaped problem", exc_info=1)
    """
    if self.isEnabledFor(LOGLEVEL_TRACE):
        self._log(LOGLEVEL_TRACE, message, args, **kws)


setattr(logging.Logger, "trace", trace)
# using this as logging.trace will still make linters and mypy unhappy
# thus, use trace(LOG, "some message here") instead

LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def flex_open(fname, *arg, **kwd):
    """
    Open a possibly compressed file transparently based on the file extension.

    Currently supports bz2 and gzip compressed files.
    Everything else is opened using the builtin open.
    """
    openers = {
        ".gz": gzip.open,
        ".bz2": bz2.open,
    }
    opener = openers.get(os.path.splitext(fname)[1], open)
    with opener(fname, *arg, **kwd) as open_file:
        yield open_file


def make_event_setting_handler(sig, event):
    """
    Return a callback that sets event for a given signal.

    Does only create the callback, not register the handler to the signal!
    """

    def interrupt_handler():
        LOG.warning("Interrupt signal %s received, shutting down.", sig)
        event.set()

    return interrupt_handler


def empty_dict_if_none(key: Hashable, value: Any) -> dict:
    """
    Useful for building up dict objects.
    If you have a variable x that may be None and if you only want to include
    it in your dict if it is not None, simply do this:
    {**empty_dict_if_none('x', x), 'y': y, …}

    :param key:
    :param value:
    :return:
    """
    return {key: value} if value is not None else {}


# SUMO helper functions


def extract_projection_data(net_file_name):
    """
    Extract geo projection data and offset from a sumo net file.
    """
    parser = ET.iterparse(net_file_name)
    loc = next(parser)[1]  # extract <location> argument from net file
    projection_params = loc.get("projParameter")
    str_offsets = loc.get("netOffset").split(",")
    offset = float(str_offsets[0]), float(str_offsets[1])
    return projection_params, offset


def make_geo_mapper(projection_params, offset):
    """Build a mapping between cartesian and geo (lon/lat) coordinates."""
    if not PYPROJ_AVAILABLE:
        raise ImportError("pyproj not available")

    x_off, y_off = offset

    if projection_params == "!":
        # "No projection was applied"
        # (https://sumo.dlr.de/docs/Networks/SUMO_Road_Networks.html)
        return lambda x, y: (x - x_off, y - y_off)

    projection = pyproj.Proj(projparams=projection_params)

    def geo_mapper(x, y):
        """Map x, y to lon, lat"""
        return projection(
            x - x_off,
            y - y_off,
            inverse=True,
        )

    return geo_mapper


def lane_to_edge(lane):
    """Extract SUMO edge id from SUMO lane id"""
    return lane[: lane.rfind("_")]


def lane_to_nr(lane):
    """Extract SUMO lane number from SUMO lane id"""
    return int(lane[lane.rfind("_") + 1 :])


def edge_lane_nr_to_lane_id(edge_id, lane_nr):
    """Build SUMO lane id from edge id and lane number"""
    return "{}_{}".format(edge_id, lane_nr)


def make_edge_to_lane_map(lane_ids):
    """return a mapping from sumo edge ids to all their lane ids"""
    edge_to_lane = collections.defaultdict(list)
    for lane in lane_ids:
        edge_to_lane[lane_to_edge(lane)].append(lane)
    return dict(edge_to_lane)


def vehicle_to_geolocation(network, vehicle):
    """Return the vehicle's geolocation in the network."""
    edge = network.getEdge(vehicle.position.road_id)
    lane = edge.getLanes()[vehicle.position.lane_id]
    return network.convertXY2LonLat(
        *sumolib.geomhelper.positionAtShapeOffset(
            lane.getShape(), vehicle.position[1] * lane.getLength()
        )
    )


def get_cartesian_and_direction_and_angle_from_edge_pos(
        sumo_net,
        edge_id,
        edge_pos,
):
    """
    :raise: ValueError if edge_pos goes beyond the defined length
        of the given edge.
    :param sumo_net: A sumolib.net.Net instance.
    :param edge_id: Name of the edge.
    :param edge_pos: Position on the edge in meters from the edge's
        start point.
    :return: Cartesian coordinates (x, y), normalized direction vector,
        and angle in degrees for a given position on a SUMO edge.
    """
    edge = sumo_net.getEdge(edge_id)
    if edge_pos < 0 or edge_pos > edge.getLength():
        raise ValueError(
            "Cannot get coordinates and angle at "
            f"position {edge_pos} on edge {edge_id} "
            f"of length {edge.getLength()}."
        )

    verts = edge.getShape()

    distance_on_edge = 0.
    for segment in zip(verts, verts[1:]):
        # An edge consists of segments, each segment being defined by
        # two consecutive vertices v_start and v_end in verts.
        v_start, v_end = np.array(segment)

        segment_length = np.linalg.norm(v_end - v_start)
        v_direction = (v_end - v_start) / segment_length

        if edge_pos <= distance_on_edge + segment_length:
            angle = -np.degrees(np.arctan2(v_direction[1], v_direction[0]))
            return (
                tuple(v_start + (edge_pos - distance_on_edge) * v_direction),
                v_direction,
                angle
            )

        distance_on_edge += segment_length

    raise ValueError(
        "Cannot get coordinates and angle at position "
        f"{edge_pos} on edge {edge_id} of length {edge.getLength()}."
    )


def get_cartesian_from_edge_pos(sumo_net, edge_id, edge_pos):
    """
    :param sumo_net: A sumolib.net.Net instance.
    :param edge_id: Name of the edge.
    :param edge_pos: Position on the edge in meters from the
        edge's start point.
    :return: Cartesian coordinates (x, y) for a given position on a SUMO edge.
        Returns None if edge_pos goes beyond the defined length
        of the given edge.
    """
    result = get_cartesian_and_direction_and_angle_from_edge_pos(
        sumo_net,
        edge_id,
        edge_pos,
    )
    return result[0] if result is not None else None


def drop_consecutive_duplicates(
    iterable: Iterable[SomeType],
) -> Iterator[SomeType]:
    """
    Remove all items that are the same as the preceding item.

    Non-consecutive duplicates are left as-is.
    Order is preserved.

    >>> list(drop_consecutive_duplicates(['a', 'a', 'b']))
    ['a', 'b']
    >>> list(drop_consecutive_duplicates([1, 2, 2, 1, 2]))
    [1, 2, 1, 2]
    """
    yield from (group[0] for group in itertools.groupby(iterable))


# subprocess spawning helpers


async def wait_for_open_port(
    pid, port, transport, wait_duration=0.05, wait_times=100
):
    """Wait until the process with pid is listening to port"""

    for _ in range(wait_times):
        open_connections = psutil.Process(pid).connections()
        for connection in open_connections:
            tcp_open = (
                transport == "tcp"
                and connection.type == socket.SOCK_STREAM
                and connection.status == psutil.CONN_LISTEN
            )
            udp_open = (
                transport == "udp" and connection.type == socket.SOCK_DGRAM
            )
            if connection.laddr[1] == port and (tcp_open or udp_open):
                LOG.debug("Found open port %d on process %d", port, pid)
                return
        await asyncio.sleep(wait_duration)
    raise TimeoutError("Process did not listen to port in time", pid, port)


async def launch_subproc(
    cmd, port, transport, name="Unknown Subprocess", wait_times=100, **kwd
):
    """
    Asynchronously launch as subprocess and wait until its transport is up.
    """
    LOG.info("Launching %s...", name)
    # wait until it's started
    proc = await asyncio.create_subprocess_exec(*cmd, **kwd)
    try:
        await wait_for_open_port(
            proc.pid, port, transport, wait_times=wait_times
        )
        LOG.info("Successfully launched %s...", name)
        return proc
    except BaseException as ex:
        # starting failed - clean up as far as possible
        proc.kill()
        raise ex


async def kill_subproc_after(subproc, timeout, name):
    """
    Wait timeout seconds for subproc to end, kill after that.
    """
    LOG.info("Waiting for subprocess '%s' to shutdown...", name)
    try:
        await asyncio.wait_for(subproc.wait(), timeout)
        LOG.info("Subprocess '%s' shut down by itself.", name)
    except asyncio.TimeoutError:
        LOG.warning(
            "Subprocess '%s' did not stop by itself, killing it.", name
        )
        subproc.kill()


async def launch_sumo(config, port, extra_opts=None, binary="sumo", seed=None):
    """
    Asynchronously lanch a SUMO instance as a subprocess and wait until its up.
    """
    proc = await launch_subproc(
        cmd=[
            binary,
            "-c",
            config,
            "--remote-port",
            "{:d}".format(port),
            *(extra_opts if extra_opts else []),
            *(["--seed", seed] if seed else []),
        ],
        port=port,
        transport="tcp",
        name="Sumo (Port: {})".format(port),
    )
    return proc


async def launch_veins(
    config_name, port, binary, scenario_dir, runnr, extra_opts=None
):
    """
    Asynchronously lanch a Veins instance as subprocess and wait until its up.
    """
    extra_opts = extra_opts if extra_opts is not None else []

    async def log_veins_instance(veins_launcher):
        async def process_pipe(stream, loggerName):
            logger = logging.getLogger(loggerName)
            while not stream.at_eof():
                line = await stream.readline()
                logger.info(line.decode("utf-8").rstrip())

        veins_proc = await veins_launcher
        asyncio.create_task(process_pipe(veins_proc.stdout, "VeinsStdout"))
        asyncio.create_task(process_pipe(veins_proc.stderr, "VeinsStderr"))
        return veins_proc

    return await log_veins_instance(
        launch_subproc(
            cmd=[
                binary,
                "--",
                "-c",
                config_name,
                "-r",
                str(runnr),
                *extra_opts,
            ],
            port=port,
            transport="tcp",
            name="Veins (Port: {})".format(port),
            cwd=scenario_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    )


def is_datagram_socket(sock):
    """
    Return whether sock is a (UDP) datagram socket.
    """
    return (sock.type & socket.SOCK_DGRAM) == socket.SOCK_DGRAM


def is_stream_socket(sock):
    """
    Return whether sock is a (TCP) stream socket.
    """
    return (sock.type & socket.SOCK_STREAM) == socket.SOCK_STREAM


# ASM data type helper functions


def make_uint_mapping(strings, nbytes=4):
    """
    Return a two-way mapping to map SUMO string ids to numerical ids and back.
    """
    forward_mapping = {
        s: int(
            hashlib.md5(s.encode("utf-8")).hexdigest()[: 2 * nbytes], base=16
        )
        for s in strings
    }
    backward_mapping = {v: k for k, v in forward_mapping.items()}
    return forward_mapping, backward_mapping


def to_uint(string_id, nbytes=4):
    """
    Map a SUMO String id to a numerical id.
    """
    return int(
        hashlib.md5(string_id.encode("utf-8")).hexdigest()[: 2 * nbytes],
        base=16,
    )


class StringIdMapper:
    """
    Maps string ids to uint ids for protobuf
    """

    def __init__(self, initials=None, nbytes=4):
        self._to_int_map = {}
        self._to_str_map = {}
        self._nbytes = nbytes
        self.prime(initials)

    def force_add_mapping(self, string_id, uint_id):
        """
        Add a mapping that is not auto-generated.
        """
        if string_id in self._to_int_map:
            raise KeyError(
                "Id {} already present in mapping".format(string_id)
            )
        LOG.debug("Force-adding id-mapping: %s <--> %d", string_id, uint_id)
        self._to_int_map[string_id] = uint_id
        self._to_str_map[uint_id] = string_id

    def prime(self, values=None):
        """
        Generate mapping entries for the given string values.
        """
        if values:
            to_int_map, to_str_map = make_uint_mapping(values)
            self._to_int_map.update(to_int_map)
            self._to_str_map.update(to_str_map)

    def to_uint(self, string_id):
        """
        Map SUMO string id to numeric id.
        """
        try:
            return self._to_int_map[string_id]
        except KeyError:
            uint_id = int(
                hashlib.md5(string_id.encode("utf-8")).hexdigest()[
                    : 2 * self._nbytes
                ],
                base=16,
            )
            self._to_int_map[string_id] = uint_id
            self._to_str_map[uint_id] = string_id
            return uint_id

    def to_string(self, uint_id):
        """
        Map numeric id (back) to SUMO string id.
        """
        try:
            return self._to_str_map[uint_id]
        except KeyError:
            string_id = "unknown-{}".format(uint_id)
            LOG.warning("Decoding unknown uint id: %s", uint_id)
            self._to_str_map[uint_id] = string_id
            return string_id

    def dump_mapping(self):
        """
        Return current mapping as string, sorted by int ids
        """
        return "int_id,string_id\n" + "\n".join(
            '{},"{}"'.format(int_id, string_id)
            for string_id, int_id in sorted(
                self._to_int_map.items(), key=lambda item: item[1]
            )
        )


class EventTracer:
    """
    Trace chrome about://trace style events.

    All passed values should be in the units in the spec:

    - ts (time stamps): microseconds
    """

    messages: List[str]

    def __init__(self) -> None:
        self.messages = []

    def write(self, writable: IO, write_head=True) -> int:
        """
        Write stored messages to file, clear buffer and return written lines.
        """
        if write_head:
            writable.write("[\n")
        num_messages = len(self.messages)
        for number, message in enumerate(self.messages):
            comma = "," if number < num_messages - 1 else ""
            writable.write("{" + message + "}" + comma + "\n")
        if write_head:
            writable.write("]\n")
        self.messages = []
        return num_messages

    @staticmethod
    def ts() -> float:
        """Get current timestamp in microseconds from the internal clock."""
        return time.perf_counter_ns() / 1000

    def begin(
        self,
        name: str,
        ts: Optional[float] = None,
        pid: str = "evi",
        tid: str = "main",
    ) -> None:
        """Begin a duration event."""
        ts = ts if ts is not None else self.ts()
        self.messages.append(
            '"ph": "B", '
            f'"name": "{name}", "ts": {ts}, '
            f'"pid": "{pid}", "tid": "{tid}"'
        )

    def end(
        self,
        name: str,
        ts: Optional[float] = None,
        pid: str = "evi",
        tid: str = "main",
        args: Optional[dict] = None,
    ) -> None:
        """End a duration event."""
        ts = ts if ts is not None else self.ts()
        msg = (
            '"ph": "E", '
            f'"name": "{name}", "ts": {ts}, '
            f'"pid": "{pid}", "tid": "{tid}"'
        )
        if args:
            msg += f', "args": {args}'.replace("'", '"')
        self.messages.append(msg)

    def instant(
        self,
        name: str,
        ts: Optional[float] = None,
        pid: str = "evi",
        tid: str = "main",
    ) -> None:
        """Record an instant event without a duration."""
        ts = ts if ts is not None else self.ts()
        self.messages.append(
            '"ph": "i", '
            f'"name": "{name}", "ts": {ts}, '
            f'"pid": "{pid}", "tid": "{tid}"'
        )

    @contextlib.contextmanager
    def complete(
        self,
        name: str,
        pid: str = "evi",
        tid: str = "main",
        args: Optional[dict] = None,
    ):
        """Record a complete event with start time and duration."""
        start = self.ts()
        yield
        end = self.ts()
        msg = (
            '"ph": "X", '
            f'"name": "{name}", "ts": {start}, "dur": {end - start}, '
            f'"pid": "{pid}", "tid": "{tid}"'
        )
        if args:
            msg += f', "args": {args}'.replace("'", '"')
        self.messages.append(msg)


# default shared mapper
ID_MAPPER = StringIdMapper()

# default event tracer
TRACER = EventTracer()
