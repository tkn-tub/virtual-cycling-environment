from typing import Optional, Iterable, Sequence, cast

from sumolib.net import Net as SumolibNet

from vcegrid import AbstractEdgeHelper
from vcegrid.grid.route import GridEgoRoute, GridEgoRouteLane
from vcegrid.grid.util import (
    grid_make_edge_id,
    grid_get_edge_name_start_and_end,
    grid_get_left_right_straight_from_positions
)
from evi.util import edge_lane_nr_to_lane_id


class GridEdgeHelper(AbstractEdgeHelper):

    def __init__(
            self,
            grid_num_junctions_x: int,
            grid_num_junctions_y: int,
            sumolib_net: SumolibNet,
            grid_edge_pos_start: Iterable = None,
            grid_edge_pos_end: Iterable = None,
            edge_id: str = None,
            ego_route: GridEgoRoute = None,
            route_elem_index: int = None,
            sumo_version: str = '1.0.1'
    ):
        if edge_id is None:
            if grid_num_junctions_x is None:
                raise ValueError(
                    "If no edge_id is given, "
                    "the grid scenario's number of junctions in x direction "
                    "is required."
                )
            edge_id = grid_make_edge_id(
                *grid_edge_pos_start,
                *grid_edge_pos_end,
                num_junctions_x=grid_num_junctions_x,
                sumo_version=sumo_version
            )
        elif grid_edge_pos_start is None or grid_edge_pos_end is None:
            _, grid_edge_pos_start, grid_edge_pos_end = (
                grid_get_edge_name_start_and_end(
                    edge_lane_nr_to_lane_id(edge_id, 0),
                    sumo_version=sumo_version
                )
            )

        super().__init__(
            edge_id=edge_id,
            sumolib_net=sumolib_net,
            ego_route=ego_route,
            route_elem_index=route_elem_index
        )

        self._grid_edge_pos_start = grid_edge_pos_start
        self._grid_edge_pos_end = grid_edge_pos_end
        self.sumo_version = sumo_version
        self._grid_num_junctions_x = grid_num_junctions_x
        self._grid_num_junctions_y = grid_num_junctions_y

        self._v_left, self._v_right, self._v_straight = (
            grid_get_left_right_straight_from_positions(
                *self._grid_edge_pos_start,
                *self._grid_edge_pos_end
            )
        )

        # Update type hints:
        self.ego_route: GridEgoRoute

    def __getitem__(self, item) -> Optional['GridEdgeHelper']:
        """
        helper[-2] returns the same result as helper.previous.previous.
        helper[2] returns the same result as helper.next.next.
        helper['left'] returns the same result as helper.left, etc.

        :param item:
        :return:
        """
        if (
                isinstance(item, int)
                and self.route_elem_index is not None
                and (
                    0
                    <= self.route_elem_index + item
                    < len(self.ego_route.lanes)
                )
        ):
            return self.ego_route.get_edge_helper(self.route_elem_index + item)
        elif isinstance(item, str):
            if item == 'inverse':
                return self.inverse
            if item == 'left':
                return self.left
            if item == 'right':
                return self.right
            if item == 'straight':
                return self.straight
        return None

    @property
    def ego_route_lane(self) -> GridEgoRouteLane:
        return cast(GridEgoRouteLane, super().ego_route_lane)

    @property
    def next(self) -> Optional['GridEdgeHelper']:
        return super().next

    @property
    def previous(self) -> Optional['GridEdgeHelper']:
        return super().previous

    def _new_from_positions(self, start: Sequence, end: Sequence):
        if not (
                0 <= start[0] < self._grid_num_junctions_x
                and 0 <= start[1] < self._grid_num_junctions_y
                and 0 <= end[0] < self._grid_num_junctions_x
                and 0 <= end[1] < self._grid_num_junctions_y
        ):
            # Not within grid bounds.
            return None
        return GridEdgeHelper(
            sumolib_net=self.sumolib_net,
            grid_edge_pos_start=start,
            grid_edge_pos_end=end,
            edge_id=None,
            grid_num_junctions_x=self._grid_num_junctions_x,
            grid_num_junctions_y=self._grid_num_junctions_y,
            ego_route=self.ego_route,
            sumo_version=self.sumo_version
        )

    @property
    def cardinal_direction(self) -> str:
        """
        :return: Either "North", "South", "East", or "West".
        """
        if self._grid_edge_pos_start[0] < self._grid_edge_pos_end[0]:
            return "East"
        if self._grid_edge_pos_start[0] > self._grid_edge_pos_end[0]:
            return "West"
        if self._grid_edge_pos_start[1] < self._grid_edge_pos_end[1]:
            return "North"
        if self._grid_edge_pos_start[1] > self._grid_edge_pos_end[1]:
            return "South"
        raise ValueError(
            "Unable to determine cardinal direction from grid edge positions "
            f"{self._grid_edge_pos_start} "
            f"and {self._grid_edge_pos_end}."
        )

    @property
    def inverse(self) -> 'GridEdgeHelper':
        return self._new_from_positions(
            self._grid_edge_pos_end,
            self._grid_edge_pos_start
        )

    @property
    def left(self) -> 'GridEdgeHelper':
        """
        The next edge (helper) if you traverse this edge from start to end and
        turn left.
        """
        next_junction_left = self._grid_edge_pos_end + self._v_left
        return self._new_from_positions(
            self._grid_edge_pos_end,
            next_junction_left
        )

    @property
    def right(self):
        """
        The next edge (helper) if you traverse this edge from start to end and
        turn right.
        """
        next_junction_right = self._grid_edge_pos_end + self._v_right
        return self._new_from_positions(
            self._grid_edge_pos_end,
            next_junction_right
        )

    @property
    def straight(self):
        """
        The next edge (helper) if you traverse this edge from start to end and
        go straight.
        """
        next_junction_straight = self._grid_edge_pos_end + self._v_straight
        return self._new_from_positions(
            self._grid_edge_pos_end,
            next_junction_straight
        )

    def get_direction_of(self, other) -> str:
        for d in ['right', 'straight', 'left', 'inverse']:
            if self[d] == other:
                return d
        raise ValueError(
            f"Unable to determine the direction of edge '{other}' "
            f"from the end of '{self}'."
        )
