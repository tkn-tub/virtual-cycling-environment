from collections import namedtuple
from random import Random

import pytest  # noqa

from evi.filtering import FELLOW_FILTERS

PLAYGROUND_SIZE = 10000

# stub type for Vehicle and position objects without all the extra fields
Position = namedtuple('Position', ['x', 'y'])
Vehicle = namedtuple('Vehicle', ['id', 'position'])


def _generate_vehicles(rgen, number, prefix="vehicle-"):
    return [
        Vehicle(
            "{}{}".format(prefix, index),
            Position(rgen.uniform(0, PLAYGROUND_SIZE), rgen.uniform(0, PLAYGROUND_SIZE))
        )
        for index in range(number)
    ]


@pytest.fixture(scope="function")
def random_generator():
    return Random(1234567890)


@pytest.fixture(scope="module", params=[1, 10, 50, 100, 200])
def vehicle_limit(request):
    return request.param


@pytest.fixture(scope="module", params=[1, 3, 10])
def ego_vehicle_nr(request):
    return request.param


@pytest.fixture(scope="module", params=[100, 500, 1000])
def fellow_pool_nr(request):
    return request.param


@pytest.fixture
def ego_vehicles(random_generator, ego_vehicle_nr):
    return frozenset(_generate_vehicles(random_generator, ego_vehicle_nr, "ego-"))


@pytest.fixture
def fellow_pool(random_generator, fellow_pool_nr):
    return frozenset(_generate_vehicles(random_generator, fellow_pool_nr))


@pytest.fixture(scope="module", params=list(FELLOW_FILTERS.values()), ids=list(FELLOW_FILTERS.keys()))
def filter_function(request):
    return request.param


def test_benchmark_filters(benchmark, filter_function, ego_vehicles, fellow_pool, vehicle_limit):
    selected_fellows = benchmark(
        filter_function,
        vehicles=fellow_pool,
        ego_vehicles=ego_vehicles,
        max_vehicles=vehicle_limit
    )
    assert len(selected_fellows) <= vehicle_limit
