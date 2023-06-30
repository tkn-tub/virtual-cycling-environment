"""
test the evi's sumo interface

TODO:
 - new state after simulation step
 - change radius -> more vehicles in context
 - detect ego vehicle
"""

import pytest

from evi.sumo import SumoInterface

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# Fixtures


@pytest.fixture
async def sumo_raw_interface(unused_sumo_port, sumo_instance, ego_vehicle_id, valid_vtype, valid_route_name):
    """create a non-initialized sumo interface"""
    sif = SumoInterface(
        sumo_host="localhost",
        sumo_port=unused_sumo_port,
        ego_vehicle_id=ego_vehicle_id,
        ego_type=valid_vtype,
        ego_route_name=valid_route_name,
    )
    try:
        yield sif
    finally:
        await sif.teardown()


@pytest.fixture
async def sumo_interface(sumo_raw_interface):
    """create an initialized sumo interface"""
    await sumo_raw_interface.warm_up_traffic()
    yield sumo_raw_interface


# Tests


async def test_interface_connects_after_init(sumo_raw_interface):
    await sumo_raw_interface.warm_up_traffic(start_time_ms=0)
    traci_connection = sumo_raw_interface._atraci._connection
    assert traci_connection.simulation.getCurrentTime() == 0


async def test_interface_advances_to_start_time(sumo_raw_interface):
    start_time_ms = 1000  # one second
    await sumo_raw_interface.warm_up_traffic(start_time_ms=start_time_ms)
    traci_connection = sumo_raw_interface._atraci._connection
    assert traci_connection.simulation.getCurrentTime() == start_time_ms


async def test_simulation_step_advances_time(sumo_interface):
    time_before_step_ms = sumo_interface._atraci.time_ms()
    await sumo_interface._simulation_step(frozenset())
    assert sumo_interface._atraci.time_ms() > time_before_step_ms


async def test_update_zero_ego_vehicles_does_not_crash(sumo_interface):
    await sumo_interface._update_ego_vehicles(frozenset())


async def test_update_single_new_ego_vehicle_spawns_correct_vehicle(
    sumo_interface, valid_ego_vehicle
):
    assert not sumo_interface._ego_vehicle_ids
    await sumo_interface._update_ego_vehicles(frozenset([valid_ego_vehicle]))

    # Note: position of the ego vehicle is not (yet) guaranteed to be set befor the first simulation step
    # existence of ego vehicle in sumo implicitly checked by querying for any of its attributes
    traci_connection = sumo_interface._atraci._connection
    assert traci_connection.vehicle.getRouteID(valid_ego_vehicle.id) == valid_ego_vehicle.route
    assert traci_connection.vehicle.getTypeID(valid_ego_vehicle.id) == valid_ego_vehicle.veh_type
