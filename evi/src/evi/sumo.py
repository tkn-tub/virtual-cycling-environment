"""
SUMO simulator interface
"""
import os
import argparse
import asyncio
import concurrent.futures
import logging
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    Mapping,
    NamedTuple,
    Optional,
)

import traci.constants as tc
import traci.exceptions

from .asynctraci import AsyncTraCI
from .defaultconfig import DEFAULTS
from .state import (
    Position,
    SignalState,
    TrafficLight,
    Vehicle,
    VehicleSignal,
    VehicleStopState,
    VehicleType,
)
from .util import (
    TRACER,
    lane_to_nr,
    trace,
    get_cartesian_from_edge_pos,
)
from .triggers import (
    TriggerCollection,
    Trigger,
)

from sumolib.net import readNet
from scipy.spatial import cKDTree
# TODO: switch to rtree, which is already in use elsewhere in evi?
import numpy as np

LOG = logging.getLogger(__name__)
TRACE = logging.getLogger("trace." + __name__)


ID_LIST = tc.ID_LIST if hasattr(tc, "ID_LIST") else tc.TRACI_ID_LIST

VEHICLE_TYPE_MAPPING = {
    "passenger": VehicleType.PASSENGER_CAR,
    "truck": VehicleType.TRUCK,
    "bus": VehicleType.TRUCK,
    "bicycle": VehicleType.BICYCLE,
}

TLS_SUMO_MAPPING = {
    "o": SignalState.OFF,
    "r": SignalState.RED,
    "a": SignalState.RED_YELLOW,
    "g": SignalState.GREEN,
    "y": SignalState.YELLOW,
}


class EgoVehicleConfig(NamedTuple):
    """Sumo configuration set for ego vehicles."""

    vehicle_type: str
    route_id: str
    keep_route: int


def infer_vehicle_type(sumo_vclass: str) -> VehicleType:
    """
    Return EVI/ASM vehicle type for a given sumo vehicle class.
    """
    return VEHICLE_TYPE_MAPPING.get(sumo_vclass, VehicleType.UNDEFINED)


def filter_context_for_signal(
    context: Dict[str, Any], signal_nr: int
) -> Dict[str, Any]:
    """Return a copy of context with only signal_nr as a signal in it."""
    new_context = context.copy()
    new_context[tc.TL_RED_YELLOW_GREEN_STATE] = new_context[
        tc.TL_RED_YELLOW_GREEN_STATE
    ][signal_nr]
    assert len(new_context[tc.TL_RED_YELLOW_GREEN_STATE]) == 1
    return new_context


def extract_vehicle(id_: str, context_value: Mapping[str, Any]) -> Vehicle:
    """
    Convert SUMO/TraCI subcription message to Vehicle object.
    """
    lane_id: str = context_value[tc.VAR_LANE_ID]
    try:
        lane_nr: int = lane_to_nr(lane_id)
    except ValueError as err:
        LOG.warning("Lane number extraction failed: %s", err)
        lane_nr = -1

    return Vehicle(
        id=id_,
        position=Position(
            context_value[tc.VAR_ROAD_ID],
            context_value[tc.VAR_LANEPOSITION],
            lane_nr,
            context_value[tc.VAR_POSITION3D][0],
            context_value[tc.VAR_POSITION3D][1],
            context_value[tc.VAR_ANGLE],
            context_value[tc.VAR_POSITION3D][2],
            context_value[tc.VAR_SLOPE],
        ),
        speed=context_value[tc.VAR_SPEED],
        route=context_value[tc.VAR_ROUTE_ID],
        signals=frozenset(
            signal_class
            for signal_class in VehicleSignal
            if context_value[tc.VAR_SIGNALS] & signal_class.value
        ),
        veh_type=infer_vehicle_type(context_value[tc.VAR_VEHICLECLASS]),
        stop_states=frozenset(
            stop_state
            for stop_state in VehicleStopState
            if context_value[tc.VAR_STOPSTATE] & stop_state.value
        ),
    )


def trace_vehicles(vehicles: Iterable[Vehicle], time_ms: int):
    """Write trace line for each vehicle in vehicles."""
    if not TRACE.isEnabledFor(logging.DEBUG):
        return
    for vehicle in vehicles:
        TRACE.debug(
            "sumoResult,%d,%s,%s,%.4f,%.4f,%.4f,%.4f,%.4f",
            time_ms,
            vehicle.id,
            vehicle.position.lane_id,
            vehicle.position.s_frac,
            vehicle.position.x,
            vehicle.position.y,
            vehicle.position.angle,
            vehicle.speed,
        )


class SumoInterface:
    """
    EVI's SUMO simulator interface

    Keeps TraCI connection to SUMO traffic simulation server.
    Sends ego vehicle updates and simulation step command.
    Manages subscriptions to ego vehicle environment.
    Receives traffic updates.
    """

    _atraci: AsyncTraCI
    _ego_config: EgoVehicleConfig
    _ego_vehicle_ids: FrozenSet[str]
    _executor: concurrent.futures.ThreadPoolExecutor
    _last_step: Optional[asyncio.Task]
    _start_time_ms: int
    _subscribed_vehicles: FrozenSet[str]

    VEHICLE_SUBSCRIPTION_VAR_IDS = (
        tc.VAR_ROAD_ID,
        tc.VAR_LANE_ID,
        tc.VAR_LANEPOSITION,
        tc.VAR_SPEED,
        tc.VAR_ROUTE_INDEX,
        tc.VAR_EDGES,
        tc.VAR_POSITION3D,
        tc.VAR_ANGLE,
        tc.VAR_SIGNALS,
        tc.VAR_ROUTE_ID,
        tc.VAR_VEHICLECLASS,
        tc.VAR_SLOPE,
        tc.VAR_STOPSTATE,
    )

    TRAFFICLIGHT_SUBSCRIPTION_VAR_IDS = (
        tc.TL_CURRENT_PHASE,
        tc.TL_CURRENT_PROGRAM,
        tc.TL_NEXT_SWITCH,
        tc.TL_RED_YELLOW_GREEN_STATE,
    )

    def __init__(
        self,
        *,
        sumo_port=DEFAULTS["sumo_port"],
        sumo_host=DEFAULTS["sumo_host"],
        ego_type=DEFAULTS["ego_type"],
        ego_route_name=None,
        sumo_keep_route=0,
        triggers_file=None,
        config_file=None,
        sumo_network_file=None,
        **ignored_kwargs
    ) -> None:
        # TODO: individual configs for each ego vehicle
        self._ego_config = EgoVehicleConfig(
            ego_type,
            ego_route_name,
            sumo_keep_route,
        )
        self._ego_vehicle_ids = frozenset()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._subscribed_vehicles = frozenset()
        self._last_step = None

        self._dynamic_traffic_spawning_manager = SumoTrafficSpawningManager(
            sumo_interface=self,
            # TODO: what if config_file not given?
            triggers_file=(
                None if triggers_file is None else os.path.join(
                    os.path.dirname(config_file),
                    triggers_file
                )
            ),
            sumo_network_file=os.path.join(
                os.path.dirname(config_file),
                sumo_network_file
            )
        )

        # initialize traci connection
        self._atraci = AsyncTraCI((sumo_host, sumo_port))
        # determine sumo version
        LOG.info(
            "Connected to TraCI Server running %s",
            self._atraci.version.sumo_version,
        )

    @classmethod
    def get_parser(cls, defaults) -> argparse.ArgumentParser:
        """Return argument parser for this interface's configuration."""
        sumo_parser = argparse.ArgumentParser(add_help=False)
        sumo_group = sumo_parser.add_argument_group("Sumo Interface")
        # config to connect to running sumo instance or start sumo ourselves
        sumo_group.add_argument(
            "--sumo-host",
            help=(
                "Host running SUMO to connect to (if not launched by evi, "
                "default: {}).".format(defaults["sumo_host"])
            ),
        )
        sumo_group.add_argument(
            "--sumo-port",
            type=int,
            help="Port to use for connection to SUMO (default: {}).".format(
                defaults["sumo_port"]
            ),
        )
        sumo_group.add_argument(
            "--sumo-keep-route",
            type=int,
            choices=[0, 1, 2],
            help=(
                "Always keep on roads and route (see move to XY, "
                "default: {})?".format(defaults["sumo_keep_route"])
            ),
        )
        evi_group = sumo_parser.add_argument_group("Ego vehicle")
        evi_group.add_argument(
            "--ego-type",
            help="Ego vehicle type in SUMO (default: {}).".format(
                defaults["ego_type"]
            ),
        )
        evi_group.add_argument(
            "--ego-route-name",
            help="Name of ego vehicle route in SUMO (default: {}).".format(
                defaults["ego_route_name"]
            ),
        )
        evi_group.add_argument(
            "--triggers-file",
            "--dynamic-spawn-points-file",  # for backwards compatibility
            help=(
                "A YAML file defining trigger locations on the map. "
                "If the ego vehicle passes one of the locations, "
                "new vehicles will be spawned in the defined locations. "
                "Requires sumo_network_file."
            )
        )
        return sumo_parser

    async def warm_up_traffic(self, start_time_ms=0) -> FrozenSet[Vehicle]:
        """
        Set up connection dependent data.
        """
        # advance traffic simulation to start time
        LOG.info(
            "Advancing traffic simulation to sync start time (%s ms)",
            start_time_ms,
        )
        if start_time_ms != 0:
            # with step == 0 simulationStep performs one step, no matter what
            with TRACER.complete("advanceInitialTraffic", tid="sumo"):
                await self._atraci.simulate_step(start_time_ms)
        # subscribe to list of active vehicle ids
        await self._atraci.subscribe_vehicle("", [ID_LIST])
        # check and set time
        assert self._atraci.time_ms() == start_time_ms
        self._start_time_ms = start_time_ms
        LOG.info("Sync start time %d ms reached", self._atraci.time_ms())

        # get initial traffic and make it available to advance
        self._last_step = asyncio.create_task(self._update_traffic())
        await self._last_step
        return self._last_step.result()

    async def teardown(self) -> None:
        """
        Tear down the interface and undelying connection
        """
        LOG.debug("Sumo teardown started...")
        with TRACER.complete("teardown", tid="sumo"):
            await self._atraci.close()
        LOG.info("Sumo teardown complete.")

    async def advance(
        self, ego_vehicles: FrozenSet[Vehicle]
    ) -> FrozenSet[Vehicle]:
        """
        Schedule next traffic simulation step and return last traffic state.
        """
        # fetch last traffic results
        assert self._last_step is not None
        if not self._last_step.done():
            LOG.error(
                "Last step in Sumo did not finish before next call to advance."
            )
            await asyncio.wait([self._last_step])
        traffic = self._last_step.result()
        # shedule next simulation step
        self._last_step = asyncio.create_task(
            self._simulation_step(ego_vehicles)
        )
        return traffic

    async def _simulation_step(self, ego_vehicles) -> FrozenSet[Vehicle]:
        """
        Instruct SUMO to perform a simulation step and process traffic updates.
        """
        with TRACER.complete("updateEgos", tid="sumo"):
            await self._update_ego_vehicles(ego_vehicles)
        current_sumo_time_ms = self._atraci.time_ms()
        LOG.debug(
            "Requesting timestep after timestep %d", current_sumo_time_ms
        )
        # perform simulation step
        with TRACER.complete("simulate", tid="sumo"):
            await self._atraci.simulate_step()

        # update subscriptions and retrieve current time and traffic state
        with TRACER.complete("updateTraffic", tid="sumo"):
            vehicles = await self._update_traffic()
        ego_vehicles = frozenset(
            vehicle
            for vehicle in vehicles
            if vehicle.id in self._ego_vehicle_ids
        )

        # handle triggers
        for ego_vehicle in ego_vehicles:
            await self._dynamic_traffic_spawning_manager.step(
                ego_vehicle=ego_vehicle,
                traci_connection=self._atraci
            )

        # sanity checks and corrections for ego vehicles
        with TRACER.complete("ensureEgoRoutes", tid="sumo"):
            await self._ensure_consistent_ego_routes(ego_vehicles)
        present_ego_vehicle_ids = frozenset(
            ego_vehicle.id for ego_vehicle in ego_vehicles
        )
        for ego_vehicle_id in self._ego_vehicle_ids - present_ego_vehicle_ids:
            LOG.error(
                "Ego-Vehicle '%s' not present in subscription results!",
                ego_vehicle_id,
            )
        with TRACER.complete("traceVehicles", tid="sumo"):
            trace_vehicles(ego_vehicles, current_sumo_time_ms)

        traffic = vehicles - ego_vehicles
        return traffic

    async def _update_traffic(self) -> FrozenSet[Vehicle]:
        """Update vehicle subscriptions and return current traffic"""
        # extract vehicle data
        active_vehicle_ids = frozenset(
            self._atraci.vehicle_subscription_results()[""][ID_LIST]
        )
        # subscribe to new vehicles
        added_vehicle_ids = active_vehicle_ids.difference(
            self._subscribed_vehicles
        )
        LOG.debug("Active vehicles in SUMO: %d", len(active_vehicle_ids))
        trace(
            LOG,
            "Newly added vehicles in timestep %.2f: %s",
            self._atraci.time_ms(),
            added_vehicle_ids,
        )
        for new_vehicle_id in added_vehicle_ids:
            await self._atraci.subscribe_vehicle(
                new_vehicle_id, self.VEHICLE_SUBSCRIPTION_VAR_IDS
            )
        self._subscribed_vehicles = active_vehicle_ids

        # don't just use subscription_results as is here
        # there may be other subscriptions in it, e.g. ID_LIST
        subscription_results = self._atraci.vehicle_subscription_results()
        vehicles = {
            vehicle_id: subscription_results[vehicle_id]
            for vehicle_id in self._subscribed_vehicles
        }
        trace(
            LOG, "current vehicles in SUMO: %s", list(sorted(vehicles.keys()))
        )
        with TRACER.complete("extractVehicles", tid="sumo"):
            extracted_vehicles = frozenset(
                extract_vehicle(vehicle_id, context_value)
                for vehicle_id, context_value in vehicles.items()
            )
        return extracted_vehicles

    async def _update_ego_vehicles(
        self, ego_vehicles: FrozenSet[Vehicle]
    ) -> None:
        """
        Update the state of the ego vehicles in the traffic simulation.
        """
        seen_ego_ids = set()

        for ego_vehicle in ego_vehicles:
            seen_ego_ids.add(ego_vehicle.id)
            if ego_vehicle.id not in self._ego_vehicle_ids:
                # register
                LOG.info("Registering ego vehicle '%s'", ego_vehicle.id)
                await self._atraci.add_ego_vehicle(
                    vehicle_id=ego_vehicle.id,
                    route_id=self._ego_config.route_id,
                    type_id=self._ego_config.vehicle_type,
                    depart_position="free",
                    speed=0,
                    speed_mode=0,
                    lane_change_mode=0,
                )
            else:
                # update -- but only in the step after creation
                LOG.debug(
                    "Updating Ego Vehicle %s to position %s and speed %.2f",
                    ego_vehicle.id,
                    ego_vehicle.position,
                    ego_vehicle.speed,
                )
                try:
                    await self._atraci.move_vehicle(
                        ego_vehicle.id,
                        ego_vehicle.position.x,
                        ego_vehicle.position.y,
                        ego_vehicle.position.angle,
                        self._ego_config.keep_route,
                    )
                    await self._atraci.set_vehicle_speed(
                        ego_vehicle.id,
                        ego_vehicle.speed,
                    )
                except traci.exceptions.TraCIException as ex:
                    # Remove ID from seen IDs s.t. the ego vehicle may be
                    # re-registered in the next time step:
                    seen_ego_ids.remove(ego_vehicle.id)
                    LOG.warning(
                        f"Could not update ego vehicle position or speed. "
                        "Will try to re-register in next time step. "
                        f"Ego ID: {ego_vehicle.id}, "
                        f"TraCI says: {ex}"
                    )

        for ego_id in self._ego_vehicle_ids - seen_ego_ids:
            # unregister
            LOG.info("Unregistering ego vehicle '%s' from Sumo.", ego_id)
            try:
                await self._atraci.remove_ego_vehicle(ego_id)
            except traci.exceptions.TraCIException as ex:
                LOG.warning(
                    f"Could not remove ego vehicle '{ego_id}', "
                    f"TraCI says: {ex}"
                )

        self._ego_vehicle_ids = frozenset(seen_ego_ids)

    async def network_init_data(self) -> Dict[str, Any]:
        """
        Extract network initalization data (for Veins) from Sumo.
        """
        # TODO: replace return type with (named)tuple
        res: Dict[str, Any] = {}
        res["netbounds"] = await self._atraci.get_network_boundary()
        res["polygons"] = await self._atraci.get_all_polygons()
        return res

    async def subscribe_to_trafficlights(
        self, whitelist: Optional[Iterable[str]] = None
    ) -> None:
        """
        Subscribe to traffic lights in whitelist or all if whitelist is None.
        """
        if whitelist is None:
            whitelist = await self._atraci.get_trafficlight_id_list()
        LOG.debug("Subscribing to trafficlignts: %s", whitelist)
        for tls_id in whitelist:
            await self._atraci.subscribe_trafficlight(
                tls_id, self.TRAFFICLIGHT_SUBSCRIPTION_VAR_IDS
            )

    async def update_trafficlights(self) -> FrozenSet[TrafficLight]:
        """Update trafficlight subscriptions and return current states."""
        time_s = self._atraci.time_ms() / 1000
        raw = self._atraci.trafficlight_subscription_results()
        result = frozenset(
            TrafficLight(
                id=tls_id,
                signals=tuple(
                    TLS_SUMO_MAPPING[char.lower()]
                    for char in context[tc.TL_RED_YELLOW_GREEN_STATE]
                ),
                phase_nr=context[tc.TL_CURRENT_PHASE],
                program_id=context[tc.TL_CURRENT_PROGRAM],
                time_to_switch=round(context[tc.TL_NEXT_SWITCH] - time_s, 3),
            )
            for tls_id, context in raw.items()
        )
        return result

    async def _ensure_consistent_ego_routes(
        self, ego_vehicles: Iterable[Vehicle]
    ) -> None:
        """
        Check if ego vehicle's routes match the configuration and set otherwise
        """
        if self._ego_config.keep_route == 2:
            # routes are not used with freely controlled vehicles
            return

        # TODO: adapt for separate routes of ego vehicles
        ego_route_name = self._ego_config.route_id
        for ego_vehicle in ego_vehicles:
            route_inconsistent_in_sumo = ego_vehicle.route is None or (
                ego_vehicle.route != ego_route_name
                and not ego_vehicle.route.startswith(":")
            )
            if route_inconsistent_in_sumo:
                LOG.debug(
                    "Re-Setting route ID of ego vehicle '%s': "
                    "fron '%s' to '%s'.",
                    ego_vehicle.id,
                    ego_vehicle.route,
                    ego_route_name,
                )
                await self._atraci.set_vehicle_route_id(
                    ego_vehicle.id, ego_route_name
                )


class SumoTrafficSpawningManager:
    """
    Based on the given dynamic_spawn_points_file YAML configuration,
    an instance of this class will
    check if the ego vehicle is in a position to trigger the spawning of a
    defined number of vehicles at the pre-defined locations specified
    in the same file.
    """

    def __init__(
            self,
            sumo_interface: SumoInterface,
            triggers_file: str,
            sumo_network_file: str,
    ):
        """
        :param dynamic_spawn_points_file: YAML file that defines the trigger
            locations and the respective traffic to be generated.
        :param sumo_network_file: SUMO *.net.xml file.
            We need this for converting positions on lanes to Cartesian
            coordinates.
        """
        self.sumo_interface = sumo_interface
        self.has_triggers = False
        self.kd_tree = None

        if not triggers_file:
            LOG.warning(
                "No triggers_file -> Skipping triggers initialization."
            )
            return
        self.trigger_collection = TriggerCollection(
            triggers_filename=triggers_file
        )

        if len(self.trigger_collection.triggers) == 0:
            return

        self.triggers_by_pos: Dict[tuple, Trigger] = {}
        """
        Keys: x-y-coordinate of the trigger as a tuple.\n
        Values: Reference to the trigger defined in the YAML.
        """

        # Since some of the trigger points are given only by an edge and a
        # position on this edge, we need to convert all positions to Cartesian
        # coordinates first for the kd-tree to work:
        net = readNet(sumo_network_file)

        for trigger in self.trigger_collection.triggers:
            pos = (
                trigger.ego_xy
                if trigger.ego_xy is not None else
                get_cartesian_from_edge_pos(
                    net,
                    trigger.ego_edge,
                    trigger.ego_edge_pos,
                )
            )
            if pos is None:
                LOG.error(
                    f"Invalid edge_pos definition for trigger: "
                    # edge id:
                    f"ego_edge={trigger.ego_edge}, "
                    # offset from start of the edge in meters:
                    f"ego_edge_pos={trigger.ego_edge_pos}"
                )
                continue
            self.triggers_by_pos[tuple(pos)] = trigger

        # A kd-tree lets us quickly query which pre-defined points are
        # closest to another given point.
        self.trigger_points = list(self.triggers_by_pos.keys())
        self.kd_tree = cKDTree(data=self.trigger_points)
        self.has_triggers = True

    async def step(
            self,
            ego_vehicle,
            traci_connection: AsyncTraCI,
    ):
        if not self.has_triggers:
            return
        if self.kd_tree is None:
            LOG.warning("triggers: kd_tree is None")
            return
        if ego_vehicle is None:
            LOG.warning("triggers: ego_vehicle is None")
            return

        # 2D position of the ego vehicle:
        current_ego_pos = np.array([
            ego_vehicle.position.x,
            ego_vehicle.position.y,
            0,
        ])

        (
            distances_of_nearest_points,
            indices_of_nearest_points
        ) = self.kd_tree.query(
            current_ego_pos,
            # In this case, our maximum number of overlapping triggers:
            k=32,
            # Get k nearest neighbors within this bound.
            # Keep in mind that individual triggers may define a trigger
            # radius below this value!
            distance_upper_bound=self.trigger_collection.triggers_max_radius
        )

        for distance, point_index in zip(
                distances_of_nearest_points,
                indices_of_nearest_points
        ):
            if distance > self.trigger_collection.triggers_max_radius:
                # KDTree returns results sorted by distance,
                # so we can assume that from this point onwards
                # there won't be any useful data.
                break
            point = self.trigger_points[point_index]
            trigger = self.triggers_by_pos[tuple(point)]
            trigger_radius = (
                trigger.trigger_radius
                if trigger.trigger_radius is not None
                else self.trigger_collection.triggers_max_radius
            )
            distance = np.linalg.norm(np.array(point) - current_ego_pos)

            if distance > trigger_radius or trigger.was_triggered:
                continue
            trigger.was_triggered = True

            LOG.info(
                f"Processing trigger at {point} with note \"{trigger.note}\""
            )
            trigger.apply_to_traci(
                connection=traci_connection.connection,
                sumo_interface=self.sumo_interface,
                trigger_collection=self.trigger_collection
            )
