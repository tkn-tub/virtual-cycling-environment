from typing import Any, Hashable
import datetime
import os
import pprint
import numpy as np
import yaml

from .triggers import TriggerGenerator


def calculate_scenario_statistics(
        stats_file_out: str,
        net_file_out: str,
        toj_route_file: str,
        num_junctions_x: int,
        num_junctions_y: int,
        sumo_version: str,
        stats_print: bool = True,
        **kwargs
):
    if stats_file_out is not None and os.path.exists(stats_file_out):
        with open(stats_file_out, 'r') as f:
            stats = yaml.load(f)
    else:
        stats = dict()

    generator = TriggerGenerator(
        toj_route_file,
        net_file_out,
        sumo_version=sumo_version,
    )
    # grid_helper = GridHelper(
    #     generator,
    #     num_junctions_x=num_junctions_x,
    #     num_junctions_y=num_junctions_y,
    # )

    total_length = 0
    total_length_levels = 0
    num_straights = 0
    num_straights_levels = 0
    num_right_turns = 0
    num_right_turns_levels = 0
    num_left_turns = 0
    num_left_turns_levels = 0
    condition_counts_in_levels = dict()

    for route_elem_index, lane in enumerate(generator.ego_route):
        current_edge_helper = generator.ego_route.get_edge_helper(
            route_elem_index=route_elem_index
        )
        is_in_level = lane.get('level', None) is not None

        total_length += current_edge_helper.length
        total_length_levels += current_edge_helper.length if is_in_level else 0

        if is_in_level and lane.get('condition', None) is not None:
            condition = lane.get('condition', 'INVALID_CONDITION')
            if condition in condition_counts_in_levels:
                condition_counts_in_levels[condition] += 1
            else:
                condition_counts_in_levels[condition] = 0

        if route_elem_index < len(generator.route) - 1:
            next_edge_helper = generator.ego_route.get_edge_helper(
                route_elem_index + 1
            )
            direction_of_next = current_edge_helper.get_direction_of(
                next_edge_helper
            )

            if direction_of_next == 'straight':
                num_straights += 1
                num_straights_levels += 1 if is_in_level else 0
            elif direction_of_next == 'left':
                num_left_turns += 1
                num_left_turns_levels += 1 if is_in_level else 0
            elif direction_of_next == 'right':
                num_right_turns += 1
                num_right_turns_levels += 1 if is_in_level else 0
            else:
                raise Exception(
                    "Scenario stats: Couldn't determine a direction "
                    "in the TOJ route for "
                    f"current={current_edge_helper}, next={next_edge_helper}"
                )

    # Calculate time to completion in seconds for an average speed of 20 km/h
    _meters_per_second = 20 / 3.6
    estimated_time = total_length / _meters_per_second
    estimated_time_levels = total_length_levels / _meters_per_second

    # TODO: num cars, events

    stats['total_length_in_meters'] = total_length
    stats['total_length_in_levels_in_meters'] = total_length_levels
    stats['time_at_20kph'] = str(datetime.timedelta(seconds=estimated_time))
    stats['time_at_20kph_in_seconds'] = estimated_time
    stats['time_in_levels_at_20kph'] = str(
        datetime.timedelta(seconds=estimated_time_levels)
    )
    stats['time_in_levels_at_20kph_in_seconds'] = estimated_time_levels
    stats['num_left_turns'] = num_left_turns
    stats['num_right_turns'] = num_right_turns
    stats['num_straights'] = num_straights
    stats['num_left_turns_in_levels'] = num_left_turns_levels
    stats['num_right_turns_in_levels'] = num_right_turns_levels
    stats['num_straights_in_levels'] = num_straights_levels
    stats['num_edges_in_levels_by_condition'] = condition_counts_in_levels

    if stats_print:
        print("\nSCENARIO STATISTICS:")
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(stats)

    if stats_file_out is None:
        return
    with open(stats_file_out, 'w') as f:
        yaml.dump(stats, f, default_flow_style=False)


def get_cartesian_and_direction_and_angle_from_edge_pos(
        sumo_net,
        edge_id,
        edge_pos,
):
    """
    :raise: ValueError if edge_pos goes beyond the defined length
        of the given edge.
    :param sumo_net: A sumolib.net.Net instance.
    :param edge_id: Name of the edge.
    :param edge_pos: Position on the edge in meters from the edge's
        start point.
    :return: Cartesian coordinates (x, y), normalized direction vector,
        and angle in degrees for a given position on a SUMO edge.
    """
    edge = sumo_net.getEdge(edge_id)
    if edge_pos < 0 or edge_pos > edge.getLength():
        raise ValueError(
            "Cannot get coordinates and angle at "
            f"position {edge_pos} on edge {edge_id} "
            f"of length {edge.getLength()}."
        )

    verts = edge.getShape()

    distance_on_edge = 0.
    for segment in zip(verts, verts[1:]):
        # An edge consists of segments, each segment being defined by
        # two consecutive vertices v_start and v_end in verts.
        v_start, v_end = np.array(segment)

        segment_length = np.linalg.norm(v_end - v_start)
        v_direction = (v_end - v_start) / segment_length

        if edge_pos <= distance_on_edge + segment_length:
            angle = -np.degrees(np.arctan2(v_direction[1], v_direction[0]))
            return (
                tuple(v_start + (edge_pos - distance_on_edge) * v_direction),
                v_direction,
                angle
            )

        distance_on_edge += segment_length

    raise ValueError(
        "Cannot get coordinates and angle at position "
        f"{edge_pos} on edge {edge_id} of length {edge.getLength()}."
    )


def get_cartesian_from_edge_pos(sumo_net, edge_id, edge_pos):
    """
    :param sumo_net: A sumolib.net.Net instance.
    :param edge_id: Name of the edge.
    :param edge_pos: Position on the edge in meters from the
        edge's start point.
    :return: Cartesian coordinates (x, y) for a given position on a SUMO edge.
        Returns None if edge_pos goes beyond the defined length
        of the given edge.
    """
    result = get_cartesian_and_direction_and_angle_from_edge_pos(
        sumo_net,
        edge_id,
        edge_pos,
    )
    return result[0] if result is not None else None


def get_angle_at_edge_pos(sumo_net, edge_id, edge_pos):
    """
    :param sumo_net: A sumolib.net.Net instance.
    :param edge_id: Name of the edge.
    :param edge_pos: Position on the edge in meters from the edge's
        start point.
    :return: The angle in degrees for a given position on a SUMO edge.
        Returns None if edge_pos goes beyond the defined length
        of the given edge.
    """
    result = get_cartesian_and_direction_and_angle_from_edge_pos(
        sumo_net,
        edge_id,
        edge_pos,
    )
    return result[2] if result is not None else None


def empty_dict_if_none(key: Hashable, value: Any) -> dict:
    """
    Useful for building up dict objects.
    If you have a variable x that may be None and if you only want to include
    it in your dict if it is not None, simply do this:
    {**empty_dict_if_none('x', x), 'y': y, …}

    :param key:
    :param value:
    :return:
    """
    return {key: value} if value is not None else {}
