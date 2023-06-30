"""
Vehicle route and location helpers.

Tooling to find and reconcstruct routes from coordinate sequences.
"""

from typing import Dict, Iterable, List, Sequence, Tuple

import rtree
import shapely.geometry
import sumolib

from .util import drop_consecutive_duplicates

FPoint = Tuple[float, float]


class LaneFinder:
    """
    Helper to find lanes by x/y coordinates in a Sumo network.

    Uses an rtree with bounding boxes for a fast, imprecise lookup.
    Then does the final decision using shapely LineStrings.
    This is aroung 100x faster than shapely.strtree.STRtree.

    However, rtree only supports numerical indices (nr).
    Thus, an additional mapping from nr to lane ids (lid) is used.
    This is twice as fast as storing the lane id as an object in the rtree.
    """

    linestrings: Dict[str, shapely.geometry.LineString]
    nr2lane: Dict[int, sumolib.net.lane.Lane]
    rtree: rtree.index.Index

    @staticmethod
    def shape2segments(shape: Sequence[FPoint]) -> List[Tuple[FPoint, FPoint]]:
        """
        Convert list of points into a list of lines between the those points.

        >>> LaneFinder.shape2segments([(0, 0), (1, 0), (1, 1)])
        [((0, 0), (1, 0)), ((1, 0), (1, 1))]
        """
        return list(zip(shape[:-1], shape[1:]))

    @staticmethod
    def segment2bbox(
        segment: Tuple[FPoint, FPoint]
    ) -> Tuple[float, float, float, float]:
        """Convert a line segments into it bounding box."""
        (px1, py1), (px2, py2) = segment
        return (min(px1, px2), min(py1, py2), max(px1, px2), max(py1, py2))

    def __init__(self, lanes: Iterable[sumolib.net.lane.Lane]) -> None:
        """
        Set up mapper for Sumo network given in sumo_net_file.
        """
        segments = {
            segment: lane
            for lane in lanes
            for segment in LaneFinder.shape2segments(lane.getShape(True))
        }
        self.linestrings = {
            lane.getID(): shapely.geometry.LineString(lane.getShape(True))
            for lane in lanes
        }
        self.rtree = rtree.index.Index()
        self.nr2lane = {}
        for lane_nr, (segment, lane) in enumerate(segments.items()):
            self.rtree.insert(lane_nr, LaneFinder.segment2bbox(segment))
            self.nr2lane[lane_nr] = lane

    def nearest_lane(self, coord: FPoint) -> sumolib.net.lane.Lane:
        """
        Return the nearest lane for given x/y coord.

        Result undefined for coords inside junctions.
        """
        point = shapely.geometry.Point(coord)
        # nearest may yield more than one candidate of similar distance
        candidates = {self.nr2lane[nr] for nr in self.rtree.nearest(coord, 1)}
        return min(
            candidates,
            key=lambda candidate: self.linestrings[candidate.getID()].distance(
                point
            ),
        )


class JunctionFinder:
    """
    Finds junctions hit by a sequence of points.
    """

    @staticmethod
    def poly_bbox(
        shape: Iterable[FPoint],
    ) -> Tuple[float, float, float, float]:
        """Return bounding box for polygon shape."""
        return (
            min(point[0] for point in shape),
            min(point[1] for point in shape),
            max(point[0] for point in shape),
            max(point[1] for point in shape),
        )

    def __init__(self, junctions: Iterable[sumolib.net.node.Node]) -> None:
        self.rtree = rtree.index.Index()
        self.nr2junction = dict(enumerate(junctions))
        self.polygons = {
            junction.getID(): shapely.geometry.Polygon(junction.getShape())
            for junction in junctions
        }
        for j_nr, junction in self.nr2junction.items():
            self.rtree.add(j_nr, JunctionFinder.poly_bbox(junction.getShape()))

    def hit_junctions(
        self, coords: List[FPoint]
    ) -> Dict[FPoint, sumolib.net.node.Node]:
        """Return list of junctions hit by path along points."""
        segments = LaneFinder.shape2segments(coords)
        points = {coord: shapely.geometry.Point(coord) for coord in coords}
        candidate_junctions = {
            self.nr2junction[j_nr]
            for segment in segments
            for j_nr in self.rtree.intersection(self.poly_bbox(segment))
        }
        return {
            coord: junction
            for coord, point in points.items()
            for junction in candidate_junctions
            if self.polygons[junction.getID()].contains(point)
        }


def are_connected(
    from_edge: sumolib.net.edge.Edge, to_edge: sumolib.net.edge.Edge
) -> bool:
    """Return whether from_edge is connected to to_edge."""
    return to_edge in from_edge.getOutgoing()


def find_connection(
    from_edge: sumolib.net.edge.Edge, to_edge: sumolib.net.edge.Edge
) -> List[sumolib.net.edge.Edge]:
    """Find a sequence of edges that connects from_edge to to_edge."""
    if from_edge == to_edge:
        raise ValueError("from_edge and to_edge can not be the same!")
    if are_connected(from_edge, to_edge):
        return [from_edge, to_edge]
    edge_pool = [
        (connection_edge, [from_edge])
        for connection_edge in from_edge.getOutgoing().keys()
    ]
    seen_edges = set()
    for connection_edge, route in edge_pool:
        if are_connected(connection_edge, to_edge):
            return route + [connection_edge, to_edge]
        seen_edges.add(connection_edge)
        edge_pool.extend(
            (next_edge, route + [connection_edge])
            for next_edge in connection_edge.getOutgoing().keys()
            if next_edge not in seen_edges
        )

    raise RuntimeError(
        f"No route from {from_edge.getID()} to {to_edge.getID()} found."
    )


def reconstruct_route(
    coords: List[FPoint],
    lane_finder: LaneFinder,
    junction_finder: JunctionFinder,
) -> List[sumolib.net.edge.Edge]:
    """
    Reconstruct a complete route of edges from a sequence of points.

    Returns a list of edges, including internal edges.
    """
    assert len(coords) >= 2, "Route recontruction needs at least 2 points."
    # check for points in junctions
    junction_coords = junction_finder.hit_junctions(coords)
    road_coords = [coord for coord in coords if coord not in junction_coords]

    # extract lanes under coordinates
    found_lanes = [lane_finder.nearest_lane(coord) for coord in road_coords]

    # convert to edges and remove consecutive duplicates
    unique_consecutive_edges = list(
        drop_consecutive_duplicates(lane.getEdge() for lane in found_lanes)
    )

    # check consistency and add missing links
    found_connections = zip(
        unique_consecutive_edges[:-1], unique_consecutive_edges[1:]
    )
    complete_edges = [unique_consecutive_edges[0]]
    for from_edge, to_edge in found_connections:
        connecting_edge_sequence = find_connection(from_edge, to_edge)
        complete_edges.extend(connecting_edge_sequence[1:])  # remove from_edge
    assert len(complete_edges) >= len(unique_consecutive_edges)

    return complete_edges


def find_tls_in_route(
    route_edges: List[sumolib.net.edge.Edge],
    sumo_net: sumolib.net.Net,
) -> List[Tuple[sumolib.net.TLS, int]]:
    """
    Find and return traffic lights and the passed link along a route of edges.

    Assumes that route_edges is connected and complete.

    Looks for a tls between the edges in route_edges.
    A tls immediately after the last edges in route_edges is *not* returned.
    For such a tls, the link index could not be reliably determined!
    """
    result = []
    for edge, next_edge in zip(route_edges[:-1], route_edges[1:]):
        # find tls
        junction = edge.getToNode()
        if junction.getType() != "traffic_light":
            continue
        tls = sumo_net.getTLS(junction.getID())

        # find link index
        edge_to_next_edge_connections = [
            link_index
            for lane_in, lane_out, link_index in tls.getConnections()
            if lane_in.getEdge() == edge and lane_out.getEdge() == next_edge
        ]
        assert len(edge_to_next_edge_connections) > 0
        # there may be multiple connections and thus links for one edge-pair
        # e.g., with two parallel lanes across the junction or a fork/join
        # but the signals should always be the same, so we just pickt the first
        link_index = edge_to_next_edge_connections[0]
        result.append((tls, link_index))
    return result


def get_next_green_phase_times(
    program: sumolib.net.TLSProgram,
    link_index: int,
    current_phase_nr: int,
    green_phases: int,
) -> List[Tuple[float, float]]:
    """
    Return the begin/end time to the next green phase.

    For a passing over link_index of the current program.
    Zero values mean that a green phase is active for link_index.

    Is not limited to sumo phases.
    Instead, merges consecutive green times for the given link_index.

    Does not incorporate the already passed time of the current phase.
    That should be offest externally to make this time-independent.
    """
    if program.getType() != "static":
        raise NotImplementedError("Non-static tls programs not yet supported.")

    phases = program.getPhases()
    phase = phases[current_phase_nr]
    result: List[Tuple[float, float]] = []
    passed_time = 0
    while len(result) < green_phases:
        # find green phase
        while not phase.state[link_index] in {"g", "G"}:
            passed_time += phase.duration
            current_phase_nr = (current_phase_nr + 1) % len(phases)
            phase = phases[current_phase_nr]
        # compute green start time
        start_time = passed_time
        # continue while consecutive green phases run
        while phase.state[link_index] in {"g", "G"}:
            passed_time += phase.duration
            current_phase_nr = (current_phase_nr + 1) % len(phases)
            phase = phases[current_phase_nr]
        result.append((start_time, passed_time))

    return result


def offset_green_phase_times(
    green_times: List[Tuple[float, float]],
    passed_time: float,
):
    """
    Incorporate passed_time within current phase to green_times.
    """
    return [
        (start - passed_time, end - passed_time) for start, end in green_times
    ]
