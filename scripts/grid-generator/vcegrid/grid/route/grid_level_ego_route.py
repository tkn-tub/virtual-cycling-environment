from typing import List

from sumolib.net import Net as SumolibNet

from ...levels.route.level_ego_route import LevelEgoRoute, LevelEgoRouteLane
from ...levels.level import Level
from .grid_ego_route import GridEgoRoute, GridEgoRouteLane


class GridLevelEgoRouteLane(LevelEgoRouteLane, GridEgoRouteLane):

    def __init__(
            self,
            ego_route: 'GridLevelEgoRoute',
            lane_id: str = None,
            grid_next_turn_sign: str = None,
            existing_yaml_dict: dict = None
    ):
        LevelEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            existing_yaml_dict=existing_yaml_dict
        )
        GridEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            grid_next_turn_sign=grid_next_turn_sign,
            existing_yaml_dict=existing_yaml_dict
        )

    def to_yaml_dict(self) -> dict:
        result = LevelEgoRouteLane.to_yaml_dict(self)
        properties = result[self.lane_id]
        properties.update(GridEgoRouteLane.to_yaml_dict(self)[self.lane_id])
        return result


class GridLevelEgoRoute(LevelEgoRoute, GridEgoRoute):

    # override
    LANE_CLASS = GridLevelEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            levels: List[Level],
            grid_num_junctions_x: int,
            grid_num_junctions_y: int,
            sumo_version: str = '1.0.1',
            existing_yaml_list: List[dict] = None
    ):
        LevelEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            levels=levels,
            existing_yaml_list=existing_yaml_list
        )
        GridEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            grid_num_junctions_x=grid_num_junctions_x,
            grid_num_junctions_y=grid_num_junctions_y,
            sumo_version=sumo_version,
            existing_yaml_list=existing_yaml_list
        )

        # Not strictly necessary, but makes code completion work in PyCharm:
        lane_class = self.LANE_CLASS
        self.lanes: List[lane_class] = self.lanes
