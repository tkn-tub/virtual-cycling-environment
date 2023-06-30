"""
More complex tests of utils that require further files.
"""

import re
from typing import Dict, Optional, Tuple

import pytest
import sumolib

from evi.routehelper import (
    JunctionFinder,
    LaneFinder,
    find_connection,
    find_tls_in_route,
    get_next_green_phase_times,
    offset_green_phase_times,
    reconstruct_route,
)
from evi.util import drop_consecutive_duplicates

COORDS: Dict[Tuple[float, float], str] = {
    (8572.29, 5154.57): "30926598#0_0",
    (8600.99, 5092.47): "30926598#1_0",
    (8604.64, 5085.16): "30926598#1_0",
    (8610.12, 5073.42): "30926598#1_0",
    (8632.22, 5046.24): ":247375513_5_0",
    (8646.91, 5043.67): "30926598#2_0",
    (8690.49, 5056.46): "30926598#3_0",
    (8969.82, 4973.09): "236094252#0_2",
    (8991.07, 4984.22): "236094252#0_2",
    (8994.04, 5005.48): "30724791#0_0",
}

ROUTE_PATHS: Dict[str, Dict] = {
    "simple_complete_one_coord_per_edge": {
        "coords": [
            (8572.29, 5154.57),
            (8604.64, 5085.16),
            (8646.91, 5043.67),
            (8690.49, 5056.46),
        ]
    },
    "simple_complete_multiple_points_per_lane": {
        "coords": [
            (8600.99, 5092.47),
            (8610.12, 5073.42),
            (8646.91, 5043.67),
        ]
    },
    "simple_complete_crossing_junction_with_one_point": {
        "coords": [
            (8600.99, 5092.47),
            (8632.22, 5046.24),
            (8646.91, 5043.67),
        ]
    },
    "simple_incomplete_skipping_one_edge": {
        "coords": [
            (8572.29, 5154.57),
            (8604.64, 5085.16),  # skipped
            (8646.91, 5043.67),
            (8690.49, 5056.46),
        ],
        "skipped_coords": {1},
    },
    "simple_incomplete_skipping_two_consecutive_edges": {
        "coords": [
            (8572.29, 5154.57),
            (8604.64, 5085.16),  # skipped
            (8646.91, 5043.67),  # skipped
            (8690.49, 5056.46),
        ],
        "skipped_coords": {1, 2},
    },
    "simple_complete_one_coord_per_edge_across_tls_junction": {
        "coords": [
            (8969.82, 4973.09),
            (8994.04, 5005.48),
        ],
        "tls": {"536777420": {"link_index": 8}},
    },
    "single_lane_that_leads_to_a_tls": {
        "coords": [
            (8969.82, 4973.09),
            (8991.07, 4984.22),
        ],
        "tls": {},
    },
    # TODO: add route with multiple tls
}

TLS_ROUTE_PATHS: Dict[str, Dict] = {
    key: val
    for key, val in ROUTE_PATHS.items()
    if val.get("tls", None) is not None
}

INTERNAL_LANE_PATTERN = re.compile(r":(.+)_\d+_\d+")


def internal_lane_to_junction(lane_id: str) -> Optional[str]:
    """
    Extract junction name from internal lane id.

    >>> internal_lane_to_junction(':247375513_5_0')
    '247375513'
    """
    match = INTERNAL_LANE_PATTERN.match(lane_id)
    if not match:
        return None
    return match.groups()[0]


def make_route_config(param) -> Dict:
    all_coords = param["coords"]
    hit_coords = [
        coord
        for index, coord in enumerate(all_coords)
        if index not in param.get("skipped_coords", [])
    ]

    all_coords_map = {coord: COORDS[coord] for coord in all_coords}
    return {
        "coords": hit_coords,
        "all_coords_map": all_coords_map,
        "route_lanes": [
            lane
            for lane in drop_consecutive_duplicates(all_coords_map.values())
            if not lane.startswith(":")
        ],
        "route_edges": [
            edge
            for edge in drop_consecutive_duplicates(
                [lane.split("_")[0] for lane in all_coords_map.values()]
            )
            if not edge.startswith(":")
        ],
        "hit_lanes": [COORDS[coord] for coord in hit_coords],
        "hit_junctions": {
            coord: internal_lane_to_junction(lane)
            for coord, lane in all_coords_map.items()
            if internal_lane_to_junction(lane)
        },
        "tls": param.get("tls", []),
    }


@pytest.fixture(scope="module")
def sumo_net() -> sumolib.net.Net:
    """A sumo network file loaded by sumolib."""
    return sumolib.net.readNet(
        "networks/paderborn-hynets/paderborn-hynets.net.xml",
        withInternal=True,
        withPrograms=True,
    )


@pytest.fixture(scope="module")
def lane_finder(sumo_net) -> LaneFinder:
    lanes = [lane for edge in sumo_net.getEdges() for lane in edge.getLanes()]
    return LaneFinder(lanes)


@pytest.fixture(scope="module")
def junction_finder(sumo_net) -> JunctionFinder:
    junctions = [
        node for node in sumo_net.getNodes() if node.getType() != "dead_end"
    ]
    return JunctionFinder(junctions)


@pytest.fixture(params=ROUTE_PATHS.values(), ids=ROUTE_PATHS.keys())
def route_config(request) -> Dict:
    return make_route_config(request.param)


@pytest.fixture(params=TLS_ROUTE_PATHS.values(), ids=TLS_ROUTE_PATHS.keys())
def tls_route_config(request) -> Dict:
    # separated out from route_config to reduce number of test configs for tls
    # finding test cases without any tls in them
    return make_route_config(request.param)


@pytest.fixture(params=[("536777420", "0")])
def tls_program(request, sumo_net) -> sumolib.net.TLSProgram:
    tls_id, program_id = request.param
    return sumo_net.getTLS(tls_id).getPrograms()[program_id]


# Tests


def test_find_connection_for_directly_connectes_edges(sumo_net):
    from_edge = sumo_net.getEdge("30926598#0")
    to_edge = sumo_net.getEdge("30926598#1")
    expted_route = [from_edge, to_edge]
    found_route = find_connection(from_edge, to_edge)
    assert found_route == expted_route


def test_find_connection_for_same_edges_is_illegal(sumo_net):
    from_edge = sumo_net.getEdge("30926598#0")
    with pytest.raises(ValueError):
        find_connection(from_edge, from_edge)


def test_find_connection_for_edges_with_one_gap(sumo_net):
    from_edge = sumo_net.getEdge("30926598#0")
    missing_edge = sumo_net.getEdge("30926598#1")
    to_edge = sumo_net.getEdge("30926598#2")
    expted_route = [from_edge, missing_edge, to_edge]
    found_route = find_connection(from_edge, to_edge)
    assert found_route == expted_route


def test_find_connection_for_edges_with_two_consecutive_gaps(sumo_net):
    from_edge = sumo_net.getEdge("30926598#0")
    missing_edges = [
        sumo_net.getEdge("30926598#1"),
        sumo_net.getEdge("30926598#2"),
    ]
    to_edge = sumo_net.getEdge("30926598#3")
    expted_route = [from_edge, *missing_edges, to_edge]
    found_route = find_connection(from_edge, to_edge)
    assert found_route == expted_route


def test_find_connection_for_edges_with_two_non_consecutive_gaps(sumo_net):
    from_edge = sumo_net.getEdge("30926598#0")
    first_missing_edge = sumo_net.getEdge("30926598#1")
    middle_edge = sumo_net.getEdge("30926598#2")
    second_missing_edge = sumo_net.getEdge("30926598#3")
    to_edge = sumo_net.getEdge("30926598#4")
    expted_route = [
        from_edge,
        first_missing_edge,
        middle_edge,
        second_missing_edge,
        to_edge,
    ]
    found_route = find_connection(from_edge, to_edge)
    assert found_route == expted_route


def test_finding_points_on_route(route_config, lane_finder):
    for point, expected_lane in route_config["all_coords_map"].items():
        lane = lane_finder.nearest_lane(point)
        if not expected_lane.startswith(":"):
            # ignore internal lanes for this comparison, their result is UB
            assert lane.getID() == expected_lane


def test_finding_hit_junctions(route_config, junction_finder):
    found_junctions = junction_finder.hit_junctions(route_config["coords"])
    found_junction_ids = {
        coord: lane.getID() for coord, lane in found_junctions.items()
    }
    assert found_junction_ids == route_config["hit_junctions"]


def test_reconstruct_simple_route(route_config, lane_finder, junction_finder):
    route = reconstruct_route(
        route_config["coords"], lane_finder, junction_finder
    )
    assert [edge.getID() for edge in route] == route_config["route_edges"]


def test_reconstruct_route_with_tls(tls_route_config, sumo_net):
    route = [
        sumo_net.getEdge(edge_id)
        for edge_id in tls_route_config["route_edges"]
    ]
    raw_found_tls = find_tls_in_route(route, sumo_net)
    found_tls_ids = [tls.getID() for tls, _link_index in raw_found_tls]
    found_link_indices = [link_index for _tls, link_index in raw_found_tls]
    assert found_tls_ids == list(tls_route_config["tls"].keys())
    expected_link_indices = [
        tls["link_index"] for tls in tls_route_config["tls"].values()
    ]
    assert found_link_indices == expected_link_indices


def test_find_one_green_duration_of_ongoing_green_phase(tls_program):
    """Assumes the green phase is already active."""
    phase_nr = 0
    link_index = 8
    expteced_durations = [(0, 27 + 6 + 6)]
    found_durations = get_next_green_phase_times(
        tls_program, link_index, phase_nr, green_phases=1
    )
    assert expteced_durations == found_durations


def test_find_one_green_duration_from_one_before_green_phase(tls_program):
    """Assumes the green phase will be the next phase."""
    phase_nr = 7
    link_index = 8
    expteced_durations = [(6, 6 + 27 + 6 + 6)]
    found_durations = get_next_green_phase_times(
        tls_program, link_index, phase_nr, green_phases=1
    )
    assert expteced_durations == found_durations


def test_find_one_green_duration_from_two_before_green_phase(tls_program):
    """Assumes the green phase will be the next next phase."""
    phase_nr = 6
    link_index = 8
    expteced_durations = [(12, 12 + 27 + 6 + 6)]
    found_durations = get_next_green_phase_times(
        tls_program, link_index, phase_nr, green_phases=1
    )
    assert expteced_durations == found_durations


def test_find_two_green_duration_of_ongoing_green_phase(tls_program):
    """Assumes the green phase is already active."""
    phase_nr = 0
    link_index = 8
    expteced_durations = [(0, 27 + 6 + 6), (90, 90 + 27 + 6 + 6)]
    found_durations = get_next_green_phase_times(
        tls_program, link_index, phase_nr, green_phases=2
    )
    assert expteced_durations == found_durations


def test_offset_green_phase_time_at_phase_start():
    raw_green_times = [(0, 39), (90, 129)]
    passed_time = 0
    expteced_green_times = [(0, 39), (90, 129)]
    restulting_green_times = offset_green_phase_times(
        raw_green_times, passed_time
    )
    assert restulting_green_times == expteced_green_times


def test_offset_green_phase_time_at_phase_mid():
    raw_green_times = [(0, 39), (90, 129)]
    passed_time = 11.5
    expteced_green_times = [(-11.5, 27.5), (78.5, 117.5)]
    restulting_green_times = offset_green_phase_times(
        raw_green_times, passed_time
    )
    assert restulting_green_times == expteced_green_times


def test_offset_green_phase_time_at_phase_end():
    raw_green_times = [(0, 39), (90, 129)]
    passed_time = 27
    expteced_green_times = [(-27, 12), (63, 102)]
    restulting_green_times = offset_green_phase_times(
        raw_green_times, passed_time
    )
    assert restulting_green_times == expteced_green_times
