"""
Test ASMP protocol helpers.
"""

import pytest

import asmp.asmp_pb2 as asmp
import evi.util
from evi.proto import vehicle_to_protobuf
from evi.state import Position, Vehicle, VehicleType

RANDOM_VEHICLE_POSITIONS = [(100.0, 200.0), (1000.0, 0.0), (0.0, 10000.0)]


@pytest.fixture(params=RANDOM_VEHICLE_POSITIONS)
def vehicle(request) -> Vehicle:
    return Vehicle(
        id="updateVehicle",
        position=Position(
            road_id="some_road",
            s_frac=0,
            lane_id=0,
            x=request.param[0],
            y=request.param[1],
            angle=0.5,
            height=0,
            slope=0,
        ),
        speed=1.0,
        route="some_route",
        signals=frozenset(),
        veh_type=VehicleType.PASSENGER_CAR,
        stop_states=frozenset(),
    )


@pytest.fixture
def geo_projection():
    return evi.util.make_geo_mapper(
        "+proj=utm +zone=32 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
        (-474821.76, -5723127.5),
    )


@pytest.fixture(autouse=True)
def fake_id_mapper(monkeypatch):
    def mock_uint(*ignored_args, **ignored_kwargs):
        return 12345

    monkeypatch.setattr(evi.util.ID_MAPPER, "to_uint", mock_uint)


def test_single_vehicle_update_to_protobuf_conversion_without_geo_projection(
    benchmark, vehicle
):
    message = asmp.Message()
    update_command = message.vehicle.commands.add().update_vehicle_command

    benchmark(
        vehicle_to_protobuf,
        vehicle=vehicle,
        command=update_command,
        geo_projection=None,
    )

    assert update_command.vehicle_id == 12345
    assert update_command.state.position.road_id == 12345
    assert update_command.state.position.px == vehicle.position.x
    assert update_command.state.position.py == vehicle.position.y
    assert update_command.state.position.angle == vehicle.position.angle
    assert update_command.state.position.height == vehicle.position.height
    assert update_command.state.position.slope == vehicle.position.slope
    assert update_command.state.speed_mps == vehicle.speed
    assert update_command.state.signal_sum == 0
    assert len(update_command.state.signals) == 0
    assert update_command.state.stopstate_sum == 0
    assert len(update_command.state.stopstates) == 0


def test_single_vehicle_update_to_protobuf_conversion_with_geo_projection(
    benchmark, vehicle, geo_projection
):
    message = asmp.Message()
    update_command = message.vehicle.commands.add().update_vehicle_command

    benchmark(
        vehicle_to_protobuf,
        vehicle=vehicle,
        command=update_command,
        geo_projection=geo_projection,
    )

    assert update_command.vehicle_id == 12345
    assert update_command.state.position.road_id == 12345
    assert update_command.state.position.px == vehicle.position.x
    assert update_command.state.position.py == vehicle.position.y
    assert update_command.state.position.angle == vehicle.position.angle
    assert update_command.state.position.height == vehicle.position.height
    assert update_command.state.position.slope == vehicle.position.slope
    assert update_command.state.speed_mps == vehicle.speed
    assert update_command.state.signal_sum == 0
    assert len(update_command.state.signals) == 0
    assert update_command.state.stopstate_sum == 0
    assert len(update_command.state.stopstates) == 0
