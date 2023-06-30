"""
Collection of handlers that process incoming requests.
"""

import asyncio
import itertools as it
import logging
from typing import (
    Callable,
    Dict,
    FrozenSet,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
)

import asmp.asmp.horizon_pb2 as horizon_pb2
import asmp.asmp_pb2 as asmp
import sumolib
import typing_extensions

from . import routehelper
from .asynctraci import PoiTracer
from .filtering import FELLOW_FILTERS, TrafficFilter
from .proto import (
    build_horizon_tls_response,
    build_traffic_message,
    build_trafficlight_message,
    protobuf_to_vehicle,
)
from .state import Vehicle
from .sumo import SumoInterface
from .util import ID_MAPPER, TRACER, trace
from .veins import VeinsInterface, VeinsResult

LOG = logging.getLogger(__name__)

GeoProjection = Callable[[float, float], Tuple[float, float]]


class RequestHandler(typing_extensions.Protocol):
    """
    Handler for protocols to process certain requests sent to the EVI.
    """

    @staticmethod
    def is_responsible(message: asmp.Message) -> bool:
        """Return true if this handler is response to process message."""
        ...

    async def process(self, message: asmp.Message) -> Sequence[asmp.Message]:
        """Process message and return replies."""
        ...


class InvalidRequest(Exception):
    """
    General Exception for errors resulting from defunct communication with ASM
    """


def extract_vehicle_updates(
    commands: Sequence,
    previous_vehicles: FrozenSet[Vehicle],
    register_from_update: bool,
) -> FrozenSet[Vehicle]:
    """
    Extract an update set of vehicles from the message commands.
    """
    register_commands = (
        cmd.register_vehicle_command
        for cmd in commands
        if cmd.HasField("register_vehicle_command")
    )
    update_commands = (
        cmd.update_vehicle_command
        for cmd in commands
        if cmd.HasField("update_vehicle_command")
    )
    unregister_commands = (
        cmd.unregister_vehicle_command
        for cmd in commands
        if cmd.HasField("unregister_vehicle_command")
    )

    ego_vehicles = {vehicle.id: vehicle for vehicle in previous_vehicles}
    for cmd in register_commands:
        ego_id = ID_MAPPER.to_string(cmd.vehicle_id)
        assert ego_id not in ego_vehicles
        vehicle = protobuf_to_vehicle(cmd.vehicle_id, cmd.state, 1)
        ego_vehicles[vehicle.id] = vehicle

    for cmd in update_commands:
        ego_id = ID_MAPPER.to_string(cmd.vehicle_id)
        if ego_id not in ego_vehicles:
            if register_from_update:
                LOG.warning(
                    "Substituting registration msg with update msg for '%s'.",
                    ego_id,
                )
            else:
                raise InvalidRequest(
                    "Expected ego registration msg has no registration cmd"
                )
        vehicle = protobuf_to_vehicle(cmd.vehicle_id, cmd.state, 1)
        ego_vehicles[vehicle.id] = vehicle

    for cmd in unregister_commands:
        ego_id = ID_MAPPER.to_string(cmd.vehicle_id)
        assert ego_id in ego_vehicles
        del ego_vehicles[ego_id]

    return frozenset(ego_vehicles.values())


def make_visualization_message(
    results: Sequence[asmp.Message], time_s: float
) -> asmp.Message:
    """
    Make a visualization message to forward data from Veins to Unity.
    """
    event_message = asmp.Message()
    event_message.visualization.time_s = time_s
    for i, event_command in enumerate(results):
        event_message.visualization.commands.add()
        event_message.visualization.commands[i].CopyFrom(event_command)
    return event_message


def make_vehicle_message(
    results: Sequence[asmp.Message], time_s: float
) -> asmp.Message:
    """
    Make a vehicle message to forward data from Veins to Unity.
    """
    vehicle_message = asmp.Message()
    vehicle_message.vehicle.time_s = time_s
    for i, vehicle_command in enumerate(results):
        vehicle_message.vehicle.commands.add()
        vehicle_message.vehicle.commands[i].CopyFrom(vehicle_command)
    return vehicle_message


class RequestDispatcher:
    """
    Process requests by dispatching them to handlers.
    """

    handlers: Sequence[RequestHandler]
    shutdown_event: asyncio.Event
    shutdown_wait_task: asyncio.Task

    def __init__(
        self,
        handlers: Sequence[RequestHandler],
        shutdown_event: asyncio.Event,
    ):
        self.handlers = handlers
        self.shutdown_event = shutdown_event
        self.shutdown_wait_task = asyncio.create_task(shutdown_event.wait())

    async def yield_tasks(self, running):
        """
        Yield tasks in running once they finish, but respect shutdown triggers.
        """
        while running and running != {self.shutdown_wait_task}:
            done, pending = await asyncio.wait(
                running | {self.shutdown_wait_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if self.shutdown_wait_task in done:
                # shutdown was triggered before the request was completed
                LOG.warning("Shutdown triggered while processing request.")
                for task in pending:
                    task.cancel()
                return
            for task in done:
                yield task
                running.remove(task)

    async def process(
        self,
        message: asmp.Message,
        send_function: Callable[[Sequence[asmp.Message]], None],
    ) -> None:
        """Process a request and send back the reply."""
        TRACER.begin("process", tid="request")
        running = {
            asyncio.create_task(handler.process(message))
            for handler in self.handlers
            if handler.is_responsible(message)
        }
        if not running:
            LOG.warning(
                "Could not process message of type %s, no handler responsible",
                message.WhichOneof("message_oneof"),
            )
            return

        async for done_task in self.yield_tasks(running):
            TRACER.instant("taskDone", tid="request")
            try:
                replies = done_task.result()
            except Exception as exc:
                LOG.critical("Task procesing failed, shutting down!")
                self.shutdown_event.set()
                raise exc

            if replies:
                send_function(replies)
        TRACER.end(
            "process",
            tid="request",
            args={"msgtype": message.WhichOneof("message_oneof")},
        )


class HorizonDummyHandler:
    """
    Handles incoming Horizon requests and sends dummy replies.

    To be replaced by an actual implementation of the Horizon protocol.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def is_responsible(message: asmp.Message) -> bool:
        """Return true if this handler is response to process message."""
        return message.HasField("horizon")

    async def process(self, message: asmp.Message) -> Sequence[asmp.Message]:
        """
        Return dummy reply for horizon request.
        """
        TRACER.begin("horizon", tid="request")
        LOG.info("Received horion request")
        LOG.debug("Sending dummy response.")
        reply = asmp.Message()
        reply.horizon.time_s = -1
        for req_nr, request in enumerate(message.horizon.requests):
            reply.horizon.responses.add()
            reply.horizon.responses[req_nr].request_id = request.request_id
            reply.horizon.responses[req_nr].items.add()
            reply.horizon.responses[req_nr].items[0].variable = 0
        TRACER.end("horizon", tid="request")
        return [reply]


class HorizonEgoTrafficLightHandler:
    """
    Handles incoming Horizon requests for traffic lights along an ego's route.
    """

    def __init__(
        self, sumo_network_file: str, sumo_interface: SumoInterface
    ) -> None:
        self.poitracer = PoiTracer(sumo_interface._atraci)
        self.sumo_interface = sumo_interface
        # TODO: extract all sumo(lib)-specific code into other class/module
        self.sumo_net = sumolib.net.readNet(
            sumo_network_file,
            withInternal=True,
            withPrograms=True,
        )
        lanes = [
            lane
            for edge in self.sumo_net.getEdges()
            for lane in edge.getLanes()
            if not lane.getID().startswith(":")
        ]
        junctions = [
            node
            for node in self.sumo_net.getNodes()
            if node.getType() != "dead_end"
        ]
        self.lane_finder = routehelper.LaneFinder(lanes=lanes)
        self.junction_finder = routehelper.JunctionFinder(junctions)
        self._last_pois: List[str] = []
        self._is_subscribed = False  # FIXME: refactor / clean up

    @staticmethod
    def is_ego_tls_request(request: horizon_pb2.Request) -> bool:
        """Return whether request contains the ego tls request variable."""
        return (
            request.variables & horizon_pb2.NEXT_TLS_GREEN_PHASES
        )

    @staticmethod
    def is_responsible(message: asmp.Message) -> bool:
        """Return true if this handler is response to process message."""
        return message.HasField("horizon") and any(
            HorizonEgoTrafficLightHandler.is_ego_tls_request(req)
            for req in message.horizon.requests
        )

    async def process(self, message: asmp.Message) -> Sequence[asmp.Message]:
        """Process ego vehicle request for traffic lights along a route."""
        num_green_phases = 3  # FIXME: make this a config param
        if not self._is_subscribed:  # FIXME: refactor / clean up
            await self.sumo_interface.subscribe_to_trafficlights()

        tls_requests = [
            request
            for request in message.horizon.requests
            if self.is_ego_tls_request(request)
        ]
        LOG.debug("Received %d TLS Horizon requests.", len(tls_requests))

        all_tls_state = {
            tls.id: tls
            for tls in await self.sumo_interface.update_trafficlights()
        }

        responses = []
        for tls_request in tls_requests:
            coords = [(point.x, point.y) for point in tls_request.points]
            await self.poitracer.update(coords, owner=tls_request.vehicle_id)

            # prepare response to individual request

            route_edges = routehelper.reconstruct_route(
                coords=coords,
                lane_finder=self.lane_finder,
                junction_finder=self.junction_finder,
            )
            route_tls = routehelper.find_tls_in_route(
                route_edges=route_edges,
                sumo_net=self.sumo_net,
            )

            tls_responses = []
            for tls, link_index in route_tls:
                tls_state = all_tls_state[tls.getID()]
                program = tls.getPrograms()[tls_state.program_id]
                phase = program.getPhases()[tls_state.phase_nr]
                absolute_green_times = routehelper.get_next_green_phase_times(
                    program=program,
                    link_index=link_index,
                    current_phase_nr=tls_state.phase_nr,
                    green_phases=num_green_phases,
                )
                relative_green_times = [
                    (round(begin, 3), round(end, 3))
                    for begin, end in routehelper.offset_green_phase_times(
                        green_times=absolute_green_times,
                        passed_time=phase.duration - tls_state.time_to_switch,
                    )
                ]
                tls_coord = self.sumo_net.getNode(tls.getID()).getCoord()

                # compute road distance to junction
                _, first_edge_offset, _ = route_edges[0].getClosestLanePosDist(
                    coords[0]
                )
                edges_till_tls = list(
                    it.takewhile(
                        lambda e: e.getFromNode().getID() != tls.getID(),
                        route_edges,
                    )
                )
                via_lanes_till_tls = (
                    self.sumo_net.getLane(
                        from_edge.getConnections(to_edge)[0].getViaLaneID()
                    )
                    for from_edge, to_edge in zip(
                        edges_till_tls[:-1], edges_till_tls[1:]
                    )
                )
                road_distance = (
                    sum(edge.getLength() for edge in edges_till_tls)
                    + sum(lane.getLength() for lane in via_lanes_till_tls)
                    - first_edge_offset
                )
                tls_responses.append(
                    {
                        "id": tls.getID(),
                        "coord": tls_coord,
                        "road_distance": road_distance,
                        "green_times": relative_green_times,
                    }
                )
            responses.append((
                tls_request.request_id,
                tls_request.vehicle_id,
                tls_responses,
            ))
        return [build_horizon_tls_response(message.horizon.time_s, responses)]


class EgoVehicleUpdateHandler:
    """
    Handles incoming ego vehicle updates messages and prepares replies.

    Main protocol interaction point to synchronize traffic.
    """

    sumo_interface: SumoInterface
    veins_interface: Optional[VeinsInterface]
    shutdown_event: asyncio.Event
    _ego_vehicles: FrozenSet[Vehicle]
    _filter: TrafficFilter
    _register_from_update: bool
    _geo_projection: Optional[GeoProjection]
    _last_veins_result: Optional[VeinsResult]

    def __init__(
        self,
        sumo_interface: SumoInterface,
        veins_interface: Optional[VeinsInterface],
        shutdown_event: asyncio.Event,
        rt_fellow_filter: str,
        *,
        register_from_update: bool = False,
        rt_max_vehicles: Optional[int] = None,
        geo_projection: Optional[GeoProjection] = None,
        **_ignored_kwargs: Dict,
    ) -> None:
        self.sumo_interface = sumo_interface
        self.veins_interface = veins_interface
        self.shutdown_event = shutdown_event
        self._filter = TrafficFilter(
            filter_function=FELLOW_FILTERS[rt_fellow_filter],
            prune_egos=True,
            filter_kwargs={"max_vehicles": rt_max_vehicles},
        )
        self._register_from_update = register_from_update
        self._ego_vehicles = frozenset()
        self._geo_projection = geo_projection
        self._last_veins_result = None

    @staticmethod
    def is_responsible(message: asmp.Message) -> bool:
        """Return true if this handler is response to process message."""
        return message.HasField("vehicle")

    async def process(self, message: asmp.Message) -> Sequence[asmp.Message]:
        """
        Forward ego updates to other simulators and return traffic update.
        """
        # TODO: veins interaction

        # extract data from message
        time_s = message.vehicle.time_s
        LOG.info(
            "Received vehicle msg with %d vehicle commands at msg time %.1fs",
            len(message.vehicle.commands),
            time_s,
        )

        TRACER.begin("egohandler", tid="request")
        ego_vehicles = extract_vehicle_updates(
            message.vehicle.commands,
            self._ego_vehicles,
            self._register_from_update,
        )
        if not ego_vehicles:
            assert self._ego_vehicles
            LOG.info("Last ego vehicle unregistered, shutting down.")
            self.shutdown_event.set()
            TRACER.end("egohandler", tid="request")
            return []

        # gather traffic update
        with TRACER.complete("sumoAdvance", tid="request"):
            traffic = await self.sumo_interface.advance(ego_vehicles)

        # push updates to veins and collect results
        if self.veins_interface is not None:
            with TRACER.complete("veinsAdvance", tid="request"):
                self._last_veins_result = await self.veins_interface.advance(
                    ego_vehicles, traffic
                )

        # prepare fellow traffic to send
        ego_ids = {ego.id for ego in ego_vehicles}
        with TRACER.complete("filterFellows", tid="request"):
            fellow_changes = self._filter.derive_changes(
                {vehicle for vehicle in traffic if vehicle.id not in ego_ids},
                ego_vehicles,
            )
        LOG.info(
            "Sending fellow traffic at %.1fs (%d new, %d updated, %d removed)",
            time_s,
            len(fellow_changes["add"]),
            len(fellow_changes["mod"]),
            len(fellow_changes["rem"]),
        )

        # build message / serialize data
        fellow_message = build_traffic_message(
            fellow_changes, time_s, self._geo_projection
        )
        replies: Sequence[asmp.Message] = [fellow_message]

        # update local state
        self._ego_vehicles = ego_vehicles

        TRACER.end("egohandler", tid="request")
        return replies


class UnityEgoVehicleUpdateHandler(EgoVehicleUpdateHandler):
    """
    Handles incoming ego vehicle updates messages and prepares replies.

    Main protocol interaction point to synchronize traffic.
    Includes TrafficLight data for Unity.
    """

    def __init__(
        self,
        sumo_interface: SumoInterface,
        veins_interface: Optional[VeinsInterface],
        shutdown_event: asyncio.Event,
        rt_fellow_filter: str,
        *,
        register_from_update: bool = False,
        rt_max_vehicles: Optional[int] = None,
        geo_projection: Optional[GeoProjection] = None,
        **_ignored_kwargs: Dict,
    ) -> None:
        super().__init__(
            sumo_interface=sumo_interface,
            veins_interface=veins_interface,
            shutdown_event=shutdown_event,
            rt_fellow_filter=rt_fellow_filter,
            register_from_update=register_from_update,
            rt_max_vehicles=rt_max_vehicles,
            geo_projection=geo_projection,
            **_ignored_kwargs,
        )
        asyncio.create_task(self.sumo_interface.subscribe_to_trafficlights())

    def serialize_veins_results(self, time_s: float) -> Iterator[asmp.Message]:
        """
        Yield mesages for further replies from recent veins results.
        """
        if not self._last_veins_result:
            return

        if self._last_veins_result.visualization:
            event_message = make_visualization_message(
                self._last_veins_result.visualization,
                time_s,
            )
            LOG.info(
                (
                    "Forwarding visualization events from Veins to Unity "
                    "(%d messages)"
                ),
                len(event_message.visualization.commands),
            )
            yield event_message

        if self._last_veins_result.vehicle:
            vehicle_message = make_vehicle_message(
                self._last_veins_result.vehicle, time_s
            )
            LOG.info(
                (
                    "Forwarding vehicle update events from Veins to Unity "
                    "(%d messages)"
                ),
                len(vehicle_message.vehicle.commands),
            )
            yield vehicle_message

    async def process(self, message: asmp.Message) -> Sequence[asmp.Message]:
        """
        Forward ego updates to other simulators and return traffic update.
        """
        # use superclass to handle ego updates and traffic data
        # then just append the traffic light message
        replies = list(await super().process(message=message))

        # get trafficlight datat
        trafficlights = await self.sumo_interface.update_trafficlights()
        trace(LOG, "Sending trafficlight updates: %s", trafficlights)

        replies.append(
            build_trafficlight_message(trafficlights, message.vehicle.time_s)
        )

        replies.extend(self.serialize_veins_results(message.vehicle.time_s))

        return replies
