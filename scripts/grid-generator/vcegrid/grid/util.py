from typing import Tuple

import string
import math
import re
import numpy as np

from evi.util import lane_to_edge


PATTERN_SUMO_0_3_GRID_EDGE = re.compile(
    r'^(?P<start_x>\d+)/(?P<start_y>\d+)to(?P<end_x>\d+)/'
    r'(?P<end_y>\d+)(_\d+)?$'
)
"""
Regular expression pattern to extract start and end positions from the name
of a SUMO edge.
When using netgenerate (from SUMO versions below 1.0) to generate a
grid scenario, edges are named according to the
following scheme:
Assume an edge coming from crossing "1/0"
(2nd crossing from the left, first from the bottom)
and leading towards crossing "2/0",
then its ID will be "1/0to2/0" and its right-most lane will be
called "1/0to2/0_0".
"""

PATTERN_SUMO_1_GRID_EDGE = re.compile(
    r'^(?P<start_x>[a-zA-Z]+)(?P<start_y>\d+)'
    r'(?P<end_x>[a-zA-Z]+)(?P<end_y>\d+)(_\d+)?$'
)

PATTERN_SUMO_0_3_GRID_JUNCTION = re.compile(
    r'^(?P<x>\d+)/(?P<y>\d+)$'
)

PATTERN_SUMO_1_GRID_JUNCTION = re.compile(
    r'^(?P<x>[a-zA-Z]+)(?P<y>\d+)$'
)


def grid_make_edge_id(
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        num_junctions_x: int,
        # ^ only for x b/c only x coordinates need to be converted to letters
        sumo_version: str = '1.0.1',
) -> str:
    if sumo_version.startswith('0.32') or sumo_version.startswith('0.30'):
        return f'{from_x}/{from_y}to{to_x}/{to_y}'
    else:
        # SUMO 1.0 and up
        num_digits = int(math.log(num_junctions_x, 26)) + 1
        return (
            f'{num2col(from_x, min_chars=num_digits)}'
            f'{from_y}{num2col(to_x, min_chars=num_digits)}{to_y}'
        )


def grid_make_lane_id(
        from_x: int,
        from_y: int,
        to_x: int,
        to_y: int,
        num_junctions_x: int,
        sumo_version: str = '1.0.1',
        lane_count: int = 0
) -> str:
    return grid_make_edge_id(
        from_x,
        from_y,
        to_x,
        to_y,
        num_junctions_x,
        sumo_version,
    ) + '_' + str(lane_count)


def num2col(num: int, min_chars=1) -> str:
    """
    Convert num to base 26 with digits from A to Z,
    padded with 'A's to match the minimum length.
    E.g., 0 = A, 25 = Z, 26 = AA.
    """
    col = ''
    while num > 0:
        num, r = divmod(num, 26)
        col = string.ascii_uppercase[r] + col
    return 'A' * (min_chars - len(col)) + col


def col2num(col: str) -> int:
    """
    Convert strings like 'AC' to integer, in this case 2.
    (Base 26, digits are the letters from A to Z.)
    """
    num = 0
    for i, c in enumerate(reversed(col)):
        num += (ord(c.upper()) - ord('A')) * 26 ** i
    return num


def grid_get_edge_name_start_and_end(
        lane_id: str,
        sumo_version: str
) -> Tuple[str, np.ndarray, np.ndarray]:
    """
    Get junction index coordinates for start and end of the edge,
    assuming the route was generated for a grid.

    :param lane_id:
    :param sumo_version:
    :return: Tuple containing the lane's parent edge ID,
        an np.array with its start position,
        an np.array with its end position.
        Note that 'position' here refers to grid indices,
        not absolute coordinates.
    """
    edge_id = lane_to_edge(lane_id)
    if sumo_version.startswith('0.32') or sumo_version.startswith('0.30'):
        m = PATTERN_SUMO_0_3_GRID_EDGE.match(edge_id)
        return (
            edge_id,
            np.array([m.group('start_x'), m.group('start_y')], int),
            np.array([m.group('end_x'), m.group('end_y')], int)
        )
    else:
        # SUMO 1.0 and up
        m = PATTERN_SUMO_1_GRID_EDGE.match(edge_id)
        return (
            edge_id,
            np.array([col2num(m.group('start_x')), m.group('start_y')], int),
            np.array([col2num(m.group('end_x')), m.group('end_y')], int)
        )


# c, s = np.cos(np.pi / 2), np.sin(np.pi / 2)
_C, _S = 0, 1
_ROT_MATRIX_90DEG = np.array([[_C, -_S], [_S, _C]], int)  # counter-clockwise


def grid_get_left_right_straight_from_positions(
        start_x,
        start_y,
        end_x,
        end_y
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Depending on the direction of the current edge
    (determined by its start and end point),
    return the (in this case axis-aligned) direction vectors
    for left, right, and straight.

    :param start_x:
    :param start_y:
    :param end_x:
    :param end_y:
    :return:
    """
    left = np.array([-1, 0], int)
    right = np.array([1, 0], int)
    straight = np.array([0, 1], int)
    dirs = left, right, straight

    def rotate_dirs(multiples_of_90deg):
        """
        Rotate left, right, and straight 90 degrees counter-clockwise
        multiples_of_90deg times.
        """
        r = np.linalg.matrix_power(_ROT_MATRIX_90DEG, multiples_of_90deg)
        return (np.dot(r, d) for d in dirs)

    if start_x == end_x:
        if start_y < end_y:  # direction north
            pass
        else:  # direction south
            left, right, straight = rotate_dirs(2)
    else:  # edge_start_y == edge_end_y:
        if start_x < end_x:  # direction east
            left, right, straight = rotate_dirs(3)
        else:  # direction west
            left, right, straight = rotate_dirs(1)

    return left, right, straight
