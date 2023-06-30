"""
Interface to Veins C2X simulator.
"""

import argparse
import asyncio
import base64
import logging
import math
from collections import namedtuple
from typing import FrozenSet, Optional

import zmq
from zmq.asyncio import Context

import asmp.asmp_pb2 as asmp

from .defaultconfig import DEFAULTS
from .filtering import FELLOW_FILTERS, TrafficFilter
from .proto import vehicle_to_protobuf
from .state import Vehicle
from .util import ID_MAPPER, TRACER

LOG = logging.getLogger(__name__)
PROTO = logging.getLogger("proto." + __name__)


VeinsResult = namedtuple("VeinsResult", ["visualization", "vehicle"])


def make_network_init_message(
    network_init_data, start_time_s, sync_interval_s
):
    """
    Prepare a serialized message with network initialization data for Veins.
    """
    msg = asmp.Message()
    netinit = msg.session.netinit
    netinit.version.api = 1
    netinit.version.server = "evi"
    netinit.network_boundaries.topleft.x = network_init_data["netbounds"][0][0]
    netinit.network_boundaries.topleft.y = network_init_data["netbounds"][0][1]
    netinit.network_boundaries.bottomright.x = network_init_data["netbounds"][
        1
    ][0]
    netinit.network_boundaries.bottomright.y = network_init_data["netbounds"][
        1
    ][1]
    for i, poly_data in enumerate(network_init_data["polygons"]):
        netinit.polygons.add()
        polygon = netinit.polygons[i]
        polygon.id = poly_data["id"]
        polygon.type = poly_data["type"]
        for j, point in enumerate(poly_data["shape"]):
            polygon.shape.add()
            polygon.shape[j].x = point[0]
            polygon.shape[j].y = point[1]
    netinit.init_time_s = start_time_s
    netinit.sync_interval_s = sync_interval_s
    LOG.debug("Sending init data:\n%s", netinit)
    if not netinit.polygons:
        LOG.warning("No polygons found to send to Veins!")
    return msg.SerializeToString()


def make_traffic_message(
        traffic_changes,
        ego_vehicles: FrozenSet[Vehicle],
        current_time_s,
        geo_projection
):
    """
    Build and serialize an asmp message containing the traffic_changes.
    """
    # TODO: extract message serialization and share with RTI and Veins
    traffic_message = asmp.Message()
    traffic_message.vehicle.time_s = current_time_s
    commands = traffic_message.vehicle.commands
    for add_vehicle in sorted(traffic_changes["add"], key=lambda v: v.id):
        add_command = commands.add()
        vehicle_to_protobuf(
            add_vehicle, add_command.register_vehicle_command, geo_projection
        )
        add_command.register_vehicle_command.veh_type = (
            add_vehicle.veh_type.value
        )
        add_command.register_vehicle_command.is_ego_vehicle = False
        if add_vehicle.id in {ego_v.id for ego_v in ego_vehicles}:
            add_command.register_vehicle_command.vehicle_id = (
                ID_MAPPER.to_uint(add_vehicle.id)
            )
            add_command.register_vehicle_command.is_ego_vehicle = True
    for remove_vehicle in sorted(traffic_changes["rem"], key=lambda v: v.id):
        remove_command = commands.add()
        remove_command.unregister_vehicle_command.vehicle_id = (
            ID_MAPPER.to_uint(remove_vehicle.id)
        )
    for update_vehicle in sorted(traffic_changes["mod"], key=lambda v: v.id):
        update_command = commands.add()
        vehicle_to_protobuf(
            update_vehicle,
            update_command.update_vehicle_command,
            geo_projection,
        )
    return traffic_message.SerializeToString()


class VeinsProtocol:
    """
    ZMQ-based protocol wrapper for synchronization with Veins.
    """

    def __init__(self, connection):
        self._connection = connection
        self._is_processing_request = False

    async def communicate(self, msgs):
        """
        Await next request from veins and reply with `msgs`.
        """
        self._connection.send_multipart(msgs)
        self._is_processing_request = True
        reqests = await self._connection.recv_multipart()
        self._is_processing_request = False
        return reqests

    async def teardown(self, teardown_msgs):
        """
        Signal Veins to shut down and close connection.
        """
        LOG.debug("Veins protocol teardown started...")
        with TRACER.complete("teardownProtocol", tid="veins"):
            if not self._connection:
                return

            if self._is_processing_request:
                # try to finish communicating before sending shutdown message
                await self._connection.poll(0.2)

            if not self._is_processing_request:
                await self._connection.send_multipart(teardown_msgs)
            else:
                LOG.warning("Could not send teardown messages to Veins.")
            self._is_processing_request = False
            self._connection.close()
            self._connection = None
        LOG.debug("Veins protocol teardown complete.")


class VeinsInterface:
    """
    Interface to Veins C2X simulator.
    """

    _last_step: Optional[asyncio.Task]

    def __init__(
        self,
        veins_host,
        veins_max_vehicles,
        *,
        veins_port=DEFAULTS["veins_port"],
        veins_fellow_filter=DEFAULTS["veins_fellow_filter"],
        veins_threshold=None,
        sync_interval_ms=DEFAULTS["sync_interval_ms"],
        geo_projection=None,
        **ignored_kwargs
    ):
        self._addr = "tcp://{}:{}".format(veins_host, veins_port)
        assert sync_interval_ms
        self._sync_interval_s = sync_interval_ms / 1e3
        self._current_time_s = None
        self._context = Context.instance()  # possbily externalize
        self._protocol = None
        self._is_processing_request = False
        self._rt_filter = TrafficFilter(
            filter_function=FELLOW_FILTERS[veins_fellow_filter],
            prune_egos=False,
            filter_kwargs={"max_vehicles": veins_max_vehicles},
        )
        self._threshold = veins_threshold
        self._repro_filter = None
        self._last_step = None
        if PROTO.isEnabledFor(logging.DEBUG):
            # add filter with pass-all filtering function
            # (to track all traffic for reproduction traces)
            self._repro_filter = TrafficFilter(
                lambda traffic, ego_vehicles, **kwd: traffic,
                prune_egos=False,
            )
        self._geo_projection = geo_projection
        if self._geo_projection is None:
            LOG.warning(
                "Geo projection not initialized, "
                "will not be able to derive lat/lon coordinates!"
            )

    @classmethod
    def get_parser(cls, defaults):
        """Return argument parser for this interface's configuration."""
        veins_parser = argparse.ArgumentParser(add_help=False)
        veins_group = veins_parser.add_argument_group("Veins Interface")
        veins_group.add_argument(
            "--veins-host",
            help=(
                "Host running the Veins server. "
                "If omitted, no connection to Veins is made."
            ),
        )
        veins_group.add_argument(
            "--veins-port",
            type=int,
            help="Port of the Veins server (default: {}).".format(
                defaults["veins_port"]
            ),
        )
        veins_group.add_argument(
            "--sync-interval-ms",
            type=int,
            help=(
                "Synchronization interval length in milliseconds "
                "(default: {}).".format(defaults["sync_interval_ms"])
            ),
        )
        veins_group.add_argument(
            "--veins-max-vehicles",
            type=lambda string: int(string) if string != "None" else None,
            help=(
                "Maximum number for vehicles synced to Veins, "
                "None means unlimited "
                "(default: {}).".format(defaults["veins_max_vehicles"])
            ),
        )
        veins_group.add_argument(
            "--veins-fellow-filter",
            choices=list(FELLOW_FILTERS.keys()),
            default=defaults["veins_fellow_filter"],
            help="Filter mechanism to select fellow vehicles.",
        )
        veins_group.add_argument(
            "--veins-threshold",
            type=lambda string: float(string) if string != "None" else None,
            default=None,
            help=(
                "Computation time veins should not exceed, "
                "used to adapt number of vehicles, ratio of the sync interval."
            ),
        )
        return veins_parser

    async def init(self, start_time_ms, network_init_data):
        """
        Connect to Veins and forward time until maneuver start.
        """
        connection = self._context.socket(zmq.REQ)
        connection.connect(self._addr)
        self._protocol = VeinsProtocol(connection)
        self._current_time_s = 0
        # wait for init subscription by veins and send init message
        LOG.debug("Socket for Veins set up, waiting for connection...")
        msg = make_network_init_message(
            network_init_data, start_time_ms / 1e3, self._sync_interval_s
        )
        await self._protocol.communicate([msg])
        if self._repro_filter:
            PROTO.debug(
                "networkInit,%s", base64.b64encode(msg).decode("ascii")
            )
        LOG.info("Connection to Veins established.")

    async def teardown(self):
        """
        Tear down the interface and underlying connection
        """
        LOG.debug("Veins teardown started...")
        with TRACER.complete("teardownInterface", tid="veins"):
            if self._protocol:
                teardown_msg = asmp.Message()
                teardown_msg.session.teardown.SetInParent()
                teardown_msg_bytes = teardown_msg.SerializeToString()
                if self._repro_filter:
                    PROTO.debug(
                        "teardown,%s",
                        base64.b64encode(teardown_msg_bytes).decode("ascii"),
                    )
                await self._protocol.teardown([teardown_msg_bytes])
            if self._context:
                self._context.destroy()
                self._context = None
        LOG.info("Veins teardown complete.")

    async def advance(
            self,
            ego_vehicles: FrozenSet[Vehicle],
            traffic: FrozenSet[Vehicle],
    ) -> VeinsResult:
        """
        Schedule the next update to Veins and return last results.
        """
        if self._last_step is None:
            # very first step
            self._last_step = asyncio.create_task(
                self.simulate_step(traffic, ego_vehicles)
            )
            return VeinsResult(None, None)

        # fetch last traffic results
        if not self._last_step.done():
            # TODO: add timing to logging
            LOG.error(
                "Last Veins step did not finish before next call to advance."
            )
            await asyncio.wait([self._last_step])
        result = self._last_step.result()
        # shedule next simulation step
        self._last_step = asyncio.create_task(
            self.simulate_step(traffic, ego_vehicles)
        )
        return result

    async def simulate_step(
            self,
            traffic: FrozenSet[Vehicle],
            ego_vehicles: FrozenSet[Vehicle],
            **ignored_kwd
    ):
        """
        Send periodic traffic update to Veins.
        """

        start_time = TRACER.ts()
        TRACER.begin("simulateStep", ts=start_time, tid="veins")
        # filter / select fellows from traffic and bui
        with TRACER.complete("filter", tid="veins"):
            traffic_changes = self._rt_filter.derive_changes(
                traffic,
                ego_vehicles,
            )
        LOG.info(
            (
                "Sending traffic to Veins at %.1fs "
                "(%d new, %d updated, %d removed vehicles, "
                "includes %d ego vehicles)"
            ),
            self._current_time_s,
            len(traffic_changes["add"]),
            len(traffic_changes["mod"]),
            len(traffic_changes["rem"]),
            len(ego_vehicles),
        )
        num_changes = {key: len(val) for key, val in traffic_changes.items()}
        with TRACER.complete("makeMessage", tid="veins", args=num_changes):
            traffic_bytes = make_traffic_message(
                traffic_changes=traffic_changes,
                ego_vehicles=ego_vehicles,
                current_time_s=self._current_time_s,
                geo_projection=self._geo_projection,
            )

        # trace all traffic for reproduction traces if enabled
        if self._repro_filter:
            with TRACER.complete("traceForReproduction", tid="veins"):
                all_traffic_changes = self._repro_filter.derive_changes(
                    traffic, ego_vehicles
                )
                all_traffic_encoded_bytes = base64.b64encode(
                    make_traffic_message(
                        traffic_changes=all_traffic_changes,
                        ego_vehicles=ego_vehicles,
                        current_time_s=self._current_time_s,
                        geo_projection=self._geo_projection,
                    )
                )
                PROTO.debug(
                    "allTraffic,%s", all_traffic_encoded_bytes.decode("ascii")
                )

        # wait for ready message from veins and send messages
        LOG.debug(
            "Waiting for ready message from Veins for time %.2fs...",
            self._current_time_s,
        )
        before_send_time = TRACER.ts()
        received_frames = await self._protocol.communicate([traffic_bytes])
        reply_receeived_time = TRACER.ts()
        TRACER.begin("simulate", ts=before_send_time, tid="veins")
        TRACER.end(
            "simulate",
            ts=reply_receeived_time,
            tid="veins",
            args={
                "num_vehicles": num_changes["add"]
                + num_changes["mod"]
                - num_changes["rem"]
            },
        )
        TRACER.begin("processReply", tid="veins")

        # advance maneuver time after veins has responded
        self._current_time_s += self._sync_interval_s

        # process results
        found_time_reached = False
        visualization_commands = []
        vehicle_commands = []
        ready_msg = asmp.Message()
        for frame in received_frames:
            ready_msg.ParseFromString(frame)
            if ready_msg.HasField("session"):
                found_time_reached = True
                # assert ready_msg.session.time_reached.HasField("time_s")
                assert math.isclose(
                    ready_msg.session.time_reached.time_s, self._current_time_s
                )
            elif ready_msg.HasField("visualization"):
                LOG.info("Appending visualization commands…")
                for vis_cmd in ready_msg.visualization.commands:
                    visualization_commands.append(vis_cmd)
            elif ready_msg.HasField("vehicle"):
                LOG.info("Veins sent vehicle message")
                for veh_cmd in ready_msg.vehicle.commands:
                    vehicle_commands.append(veh_cmd)
        assert found_time_reached
        if visualization_commands:
            LOG.debug(
                "Received %d visualization commands",
                len(visualization_commands),
            )
        if vehicle_commands:
            LOG.debug("Received %d vehicle commands", len(vehicle_commands))
        TRACER.end("processReply", tid="veins")

        finish_time = TRACER.ts()
        TRACER.end("simulateStep", ts=finish_time, tid="veins")

        with TRACER.complete("computeThreshold", tid="veins"):
            # TODO: extract or reduce/remove
            veins_preprocess_ratio = (
                before_send_time - start_time
            ) / self._sync_interval_s
            veins_simulation_ratio = (
                reply_receeived_time - before_send_time
            ) / self._sync_interval_s
            veins_postprocess_ratio = (
                finish_time - reply_receeived_time
            ) / self._sync_interval_s
            total_ratio = (finish_time - start_time) / self._sync_interval_s
            LOG.trace(
                "Preparations took a portion of %.3f of the sync interval",
                veins_preprocess_ratio,
            )
            LOG.trace(
                (
                    "Veins took a portion of %.3f of the sync interval "
                    "to simulate and reply for %d (of %s) vehicles"
                ),
                veins_simulation_ratio,
                len(traffic_changes["add"]) + len(traffic_changes["mod"]),
                self._rt_filter._filter_kwargs["max_vehicles"],
            )
            LOG.trace(
                "Postprocessing took a portion of %.3f of the sync interval",
                veins_postprocess_ratio,
            )
            LOG.debug("Total processing portion: %.3f", total_ratio)

            # dynamically adapt number of vehicles syned to veins
            if self._threshold is not None:
                if (
                    abs(self._threshold - veins_simulation_ratio) > 0.02
                ):  # deadzone
                    per_vehicle = (
                        veins_simulation_ratio
                        / self._rt_filter._filter_kwargs["max_vehicles"]
                    )
                    new_max_vehicles = int(self._threshold / per_vehicle)
                    LOG.info(
                        (
                            "Adjusting max vehicles from %d to %d "
                            "(ratio per vehicle: %.3f)"
                        ),
                        self._rt_filter._filter_kwargs["max_vehicles"],
                        new_max_vehicles,
                        per_vehicle,
                    )
                    self._rt_filter._filter_kwargs[
                        "max_vehicles"
                    ] = new_max_vehicles

        return VeinsResult(
            visualization=visualization_commands,
            vehicle=vehicle_commands,
        )
