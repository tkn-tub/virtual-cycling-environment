from __future__ import annotations
from typing import List, Tuple, Union
import typing

import yaml
import traci
import time
from copy import copy

from .util import empty_dict_if_none
from .state import VehicleSignal
import evi
if typing.TYPE_CHECKING:
    from .sumo import SumoInterface


class TriggerCollection:
    """
    Represents a number of triggers (instances of Trigger)
    and a default configuration for these triggers.
    Each trigger can, for example, cause the spawning of cars,
    make any number of individual cars
    stop or resume, or activate turning signals.

    Instances of this class can be loaded from or saved to a YAML file.
    """

    def __init__(
            self,
            triggers_max_radius: float = 3,
            default_vehicle_type: str = 'default',
            triggers_filename: str = None
    ):
        """
        :param triggers_max_radius: Maximum radius of any trigger in this
            collection.
            Such an upper bound is needed for the kd-tree in
            SumoTrafficSpawningManager, which is periodically being queried
            for any triggers around the ego vehicle within this maximum radius.
        :param default_vehicle_type: Must correspond to a vehicle type in
            the *.rou.xml for SUMO.
        :param triggers_filename: YAML filename.
            Leave blank if you're creating a new TriggerCollection
            from scratch.
        """
        self.triggers_max_radius = triggers_max_radius
        self.default_vehicle_type = default_vehicle_type

        if triggers_filename is not None:
            with open(triggers_filename, 'r') as f:
                triggers_yaml = yaml.load(f, Loader=yaml.SafeLoader)
            self.triggers_max_radius = triggers_yaml['config'].get(
                'triggers_max_radius', self.triggers_max_radius)
            self.default_vehicle_type = triggers_yaml['config'].get(
                'default_vehicle_type', self.default_vehicle_type)

            self.triggers = [
                Trigger(existing_yaml_dict=d)
                for d in triggers_yaml['triggers']
            ]
        else:
            self.triggers = []

    def __getitem__(self, item):
        return self.triggers[item]

    def save(self, triggers_filename: str):
        d = {
            'config': {
                **empty_dict_if_none(
                    'triggers_max_radius',
                    self.triggers_max_radius
                ),
                **empty_dict_if_none(
                    'default_vehicle_type',
                    self.default_vehicle_type
                ),
            },
            'triggers': [t.to_yaml_dict() for t in self.triggers]
        }
        with open(triggers_filename, 'w') as f:
            yaml.dump(d, f, default_flow_style=False)


class TriggerEvent:

    def __init__(self):
        pass

    def to_yaml_dict(self) -> dict:
        # Abstract
        pass

    def apply_to_traci(
            self,
            connection: traci.Connection,
            sumo_interface: 'SumoInterface',
            trigger_collection: TriggerCollection
    ):
        # Abstract
        pass


class StopWaypoint:
    """
    Make a vehicle stop (temporarily) somewhere along its route.
    Typically part of a SpawnEvent.
    """

    def __init__(
            self,
            edge: str = None,
            end_pos: float = 1.0,
            lane_index: int = 0,
            duration: float = -1073741824,
            start_pos: float = -1073741824,
            until: float = -1073741824,
            existing_yaml_dict: dict = None,
    ):
        """
        :param edge: ID of the edge on which to stop.
        :param end_pos: 'pos' in traci._vehicle.setStop corresponds to the
            endPos of a stop:
            https://github.com/eclipse/sumo/blob/4f2d9c278dc63a785ac8c1a68dd3a6e61e18bd3b/src/microsim/MSVehicle.cpp#L5299
            The current version of the SUMO Wiki (as of 2019-01-10) does not
            specify how start and end of a
            stop are to be interpreted, but they must be at least .1 m apart:
            http://sumo.dlr.de/wiki/Definition_of_Vehicles,_Vehicle_Types,_and_Routes#Stops
        :param lane_index:
        :param duration: Stop duration in seconds.
        :param start_pos: According to the C++ implementation
            (and errors being thrown accordingly),
            startPos must not be negative and startPos < pos must hold:
            https://github.com/eclipse/sumo/blob/4f2d9c278dc63a785ac8c1a68dd3a6e61e18bd3b/src/libsumo/Vehicle.cpp#L794
        :param until: Stop until this simulated time in seconds.
        :param existing_yaml_dict:
        """
        self.edge = edge
        self.end_pos = end_pos
        self.lane_index = lane_index
        self.duration = duration
        self.start_pos = start_pos
        self.until = until

        if existing_yaml_dict is not None:
            d = existing_yaml_dict
            self.edge = d.get('edge', self.edge)
            self.end_pos = d.get('end_pos', self.end_pos)
            self.lane_index = d.get('lane_index', self.lane_index)
            self.duration = d.get('duration', self.duration)
            self.start_pos = d.get('start_pos', self.start_pos)
            self.until = d.get('until', self.until)

    def to_yaml_dict(self) -> dict:
        return {
            **empty_dict_if_none('edge', self.edge),
            **empty_dict_if_none('end_pos', self.end_pos),
            **empty_dict_if_none('lane_index', self.lane_index),
            **empty_dict_if_none('duration', self.duration),
            **empty_dict_if_none('start_pos', self.start_pos),
            **empty_dict_if_none('until', self.until),
        }

    def apply_to_traci(
            self,
            connection: traci.Connection,
            vehicle_id: str
    ):
        # http://sumo.sourceforge.net/pydoc/traci._vehicle.html#VehicleDomain-setStop
        connection.vehicle.setStop(
            vehicle_id,
            self.edge,
            pos=self.end_pos,
            laneIndex=self.lane_index,
            duration=self.duration,
            startPos=self.start_pos,
            until=self.until
        )


class ParkingStopWaypoint:

    pass  # TODO (parked vehicles are currently not visible in Unity anyway)


class SpawnEvent(TriggerEvent):

    def __init__(
            self,
            num_vehicles: int = 1,
            route_id: str = None,
            vehicle_id: str = None,
            vehicle_type: str = None,
            depart_delay_seconds: float = None,
            depart_time_seconds: float = None,
            route_edges: List[str] = None,
            depart_pos: Union[float, str] = 'base',
            depart_lane: Union[int, str] = 'first',
            depart_speed: Union[float, str] = 0,
            arrival_lane: Union[int, str] = 'current',
            arrival_pos: Union[float, str] = 'max',
            arrival_speed: Union[float, str] = 'current',
            stops: List[StopWaypoint] = None,
            existing_yaml_dict: dict = None,
    ):
        """
        :param num_vehicles: How many vehicles to spawn with the exact same
            configuration.
            By default, SUMO should wait for one car to move before the
            next car is spawned in the same position.
        :param route_id:
        :param vehicle_id:
        :param vehicle_type:
        :param depart_delay_seconds:
        :param depart_time_seconds:
        :param route_edges:
        :param depart_pos:
        :param depart_lane:
        :param depart_speed:
        :param arrival_lane:
        :param arrival_pos:
        :param arrival_speed:
        :param stops:
        :param existing_yaml_dict:
        """
        super().__init__()

        self.num_vehicles = num_vehicles
        self.route_id = route_id
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.depart_delay_seconds = depart_delay_seconds
        self.depart_time_seconds = depart_time_seconds
        self.route_edges = route_edges
        self.depart_pos = depart_pos
        self.depart_lane = depart_lane
        self.depart_speed = depart_speed
        self.arrival_lane = arrival_lane
        self.arrival_pos = arrival_pos
        self.arrival_speed = arrival_speed
        self.stops = stops if stops is not None else []
        # TODO: parking_stops

        # Yes, this is lots of duplicate writing,
        # but if I were to write a helper function making use of self.__dict__,
        # ordinary code completion (at least in PyCharm) wouldn't know that
        # these member variables exist…

        if existing_yaml_dict is not None:
            d = existing_yaml_dict
            self.num_vehicles = d.get('num_vehicles', self.num_vehicles)
            self.route_id = d.get('route_id', self.route_id)
            self.vehicle_id = d.get('vehicle_id', self.vehicle_id)
            self.vehicle_type = d.get('vehicle_type', self.vehicle_type)
            self.depart_delay_seconds = d.get(
                'depart_delay_seconds',
                self.depart_delay_seconds
            )
            self.depart_time_seconds = d.get(
                'depart_time_seconds',
                self.depart_time_seconds
            )
            self.route_edges = d.get('route_edges', self.route_edges)
            self.depart_pos = d.get('depart_pos', self.depart_pos)
            self.depart_lane = d.get('depart_lane', self.depart_lane)
            self.depart_speed = d.get('depart_speed', self.depart_speed)
            self.arrival_lane = d.get('arrival_lane', self.arrival_lane)
            self.arrival_pos = d.get('arrival_pos', self.arrival_pos)
            self.arrival_speed = d.get('arrival_speed', self.arrival_speed)

            for stop_dict in d.get('stops', []):
                self.stops.append(StopWaypoint(existing_yaml_dict=stop_dict))

    def to_yaml_dict(self) -> dict:
        stops = None if len(self.stops) == 0 else [
            s.to_yaml_dict() for s in self.stops
        ]

        return {
            **empty_dict_if_none('num_vehicles', self.num_vehicles),
            **empty_dict_if_none('route_id', self.route_id),
            **empty_dict_if_none('vehicle_id', self.vehicle_id),
            **empty_dict_if_none('vehicle_type', self.vehicle_type),
            **empty_dict_if_none(
                'depart_delay_seconds',
                self.depart_delay_seconds
            ),
            **empty_dict_if_none(
                'depart_time_seconds',
                self.depart_time_seconds
            ),
            **empty_dict_if_none('route_edges', self.route_edges),
            **empty_dict_if_none('depart_pos', self.depart_pos),
            **empty_dict_if_none('depart_lane', self.depart_lane),
            **empty_dict_if_none('depart_speed', self.depart_speed),
            **empty_dict_if_none('arrival_lane', self.arrival_lane),
            **empty_dict_if_none('arrival_pos', self.arrival_pos),
            **empty_dict_if_none('arrival_speed', self.arrival_speed),
            **empty_dict_if_none('stops', stops),
        }

    def apply_to_traci(
            self,
            connection: traci.Connection,
            sumo_interface: 'SumoInterface',
            trigger_collection: TriggerCollection
    ):
        """
        Spawn the vehicles defined by this event.
        Corresponding SUMO/TraCI documentation:
        http://sumo.sourceforge.net/pydoc/traci._vehicle.html

        :param connection:
        :param sumo_interface:
        :param trigger_collection: The parent TriggerCollection with the
            desired default trigger (event) properties.
        :return:
        """

        dyn_id = str(time.time())
        route_id = (
            self.route_id
            if self.route_id is not None
            else f"dyn_route_{dyn_id}"
        )
        if self.route_edges is not None and len(self.route_edges) > 0:
            connection.route.add(route_id, self.route_edges)

        for i in range(self.num_vehicles):
            vehicle_id = (
                self.vehicle_id + (f'_{i}' if self.num_vehicles > 1 else '')
                if self.vehicle_id is not None
                else f'dyn_vehicle_{dyn_id}_{i}'
            )
            depart = (
                sumo_interface.current_time + self.depart_delay_seconds
                if self.depart_delay_seconds is not None
                else self.depart_time_seconds  # may be None
            )
            type_id = (
                self.vehicle_type
                if self.vehicle_type is not None
                else trigger_collection.default_vehicle_type
            )
            print(
                f"Spawning vehicle:\n"
                f"\tvehicle_id={vehicle_id}\n"
                f"\troute_id={route_id}\n"
                f"\ttypeID={type_id}\n"
                f"\tdepart={depart}\n"
                f"\tdepartLane={self.depart_lane}\n"
                f"\tdepartPos={self.depart_pos}\n"
                f"\tdepartSpeed={self.depart_speed}\n"
                f"\tarrivalLane={self.arrival_lane}\n"
                f"\tarrivalPos={self.arrival_pos}\n"
                f"\tarrivalSpeed={self.arrival_speed}\n"
            )
            connection.vehicle.addFull(
                vehicle_id,
                route_id,
                typeID=type_id,
                depart=str(depart if depart is not None else 'now'),
                departLane=str(self.depart_lane),
                departPos=str(self.depart_pos),
                departSpeed=str(self.depart_speed),
                arrivalLane=str(self.arrival_lane),
                arrivalPos=str(self.arrival_pos),
                arrivalSpeed=str(self.arrival_speed)
            )

            for stop_waypoint in self.stops:
                stop_waypoint.apply_to_traci(
                    connection=connection,
                    vehicle_id=vehicle_id
                )


class ResumeEvent(TriggerEvent):

    def __init__(
            self,
            vehicle_id: str = None,
            existing_yaml_dict: dict = None,
    ):
        super().__init__()
        self.vehicle_id = vehicle_id

        if existing_yaml_dict is not None:
            d = existing_yaml_dict
            self.vehicle_id = d.get('vehicle_id', self.vehicle_id)

    def to_yaml_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
        }

    def apply_to_traci(
            self,
            connection: traci.Connection,
            sumo_interface: 'SumoInterface',
            trigger_collection: TriggerCollection
    ):
        try:
            connection.vehicle.resume(self.vehicle_id)
        except traci.TraCIException as e:
            # In most cases probably because there is no vehicle with that ID.
            evi.sumo.interface.LOG.warning(
                f"Could not resume vehicle \"{self.vehicle_id}\": {e}"
            )


class SignalEvent(TriggerEvent):

    def __init__(
            self,
            vehicle_id: str = None,
            active_signals: List[VehicleSignal] = None,
            existing_yaml_dict: dict = None,
    ):
        super().__init__()
        self.vehicle_id = vehicle_id
        self.active_signals = (
            active_signals if active_signals is not None else []
        )

        if existing_yaml_dict is not None:
            d = existing_yaml_dict
            self.vehicle_id = d.get('vehicle_id', self.vehicle_id)
            for s in d.get('set_signals', []):
                self.active_signals.append(VehicleSignal[s])

    def to_yaml_dict(self) -> dict:
        signal_names = None if len(self.active_signals) == 0 else [
            s.name for s in self.active_signals
        ]
        return {
            'vehicle_id': self.vehicle_id,
            **empty_dict_if_none('set_signals', signal_names)
            # ^ If there are no signals to set, all signals will be
            # deactivated by this event.
        }

    def apply_to_traci(
            self,
            connection: traci.Connection,
            sumo_interface: 'SumoInterface',
            trigger_collection: TriggerCollection
    ):
        signals = 0
        for signal_state in self.active_signals:
            signals |= signal_state.value
        try:
            evi.sumo.LOG.warning(
                f"Setting signal {self.active_signals} for {self.vehicle_id}"
            )
            connection.vehicle.setSignals(self.vehicle_id, signals)
        except traci.TraCIException as e:
            # In most cases probably because there is no vehicle with that ID.
            evi.sumo.LOG.warning(
                f"Could not set signals for vehicle \"{self.vehicle_id}\": {e}"
            )


class Trigger:

    def __init__(
            self,
            trigger_radius: float = None,
            note: str = None,
            events: List[TriggerEvent] = None,
            ego_xy: Tuple[float, float] = None,
            ego_edge: str = None,
            ego_edge_pos: float = None,
            existing_yaml_dict: dict = None
    ):
        """
        :param trigger_radius: Trigger will be triggered if the vehicle is
            within this radius.
            If not given, trigger_collection.triggers_max_radius will be used.
        :param note: An optional note for improved readability of the YAML
            file or for helpful logging messages.
        :param events: The events to be triggered by this Trigger.
        :param ego_xy: Position of the ego vehicle in SUMO coordinates.
            The ego vehicle must be within trigger_radius distance of this
            trigger for the trigger to fire.
            ego_xy has precedence over ego_edge and ego_edge_pos.
        :param ego_edge: If ego_xy is not given, use this and ego_edge_pos to
            calculate the absolute position.
        :param ego_edge_pos: If ego_xy is not given, use this and ego_edge to
            calculate the absolute position.
        :param existing_yaml_dict: Properties set in this dict will override
            other arguments given to this constructor.
            If the events argument isn't empty, events from existing_yaml_dict
            will be appended.
        """
        self.was_triggered = False

        self.trigger_radius = trigger_radius
        self.note = note
        self.events: List[TriggerEvent] = events if events is not None else []
        self.ego_xy = ego_xy
        self.ego_edge = ego_edge
        self.ego_edge_pos = ego_edge_pos

        if existing_yaml_dict is not None:
            d = existing_yaml_dict
            self.trigger_radius = d.get('trigger_radius', self.trigger_radius)
            self.note = d.get('note', self.note)
            self.ego_xy = d.get('ego_xy', self.ego_xy)
            self.ego_edge = d.get('ego_edge', self.ego_edge)
            self.ego_edge_pos = d.get('ego_edge_pos', self.ego_edge_pos)
            for event_dict in d.get('spawn', []):
                self.events.append(SpawnEvent(existing_yaml_dict=event_dict))
            for event_dict in d.get('resume', []):
                self.events.append(ResumeEvent(existing_yaml_dict=event_dict))
            for event_dict in d.get('signals', []):
                self.events.append(SignalEvent(existing_yaml_dict=event_dict))

    def to_yaml_dict(self) -> dict:
        spawn = []
        resume = []
        signals = []
        for event in self.events:
            if isinstance(event, SpawnEvent):
                spawn.append(event.to_yaml_dict())
            if isinstance(event, ResumeEvent):
                resume.append(event.to_yaml_dict())
            if isinstance(event, SignalEvent):
                signals.append(event.to_yaml_dict())

        return {
            **empty_dict_if_none('trigger_radius', self.trigger_radius),
            **empty_dict_if_none('note', self.note),
            **empty_dict_if_none(
                'ego_xy',
                list([float(f) for f in self.ego_xy])
                if self.ego_xy is not None else None
            ),
            **empty_dict_if_none('ego_edge', self.ego_edge),
            **empty_dict_if_none('ego_edge_pos', self.ego_edge_pos),
            **empty_dict_if_none('spawn', spawn if len(spawn) > 0 else None),
            **empty_dict_if_none(
                'resume',
                resume if len(resume) > 0 else None
            ),
            **empty_dict_if_none(
                'signals',
                signals if len(signals) > 0 else None
            ),
        }

    def __copy__(self):
        d = self.to_yaml_dict()
        return Trigger(
            existing_yaml_dict=d.copy()
        )

    def copy(self):
        return copy(self)

    def apply_to_traci(
            self,
            connection: traci.Connection,
            sumo_interface: 'SumoInterface',
            trigger_collection: TriggerCollection
    ):
        for event in self.events:
            event.apply_to_traci(
                connection=connection,
                sumo_interface=sumo_interface,
                trigger_collection=trigger_collection
            )
