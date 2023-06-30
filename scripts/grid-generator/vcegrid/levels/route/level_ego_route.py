from typing import List, Tuple, Optional, Iterator

from sumolib.net import Net as SumolibNet

from ... import route
from ... import levels


class LevelEgoRouteLane(route.AbstractEgoRouteLane):

    def __init__(
            self,
            ego_route: 'LevelEgoRoute',
            lane_id: str = None,
            existing_yaml_dict: dict = None
    ):
        route.AbstractEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            existing_yaml_dict=existing_yaml_dict
        )

        # if existing_yaml_dict is not None:
        #     self._try_set_remaining_property()

    def to_yaml_dict(self) -> dict:
        result = route.AbstractEgoRouteLane.to_yaml_dict(self)
        # properties = result[self.lane_id]
        # properties.update(…)
        return result


class LevelEgoRoute(route.AbstractEgoRoute):

    # override
    LANE_CLASS = LevelEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            levels: List['levels.Level'],
            existing_yaml_list: List[dict] = None,
            **kwargs
    ):
        route.AbstractEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            existing_yaml_list=existing_yaml_list,
            **kwargs
        )
        self.levels = levels

        # Not strictly necessary, but makes code completion work in PyCharm:
        lane_class = self.LANE_CLASS
        self.lanes: List[lane_class] = self.lanes

    def index_to_level_route_elem_index(self, route_elem_index: int) -> int:
        """
        Convert a total number of edges so far to the number of edges in the
        current level so far.
        """
        level_edges = 0
        for level in self.levels:
            if level_edges + level.num_edges > route_elem_index:
                break
            level_edges += level.num_edges
        return route_elem_index - level_edges

    def level_route_iterator(
            self
    ) -> Iterator[Tuple[
        Optional[int],
        Optional['levels.Level'],
        Optional[int],
        int,
        LevelEgoRouteLane
    ]]:
        """
        Iterate over the route and the list of levels simultaneously.
        Each iteration returns the following tuple:
        level index, Level, route element index in level, route element index,
        LevelEgoRouteLane.

        If the route continues after all levels have been processed,
        level index, and Level will be None.
        """
        level_i = (
            0
            if self.levels is not None and len(self.levels) > 0
            else None
        )
        lane_i_in_lvl = 0

        for lane_i, lane in enumerate(self.lanes):
            level = self.levels[level_i] if level_i is not None else None

            yield level_i, level, lane_i_in_lvl, lane_i, lane

            lane_i_in_lvl += 1
            if level_i is not None and lane_i_in_lvl >= level.num_edges:
                if level_i + 1 < len(self.levels):
                    lane_i_in_lvl = 0
                    level_i += 1
                else:
                    level_i = None

    def level_from_route_elem_index(
            self,
            route_elem_index: int
    ) -> Tuple[Optional[int], Optional['levels.Level']]:
        level_edges = 0
        for i, level in enumerate(self.levels):
            if level_edges + level.num_edges > route_elem_index:
                return i, level
            level_edges += level.num_edges
        return None, None

    # override
    def calculate_stats(self, stats: dict):
        super().calculate_stats(stats)

        if 'levels' not in stats:
            stats['levels'] = [dict()] * len(self.levels)
        for i, level in enumerate(self.levels):
            stats['levels'][i].update({
                'difficulty': level.difficulty,
                'num_edges': level.num_edges
            })

        # TODO: distances in levels
