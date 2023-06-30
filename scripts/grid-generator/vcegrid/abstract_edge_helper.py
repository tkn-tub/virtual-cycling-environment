from typing import Tuple, Optional

import numpy as np
from sumolib.net import Net as SumolibNet
from sumolib.net.edge import Edge as SumolibEdge

from .util import get_cartesian_and_direction_and_angle_from_edge_pos
import vcegrid.route as route


class AbstractEdgeHelper:

    def __init__(
            self,
            edge_id: str,
            sumolib_net: SumolibNet,
            ego_route: 'route.AbstractEgoRoute' = None,
            route_elem_index: int = None
    ):
        self.edge_id = edge_id
        self.sumolib_net = sumolib_net
        self.ego_route = ego_route
        self.route_elem_index = route_elem_index

    def __str__(self):
        return self.edge_id

    def __eq__(self, other):
        return self.edge_id == other.edge_id

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def next(self) -> 'Optional[AbstractEdgeHelper]':
        if self.route_elem_index is None or self.ego_route is None:
            raise ValueError(
                f"Edge {self.edge_id} is not set up to be part of a route"
            )
        if self.route_elem_index + 1 >= len(self.ego_route.lanes):
            return None
        return self.ego_route.get_edge_helper(self.route_elem_index + 1)

    @property
    def previous(self) -> 'Optional[AbstractEdgeHelper]':
        if self.route_elem_index is None or self.ego_route is None:
            raise ValueError(
                f"Edge {self.edge_id} is not set up to be part of a route"
            )
        if self.route_elem_index - 1 < 0:
            return None
        return self.ego_route.get_edge_helper(self.route_elem_index - 1)

    @property
    def length(self) -> float:
        return self.sumolib_edge.getLength()

    @property
    def sumolib_edge(self) -> SumolibEdge:
        return self.sumolib_net.getEdge(self.edge_id)

    @property
    def ego_route_lane(self) -> route.AbstractEgoRouteLane:
        return self.ego_route.lanes[self.route_elem_index]

    def get_cartesian_and_direction_and_angle_at(
            self,
            edge_pos: float
    ) -> Tuple[Tuple[float, float], np.ndarray, float]:
        """
        :raise ValueError: if edge_pos goes beyond the defined length
            of the given edge.
        :param edge_pos: Position on the edge in meters from the edge's
            start point.
        :return: Cartesian coordinates (x, y), normalized direction vector,
            and angle in degrees for a given position on a SUMO edge.
        """
        return get_cartesian_and_direction_and_angle_from_edge_pos(
            self.sumolib_net,
            self.edge_id,
            edge_pos
        )
