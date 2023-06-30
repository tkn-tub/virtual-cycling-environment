import typing
from typing import List, Tuple

import numpy as np
import networkx as nx
import time
from sumolib.net import Net as SumolibNet

from vcegrid.grid.util import (
    grid_make_lane_id,
    grid_get_edge_name_start_and_end,
    grid_get_left_right_straight_from_positions
)
import vcegrid.route
import vcegrid.grid
import evi
from ...util import empty_dict_if_none

if typing.TYPE_CHECKING:
    from .. import GridEdgeHelper


class GridEgoRouteLane(vcegrid.route.AbstractEgoRouteLane):

    def __init__(
            self,
            ego_route: 'GridEgoRoute',
            lane_id: str = None,
            grid_next_turn_sign: str = None,
            existing_yaml_dict: dict = None
    ):
        """
        :param ego_route:
        :param lane_id: SUMO lane ID
        :param grid_next_turn_sign: If set to 'left', 'right', or 'straight',
            street signs indicating
            the direction of the next street in the route will be placed in
            the (Unity) visualization.
        """
        vcegrid.route.AbstractEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            existing_yaml_dict=existing_yaml_dict
        )
        self.grid_next_turn_sign = grid_next_turn_sign

        if existing_yaml_dict is not None:
            self._try_set_remaining_property('grid_next_turn_sign')

    def to_yaml_dict(self) -> dict:
        result = vcegrid.route.AbstractEgoRouteLane.to_yaml_dict(self)
        properties = result[self.lane_id]
        properties.update({**empty_dict_if_none(
            'grid_next_turn_sign',
            self.grid_next_turn_sign
        )})
        return result


class GridEgoRoute(vcegrid.route.AbstractEgoRoute):

    # override
    LANE_CLASS = GridEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            grid_num_junctions_x: int,
            grid_num_junctions_y: int,
            existing_yaml_list: List[dict] = None,
            sumo_version: str = '1.0.1'
    ):
        vcegrid.route.AbstractEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            existing_yaml_list=existing_yaml_list
        )
        self.sumo_version = sumo_version
        self._grid_num_junctions_x = grid_num_junctions_x
        self._grid_num_junctions_y = grid_num_junctions_y

        # Not strictly necessary, but makes code completion work in PyCharm:
        lane_class = self.__class__.LANE_CLASS
        self.lanes: List[lane_class] = self.lanes

    # Override
    def get_edge_helper(
            self,
            route_elem_index: int
    ) -> 'GridEdgeHelper':
        return vcegrid.grid.GridEdgeHelper(
            grid_num_junctions_x=self._grid_num_junctions_x,
            grid_num_junctions_y=self._grid_num_junctions_y,
            edge_id=evi.util.lane_to_edge(
                self.lanes[route_elem_index].lane_id),
            sumolib_net=self.sumo_net,
            ego_route=self,
            route_elem_index=route_elem_index,
            sumo_version=self.sumo_version
        )

    def get_left_right_straight(
            self,
            route_elem_index: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Depending on the direction of the current edge
        (determined by its start and end point),
        return the (in this case axis-aligned) direction vectors for
        left, right, and straight.

        :param route_elem_index: Index in the generator's route list
            (loaded from the route YAML).
        :return:
        """
        route_lane = self.lanes[route_elem_index]
        edge_id_name, edge_start, edge_end = grid_get_edge_name_start_and_end(
            route_lane.lane_id,
            sumo_version=self.sumo_version
        )
        return grid_get_left_right_straight_from_positions(
            *edge_start,
            *edge_end
        )

    @staticmethod
    def generate_rectangular(
            sumo_net: SumolibNet,
            grid_route_margin_x=0,
            grid_route_margin_y=0,
            grid_num_junctions_x=15,
            grid_num_junctions_y=15,
            sumo_version='1.0.1',
            **kwargs
    ) -> 'GridEgoRoute':
        """
        :param sumo_net:
        :param grid_route_margin_x:
        :param grid_route_margin_y:
        :param num_junctions_x: Total number of junctions of the grid
            in horizontal direction.
        :param num_junctions_y: Total number of junctions of the grid
            in vertical direction.
        :param sumo_version:
        :return:
        """
        route = []

        min_junction_y = grid_route_margin_y
        max_junction_y = grid_num_junctions_y - grid_route_margin_y - 1
        min_junction_x = grid_route_margin_x
        max_junction_x = grid_num_junctions_x - grid_route_margin_x - 1

        default_lane_params = {}

        # A perfectly rectangular track with a margin of
        # toj_route_junction_skip(_x|_y) junctions
        # from the horizontal and vertical grid street network boundaries.

        gen_kwargs = dict(
            sumo_version=sumo_version,
            num_junctions_x=grid_num_junctions_x,
        )

        # Bottom left to top left:
        junction_x = min_junction_x
        for junction_y in range(min_junction_y, max_junction_y):
            route.append({
                grid_make_lane_id(
                    junction_x,
                    junction_y,
                    junction_x,
                    junction_y + 1,
                    **gen_kwargs
                ): default_lane_params.copy()
            })

        # Top left to top right:
        junction_y = max_junction_y
        for junction_x in range(min_junction_x, max_junction_x):
            route.append({
                grid_make_lane_id(
                    junction_x,
                    junction_y,
                    junction_x + 1,
                    junction_y,
                    **gen_kwargs
                ): default_lane_params.copy()
            })

        # Top right to bottom right:
        junction_x = max_junction_x
        for junction_y in range(max_junction_y, min_junction_y, -1):
            route.append({
                grid_make_lane_id(
                    junction_x,
                    junction_y,
                    junction_x,
                    junction_y - 1,
                    **gen_kwargs
                ): default_lane_params.copy()
            })

        # Bottom right to bottom left:
        junction_y = min_junction_y
        for junction_x in range(max_junction_x, min_junction_x, -1):
            route.append({
                grid_make_lane_id(
                    junction_x,
                    junction_y,
                    junction_x - 1,
                    junction_y,
                    **gen_kwargs
                ): default_lane_params.copy()
            })

        return GridEgoRoute(
            sumo_net=sumo_net,
            grid_num_junctions_x=grid_num_junctions_x,
            grid_num_junctions_y=grid_num_junctions_y,
            existing_yaml_list=route,
            sumo_version=sumo_version
        )

    @staticmethod
    def generate_random(
            sumo_net: SumolibNet,
            grid_route_margin_x=0,
            grid_route_margin_y=0,
            grid_num_junctions_x=15,
            grid_num_junctions_y=15,
            grid_route_seed=None,
            grid_route_randomization_steps=10000,
            grid_route_print_progress=False,
            sumo_version='1.0.1',
            **kwargs
    ):
        """
        Generate a random Hamiltonian path (aka. self-avoiding walk (SAW))
        through a grid network.

        :param sumo_net:
        :param grid_route_margin_x:
        :param grid_route_margin_y:
        :param grid_num_junctions_x: Total number of junctions of the grid
            in horizontal direction.
        :param grid_num_junctions_y: Total number of junctions of the grid
            in vertical direction.
        :param grid_route_seed:
        :param grid_route_randomization_steps:
        :param grid_route_print_progress:
        :param toj_route_add_direction_signs:
        :param toj_route_condition_markers: Adds a key-value pair of
            'condition' and whatever the callable
            toj_route_condition_markers returns for the input of the index of
            an edge within the route up to that point.
        :param toj_difficulty_levels: If set, add level markers to each lane
            in the route.
            Each item in this list must have at least an attribute 'difficulty'
            (any str as a name) and 'num_edges'
            (the number of edges in this level).
        :param sumo_version:
        :return:
        """
        default_lane_params = {}

        walk = GridEgoRoute._get_self_avoiding_walk_on_lattice(
            lattice_width=grid_num_junctions_x - 2 * grid_route_margin_x,
            lattice_height=grid_num_junctions_y - 2 * grid_route_margin_y,
            steps=grid_route_randomization_steps,
            seed=grid_route_seed,
            print_progress=grid_route_print_progress
        )
        offset = np.array([grid_route_margin_x, grid_route_margin_y])
        route = [
            {
                grid_make_lane_id(
                    *(walk[i] + offset),
                    *(step + offset),
                    num_junctions_x=grid_num_junctions_x,
                    sumo_version=sumo_version
                ):
                    default_lane_params.copy()
            }
            for i, step in enumerate(walk[1:])
        ]
        return GridEgoRoute(
            sumo_net=sumo_net,
            grid_num_junctions_x=grid_num_junctions_x,
            grid_num_junctions_y=grid_num_junctions_y,
            existing_yaml_list=route,
            sumo_version=sumo_version
        )

        # TODO: difficulty level markers (in levels package)

    @staticmethod
    def _get_self_avoiding_walk_on_lattice(
            lattice_width,
            lattice_height,
            steps=int(1e6),
            seed=None,
            print_progress=False
    ):
        """
        Based on "Secondary structures in long compact polymers." 2006.
        Richard Oberdorf, Allison Ferguson, Jesper L. Jacobsen,
        and Jané Kondev.
        http://doi.org/10.1103/PhysRevE.74.051801

        :return: A list of tuples (x, y) corresponding to lattice coordinates.
        """
        if lattice_width < 2 or lattice_height < 2:
            raise Exception(
                "Lattices for get_self_avoiding_walk_on_lattice "
                "must be at least 2x2. "
                f"You tried {lattice_height}x{lattice_width} (height x width)."
            )

        # for resetting later if seed is set
        random_state = np.random.get_state()
        if seed is not None:
            np.random.seed(seed)

        # Create an undirected graph for the lattice/grid to operate on.
        # Nodes will be tuples of the form (x, y), where the maximum y is
        # equal to lattice_height-1.
        lattice_graph = nx.grid_2d_graph(lattice_width, lattice_height)
        lattice_graph_original = lattice_graph.copy()

        # Remove some of the edges just created s.t. we get the "plough",
        # an initial non-random Hamiltonian path.
        # Unlike FIG. 1 in the paper, we start in the bottom left going right.
        # 4x4:
        #
        #  x-x-x-x
        #        |
        #  x-x-x-x
        #  |
        #  x-x-x-x
        #        |
        #  x-x-x-x
        #
        for y in range(lattice_height - 1):
            for x in range(lattice_width):
                if x == lattice_width - 1 and y % 2 == 0:
                    # Do not remove vertical edge on right border if y is even:
                    continue
                if x == 0 and y % 2 != 0:
                    # Do not remove vertical edge on left border if y is odd:
                    continue
                lattice_graph.remove_edge((x, y), (x, y + 1))

        start_node = (0, 0)
        end_node = (
            (0, lattice_height - 1)
            if lattice_height % 2 == 0
            else (lattice_width - 1, lattice_height - 1)
        )

        # Repeatedly perform the "backbite" move:
        time_start = time.time()
        time_prev = time.time()
        for step in range(steps):
            if print_progress and time.time() - time_prev > .5:
                print(
                    f"Randomizing a Hamiltonian path: {step / steps:.1%}, "
                    f"elapsed time: {time.time() - time_start:.1f} s, "
                    f"step {step}/{steps}"
                )
                time_prev = time.time()

            start_neighbors = set(lattice_graph.neighbors(start_node))
            end_neighbors = set(lattice_graph.neighbors(end_node))
            start_all_possible_neighbors = set(
                lattice_graph_original.neighbors(start_node)
            )
            end_all_possible_neighbors = set(
                lattice_graph_original.neighbors(end_node)
            )
            start_unconnected_neighbors = list(
                start_all_possible_neighbors - start_neighbors
            )
            end_unconnected_neighbors = list(
                end_all_possible_neighbors - end_neighbors
            )

            # Randomly determine which adjacent site to connect to either the
            # start or the end point:
            k = np.random.randint(
                len(start_unconnected_neighbors)
                + len(end_unconnected_neighbors)
            )
            if k < len(start_unconnected_neighbors):
                terminating_node = start_node
                neighbor_node = start_unconnected_neighbors[k]
            else:
                terminating_node = end_node
                neighbor_node = end_unconnected_neighbors[
                    k - len(start_unconnected_neighbors)
                ]

            # one link to be removed
            neighbor_neighbors = list(lattice_graph.neighbors(neighbor_node))

            # TODO: The paper describes an adjustment where the backbite
            #  move is only made with a certain
            #  probability…
            #  But then it would be done in the next step…
            #  I don't think I get what they mean exactly…

            # Add this edge:
            lattice_graph.add_edge(terminating_node, neighbor_node)

            # Delete that edge connected to neighbor_node which is
            # "uniquely characterized by being part of a cycle (closed path)
            # and not being the link just added:"
            try:
                # TODO: can this be made quicker?
                cycle = nx.find_cycle(lattice_graph, source=neighbor_node)
            except nx.NetworkXNoCycle as e:
                # This should never happen
                raise e
            for candidate_neighbor in neighbor_neighbors:
                if (
                        (candidate_neighbor, neighbor_node) in cycle
                        or (neighbor_node, candidate_neighbor) in cycle
                ):
                    lattice_graph.remove_edge(
                        candidate_neighbor,
                        neighbor_node
                    )
                    # Move start or end point accordingly:
                    if terminating_node == start_node:
                        start_node = candidate_neighbor
                    else:
                        end_node = candidate_neighbor
                    break

        if seed is not None:
            np.random.set_state(random_state)

        # Create a list of nodes and return it:
        previous_node = start_node
        current_node = list(lattice_graph.neighbors(start_node))[0]
        walk = [start_node, current_node]
        while len(walk) < lattice_width * lattice_height:
            next_node = (
                set(lattice_graph.neighbors(current_node)) - {previous_node}
            ).pop()
            walk.append(next_node)
            previous_node = current_node
            current_node = next_node
        return walk

    def generate_direction_sign_markers(self):
        """
        Generate direction markers in this route.
        These markers may be used later to generate points of interest (POIs)
        for street signs.
        """
        for route_elem_index, route_lane in enumerate(self.lanes[:-1]):
            current_edge_helper = self.get_edge_helper(route_elem_index)
            next_edge_helper = self.get_edge_helper(route_elem_index + 1)
            next_edge = str(next_edge_helper)
            if str(current_edge_helper.straight) == next_edge:
                next_turn = 'straight'
            elif str(current_edge_helper.left) == next_edge:
                next_turn = 'left'
            elif str(current_edge_helper.right) == next_edge:
                next_turn = 'right'
            else:
                raise Exception(
                    "GridEgoRoute.generate_direction_signs: Can't determine "
                    f"direction to next_edge={next_edge} "
                    f"from current_edge={str(current_edge_helper)}!"
                )

            route_lane.grid_next_turn_sign = next_turn
