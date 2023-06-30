"""
Internal state representations for EVI
"""
from enum import Enum
from typing import FrozenSet, NamedTuple, Optional, Tuple


class SignalState(Enum):
    """
    State or color a traffic light can display.
    """

    OFF = 0
    RED = 1
    RED_YELLOW = 2
    GREEN = 3
    YELLOW = 4


class VehicleSignal(Enum):
    """
    Vehicle signals / indication lights.
    """

    NONE = 0
    BLINKER_RIGHT = 1
    BLINKER_LEFT = 2
    BLINKER_EMERGENCY = 4
    BREAKLIGHT = 8
    FRONTLIGHT = 16
    FOGLIGHT = 32
    HIGHBEAM = 64
    BACKDRIVE = 128
    WIPER = 256
    DOOR_OPEN_LEFT = 512
    DOOR_OPEN_RIGHT = 1024
    EMERGENCY_BLUE = 2048
    EMERGENCY_RED = 4096
    EMERGENCY_YELLOW = 8192


class VehicleType(Enum):
    """
    Type or class of vehicle.
    """

    UNDEFINED = 0
    PASSENGER_CAR = 1
    TRUCK = 2
    BICYCLE = 3


class VehicleStopState(Enum):
    """
    Vehicle stop states.
    """

    STOPPED = 1
    PARKING = 2
    TRIGGERED = 4
    CONTAINER_TRIGGERED = 8
    AT_BUS_STOP = 16
    AT_CONTAINER_STOP = 32
    AT_CHARGING_STATION = 64
    AT_PARKING_AREA = 128


class Position(NamedTuple):
    """
    Position of a Vehicle.
    """

    road_id: str
    s_frac: float
    lane_id: int
    x: float
    y: float
    angle: float
    height: float
    slope: float


class Vehicle(NamedTuple):
    """
    State of a vehicle.
    """

    id: str
    position: Position
    speed: float
    route: Optional[str]
    signals: FrozenSet[VehicleSignal]
    veh_type: VehicleType
    stop_states: FrozenSet[VehicleStopState]


class Edge(NamedTuple):
    """
    Traffic data of a road in Sumo.
    """

    id: str
    vehicle_count: int
    mean_speed: float


class TrafficLight(NamedTuple):
    """
    Current state of a traffic light in Sumo.
    """

    id: str
    signals: Tuple[SignalState, ...]
    phase_nr: int
    program_id: str
    time_to_switch: float
