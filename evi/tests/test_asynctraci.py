import itertools as it
import unittest.mock as mock

import pytest
import traci.constants as tc

from evi.asynctraci import AsyncTraCI

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


def fake_simtime_generator(step_duration=0.1):
    for step in it.count(1):
        yield {tc.VAR_TIME_STEP: step * step_duration}


def make_fake_sumo():
    """
    Creates a fake traci.connect function to mock sumo.

    The returned mock contains all fake data to:
    - establish a connection
    - query simulation time via a subscription

    TODO: make this more flexible
    """

    def connect_function(*_arg, **_kwargs):
        connection = mock.Mock()
        connection.getVersion = mock.Mock(return_value=(20, "SUMO 1.6.0"))
        connection.simulation = mock.NonCallableMock()
        connection.simulation.subscribe = mock.Mock()
        connection.simulation.getSubscriptionResults = mock.Mock(
            side_effect=fake_simtime_generator()
        )
        return connection

    return connect_function


@pytest.fixture
async def atraci():
    atraci = AsyncTraCI(("localhost", 99999), make_fake_sumo())
    try:
        yield atraci
    finally:
        await atraci.close()


# tests


def test_connection_starts_at_0_ms(atraci):
    assert atraci.time_ms() == 0


def test_connection_tells_version(atraci):
    assert atraci.version.api_number == 20
    assert atraci.version.sumo_version == "SUMO 1.6.0"


async def test_simulate_step_advances_time(atraci):
    initial_time = atraci.time_ms()
    await atraci.simulate_step()
    second_time = atraci.time_ms()
    await atraci.simulate_step()
    third_time = atraci.time_ms()

    assert initial_time < second_time
    assert second_time < third_time


async def test_vehicle_subscription_yields_vehicle_next_step(atraci):
    # extend fake sumo instance with mock results
    atraci._connection.vehicle.getAllSubscriptionResults = mock.Mock(
        side_effect=[{"veh_1": {tc.VAR_SPEED: 10.0}}]
    )
    # perform subscription, advance simulation and extract result
    await atraci.subscribe_vehicle("veh_1", [tc.VAR_SPEED])
    await atraci.simulate_step()
    results = atraci.vehicle_subscription_results()

    assert "veh_1" in results
    assert tc.VAR_SPEED in results["veh_1"]
    assert 10.0 == results["veh_1"][tc.VAR_SPEED]
