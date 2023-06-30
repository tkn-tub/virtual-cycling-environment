"""
Asynchronous interface to TraCI.

Use an instance of this class in asynchronous code instead of calls to traci.

Orders traci commands and allows coroutine-based access.
Internally, a asyncio.Lock is used for this.
Only one command can interact with TraCI at a time.
This is necessary as some long-running commands may be run in a thread.
Especially execting the next time step and receiving subscription results.
This should be done implicitly by using coroutines and the lock.
According to the docs, aquiring a lock is fair (FIFO).
So the order of calls should be preserved.
Though there is still the TODO: test the locking
"""

import asyncio
import concurrent.futures
import logging
from typing import (
    Any,
    Dict,
    List,
    Iterable,
    Mapping,
    NamedTuple,
    Sequence,
    Tuple,
    Union,
)

import traci
import traci.constants as tc
import traci.exceptions

LOG = logging.getLogger(__name__)


class TraCIVersion(NamedTuple):
    """Version tuple returned by TraCI."""

    api_number: int
    sumo_version: str


class NetBoundary(NamedTuple):
    """Sumo network boundary definition."""

    bottomleft: Tuple[float, float]
    topright: Tuple[float, float]


class AsyncTraCI:
    """Asynchronous Interface using TraCI"""

    version: TraCIVersion
    """Version tuple reported by the TraCI server."""

    _simtime_ms: int

    def __init__(
        self, address: Tuple, connection_class=traci.Connection
    ) -> None:
        """
        Establish a connection to `address`.
        """
        try:
            self._connection = connection_class(*address, process=None)
        except Exception:
            LOG.critical(
                "Connection to sumo failed (using address %s:%d)",
                *address,
            )
            raise
        self.version = TraCIVersion(*self._connection.getVersion())
        self._connection.simulation.subscribe([tc.VAR_TIME_STEP])
        self._lock = asyncio.Lock()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._simtime_ms = 0

    def time_ms(self) -> int:
        """Return current time in Sumo in milliseconds."""
        return self._simtime_ms

    @property
    def connection(self) -> traci.Connection:
        return self._connection

    # simulation control

    async def close(self) -> None:
        """
        Shutdown and disconnect.

        Calling this more than once is undefined behavior.
        """
        LOG.debug("Shutting down SUMO connection.")
        if self._lock.locked():
            LOG.warning("TraCI access lock is locked on close attempt!")
            await self._lock.acquire()
        self._executor.shutdown(wait=False)
        try:
            self._connection.close()
        except traci.exceptions.FatalTraCIError as exc:
            LOG.warning("Sumo shutdown raised an error: %s", exc)

    async def simulate_step(self, time_ms=None) -> None:
        """
        Advance simulation by one step or up to `time_ms`.

        Time is always given in milliseconds, thus `time_ms`.
        This function takes care of converting to traci time internally.
        """
        if time_ms is None:
            time_ms = 0
        traci_time = (
            time_ms if self.version.api_number < 18 else time_ms / 1000.0
        )
        async with self._lock:
            await asyncio.get_running_loop().run_in_executor(
                self._executor,
                self._connection.simulationStep,
                traci_time,
            )
        self._simtime_ms = (
            self._connection.simulation.getSubscriptionResults()[
                tc.VAR_TIME_STEP
            ]
        )

    # subscription control

    async def subscribe_vehicle(
        self, vehicle_id: str, variable_ids: Sequence[int]
    ) -> None:
        """
        Subscribe to get variables for vehicle_id on all coming time steps.
        """
        # TODO: design and implement a better subscription interface
        #   e.g., by using handles given out on subscription that can retrieve
        #   the most recent data on every step
        async with self._lock:
            self._connection.vehicle.subscribe(vehicle_id, variable_ids)

    def vehicle_subscription_results(self) -> Mapping[str, Mapping[str, Any]]:
        """Return most recent subscription results for all vehicles."""
        return self._connection.vehicle.getAllSubscriptionResults()

    async def subscribe_trafficlight(
        self, tls_id: str, varible_ids: Iterable[int]
    ) -> None:
        """
        Subscribe to get variables for tls_id on all coming time steps.
        """
        async with self._lock:
            self._connection.trafficlight.subscribe(tls_id, varible_ids)

    def trafficlight_subscription_results(
        self,
    ) -> Mapping[str, Mapping[int, Any]]:
        """
        Return most recent subscription results for subscribed trafficlights.
        """
        return self._connection.trafficlight.getAllSubscriptionResults()

    # vehicle control

    async def add_ego_vehicle(
        self,
        vehicle_id: str,
        route_id: str,
        type_id: str,
        depart_position: Union[float, str],
        speed: Union[float, str],
        speed_mode: int,
        lane_change_mode: int,
    ) -> None:
        """Add an ego vehicle to the simulation."""
        async with self._lock:
            self._connection.vehicle.addFull(
                vehID=vehicle_id,
                routeID=route_id,
                typeID=type_id,
                departPos=depart_position,
            )
            self._connection.vehicle.setRouteID(vehicle_id, route_id)
            # configure the vehicle to be fully remote controlled
            # (this disables checks)
            self._connection.vehicle.setSpeedMode(
                vehID=vehicle_id,
                sm=speed_mode,
            )
            self._connection.vehicle.setLaneChangeMode(
                vehID=vehicle_id,
                lcm=lane_change_mode,
            )
            # set the ego vehicle's initial speed to 0
            # all further update come next round
            self._connection.vehicle.setSpeed(
                vehID=vehicle_id,
                speed=speed,
            )

    async def set_vehicle_route_id(
        self, vehicle_id: str, route_id: str
    ) -> None:
        """Set the route of a vehicle by a route id."""
        async with self._lock:
            self._connection.vehicle.setRouteID(vehicle_id, route_id)

    async def move_vehicle(
        self,
        vehicle_id: str,
        x: float,
        y: float,
        angle: float,
        keep_route: int,
    ) -> None:
        """
        Move a vehicle to x/y coordinates.

        May raise a traci.exceptions.TraCIException if vehicle does not exist.
        """
        async with self._lock:
            self._connection.vehicle.moveToXY(
                vehID=vehicle_id,
                edgeID="",
                lane=-1,
                x=x,
                y=y,
                angle=angle,
                keepRoute=keep_route,
            )

    async def set_vehicle_speed(self, vehicle_id: str, speed: float) -> None:
        """
        Set the speed of a vehicle in meters per second.

        May raise a traci.exceptions.TraCIException if vehicle does not exist.
        """
        async with self._lock:
            self._connection.vehicle.setSpeed(vehicle_id, speed)

    async def remove_ego_vehicle(self, vehicle_id: str) -> None:
        """Remove an ego vehicle from the simulation."""
        async with self._lock:
            self._connection.vehicle.remove(vehicle_id)

    # simulation and network queries

    async def get_network_boundary(self) -> NetBoundary:
        """Return the network boundary of the road network."""
        async with self._lock:
            bottomleft, topright = self._connection.simulation.getNetBoundary()
        return NetBoundary(bottomleft, topright)

    async def get_all_polygons(self) -> Sequence[Mapping]:
        """Return a list of all polygons as dicts with id, type, and shape."""
        # TODO: add type for polygon entry (e.g., via NamedTuple)
        async with self._lock:
            return [
                {
                    "id": p_id,
                    "type": self._connection.polygon.getType(p_id),
                    "shape": self._connection.polygon.getShape(p_id),
                }
                for p_id in self._connection.polygon.getIDList()
            ]

    async def get_trafficlight_id_list(self) -> Sequence[str]:
        """Return a list of all traffig lights' ids."""
        async with self._lock:
            return self._connection.trafficlight.getIDList()

    # annotation drawing

    async def remove_pois(self, poi_ids: Iterable[str]) -> Iterable[str]:
        """Remove a collection of POIs."""
        removed_poi_ids = []
        async with self._lock:
            for poi_id in poi_ids:
                try:
                    self._connection.poi.remove(poi_id)
                    removed_poi_ids.append(poi_id)
                except traci.exceptions.TraCIException as ex:
                    LOG.warning(
                        "Could not remove POI '%s', TracCI says: %s",
                        poi_id,
                        ex,
                    )
        return removed_poi_ids

    async def add_pois(self, pois: Iterable[dict]) -> Iterable[str]:
        successful_poi_ids = []
        async with self._lock:
            for poi in pois:
                try:
                    self._connection.poi.add(**poi)
                    successful_poi_ids.append(poi["poiID"])
                except traci.exceptions.TraCIException as ex:
                    LOG.warning(
                        "Could not add POI '%s', TracCI says: %s",
                        poi["poiID"],
                        ex,
                    )
        return successful_poi_ids


class PoiTracer:
    """
    Helper class to trace Point of Interest in Sumo GUI.

    Mostly for debugging, modeled after Veins' annotation modules.
    """

    _atraci: AsyncTraCI
    _poi: Dict[str, List[str]]
    _colors: Dict[str, Tuple[float, float, float, float]]

    def __init__(self, atraci: AsyncTraCI) -> None:
        self._atraci = atraci
        self._poi = {}
        self._colors = {}

    async def update(self, coords, owner=None) -> None:
        # find and clear previous pois for owner
        last_poi = list(self._poi.get(owner, []) if owner is not None else [])
        await self._atraci.remove_pois(last_poi)

        # find or set up color for owner
        if owner not in self._colors:
            # TODO: support different colors
            self._colors[owner] = (
                0,
                0,
                255,
                255,
            )
        color = self._colors[owner]

        # create pois for coords
        new_poi = [
            {
                "x": coord[0],
                "y": coord[1],
                "poiID": f"{str(owner)}-{nr}",
                "color": color,
                "layer": 6,
            }
            for nr, coord in enumerate(coords)
        ]
        self._poi[owner] = list(await self._atraci.add_pois(new_poi))
