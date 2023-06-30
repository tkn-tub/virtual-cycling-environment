"""
Protobuf-based communication utilities.

For communication with RTIs and Veins.
"""

from typing import Any, Dict, Iterable, List, Tuple

import asmp.asmp.horizon_pb2 as horizon_pb2
import asmp.asmp.trafficlight_pb2 as asmp_trafficlight
import asmp.asmp_pb2 as asmp

from .filtering import select_fellows_equally_distributed
from .state import (
    Edge,
    Position,
    SignalState,
    TrafficLight,
    Vehicle,
    VehicleSignal,
    VehicleStopState,
    VehicleType,
)
from .util import ID_MAPPER


def protobuf_to_vehicle(uint_id, state, veh_type):
    """
    Convert protobuf message to Vehicle object.
    """
    return Vehicle(
        id=ID_MAPPER.to_string(uint_id),
        position=Position(
            ID_MAPPER.to_string(state.position.road_id),
            state.position.s_frac,
            state.position.lane_id,
            state.position.px,
            state.position.py,
            state.position.angle,
            state.position.height,
            state.position.slope,
        ),
        speed=state.speed_mps,
        route=None,
        signals=frozenset(VehicleSignal(signal) for signal in state.signals),
        veh_type=VehicleType(veh_type),
        stop_states=frozenset(
            VehicleStopState(stop_state) for stop_state in state.stopstates
        ),
    )


def vehicle_to_protobuf(vehicle, command, geo_projection=None):
    """
    Convert Vehicle to protobuf message.
    """
    command.vehicle_id = ID_MAPPER.to_uint(vehicle.id)
    command.state.position.road_id = ID_MAPPER.to_uint(
        vehicle.position.road_id
    )
    command.state.position.s_frac = vehicle.position.s_frac
    command.state.position.lane_id = vehicle.position.lane_id
    command.state.position.px = vehicle.position.x
    command.state.position.py = vehicle.position.y
    command.state.position.angle = vehicle.position.angle
    command.state.position.height = vehicle.position.height
    command.state.position.slope = vehicle.position.slope
    command.state.position.edge_id = vehicle.position.road_id
    if geo_projection:
        (
            command.state.position.lon,
            command.state.position.lat,
        ) = geo_projection(
            x=vehicle.position.x,
            y=vehicle.position.y,
        )
    command.state.speed_mps = vehicle.speed
    if vehicle.signals:
        command.state.signal_sum = 0
        for signal in sorted(vehicle.signals, key=lambda x: x.value):
            command.state.signals.append(signal.value)
            command.state.signal_sum += signal.value
    if vehicle.stop_states:
        command.state.stopstate_sum = 0
        for stopstate in sorted(vehicle.stop_states, key=lambda x: x.value):
            command.state.stopstates.append(stopstate.value)
            command.state.stopstate_sum += stopstate.value


def edge_to_protobuf(edge, road_segment):
    """
    Fill road_segment protobuf message with this edge's data.
    """
    road_segment.id = ID_MAPPER.to_uint(edge.id)
    road_segment.num_vehicles = edge.vehicle_count
    road_segment.mean_speed_mps = edge.mean_speed


def protobuf_to_edge(road_segment):
    """
    Derive Edge object from protobuf road_segment message.
    """
    return Edge(
        id=ID_MAPPER.to_string(road_segment.id),
        vehicle_count=road_segment.num_vehicles,
        mean_speed=road_segment.mean_speed_mps,
    )


def trafficlight_to_protobuf(
    trafficlight: TrafficLight, junction: asmp_trafficlight.Junction
) -> None:
    """
    Fill junction protobuf message with traffilight's data.
    """
    junction.id = ID_MAPPER.to_uint(trafficlight.id)
    for i, signal in sorted(enumerate(trafficlight.signals)):
        junction.signals.add()
        junction.signals[i].index = i
        junction.signals[i].state = signal.value
    junction.phase_nr = trafficlight.phase_nr
    junction.program_id = trafficlight.program_id
    junction.time_to_switch_s = trafficlight.time_to_switch


def protobuf_to_trafficlight(
    junction: asmp_trafficlight.Junction,
) -> TrafficLight:
    """
    Derive TrafficLight object from protobuf junction message.
    """
    return TrafficLight(
        id=junction.id,
        signals=tuple(SignalState(signal) for signal in junction.signals),
        phase_nr=junction.phase_nr,
        program_id=junction.program_id,
        time_to_switch=junction.time_to_switch_s,
    )


def build_traffic_message(fellow_changes, time_s, geo_projection=None):
    """Build an ASMP traffic update message from a fellow change set."""
    update_message = asmp.Message()
    update_message.vehicle.time_s = time_s
    commands = update_message.vehicle.commands
    for add_vehicle in sorted(fellow_changes["add"], key=lambda v: v.id):
        add_command = commands.add()
        vehicle_to_protobuf(
            add_vehicle, add_command.register_vehicle_command, geo_projection
        )
        add_command.register_vehicle_command.veh_type = (
            add_vehicle.veh_type.value
        )
    for remove_vehicle in sorted(fellow_changes["rem"], key=lambda v: v.id):
        remove_command = commands.add()
        remove_command.unregister_vehicle_command.vehicle_id = (
            ID_MAPPER.to_uint(remove_vehicle.id)
        )
    for update_vehicle in sorted(fellow_changes["mod"], key=lambda v: v.id):
        update_command = commands.add()
        vehicle_to_protobuf(
            update_vehicle,
            update_command.update_vehicle_command,
            geo_projection,
        )
    return update_message


def build_trafficlight_message(
    trafficlights: Iterable[TrafficLight], time_s: float
) -> asmp.Message:
    """Build an ASMP traffic update message from a fellow change set."""
    message = asmp.Message()
    message.trafficlight.time_s = time_s

    for trafficlight in trafficlights:
        junction = message.trafficlight.junctions.add()
        trafficlight_to_protobuf(trafficlight, junction)

    return message


def build_horizon_tls_response(
    time_s: float,
    responses: Iterable[Tuple[int, int, List[Dict[str, Any]]]],
) -> asmp.Message:
    message = asmp.Message()
    message.horizon.time_s = time_s

    for request_id, vehicle_id, response in responses:
        message.horizon.responses.add()
        resp = message.horizon.responses[-1]
        resp.request_id = request_id
        resp.vehicle_id = vehicle_id
        resp.items.add()
        resp_item = resp.items[-1]
        resp_item.variable = horizon_pb2.Variable.NEXT_TLS_GREEN_PHASES
        tls_vector = resp_item.tls_vector

        for tls in response:
            tls_vector.value.add()
            tls_record = tls_vector.value[-1]
            tls_record.tls_id = ID_MAPPER.to_uint(tls["id"])
            tls_record.position.x = tls["coord"][0]
            tls_record.position.y = tls["coord"][1]
            tls_record.road_distance = tls["road_distance"]

            for begin, end in tls["green_times"]:
                tls_record.next_green_phases.add()
                next_green_phase = tls_record.next_green_phases[-1]
                next_green_phase.begin_earliest_s = begin
                next_green_phase.begin_latest_s = begin
                next_green_phase.end_earliest_s = end
                next_green_phase.end_latest_s = end
    return message


def select_fellows(traffic, ego_vehicles, max_vehicles):
    """Pick fellows from traffic."""
    # make sure the ego vehicle is not part of the fellows
    traffic = frozenset(
        vehicle
        for vehicle in traffic
        if vehicle.id not in {ego.id for ego in ego_vehicles}
    )
    fellows = select_fellows_equally_distributed(
        traffic, ego_vehicles, max_vehicles
    )
    return fellows
