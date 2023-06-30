from typing import Any, List, cast

from sumolib.net import Net as SumolibNet

from .toj_experiment_ego_route import (
    TojExperimentEgoRoute,
    TojExperimentEgoRouteLane,
)
from ...levels import LevelEgoRouteLane, Level, LevelEgoRoute


class LeveledTojExperimentEgoRouteLane(
    TojExperimentEgoRouteLane,
    LevelEgoRouteLane
):

    def __init__(
            self,
            ego_route: 'LeveledTojExperimentEgoRoute',
            lane_id: str = None,
            experiment_condition: Any = None,
            toj_start_offset: float = None,
            toj_end_offset: float = None,
            existing_yaml_dict: dict = None
    ):
        TojExperimentEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            experiment_condition=experiment_condition,
            toj_start_offset=toj_start_offset,
            toj_end_offset=toj_end_offset,
            existing_yaml_dict=existing_yaml_dict
        )
        LevelEgoRouteLane.__init__(
            self,
            ego_route=ego_route,
            lane_id=lane_id,
            existing_yaml_dict=existing_yaml_dict
        )

    # override
    def to_yaml_dict(self) -> dict:
        result = TojExperimentEgoRouteLane.to_yaml_dict(self)
        properties = result[self.lane_id]
        properties.update(LevelEgoRouteLane.to_yaml_dict(self)[self.lane_id])
        return result


class LeveledTojExperimentEgoRoute(
    TojExperimentEgoRoute,
    LevelEgoRoute
):
    # override
    LANE_CLASS = LeveledTojExperimentEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            levels: List[Level],
            existing_yaml_list: List[dict] = None
    ):
        TojExperimentEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            existing_yaml_list=existing_yaml_list
        )
        LevelEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            levels=levels,
            existing_yaml_list=existing_yaml_list
        )

    # override
    def calculate_stats(self, stats: dict = None):
        TojExperimentEgoRoute.calculate_stats(self, stats)
        LevelEgoRoute.calculate_stats(self, stats)

        stats['num_edges_in_levels_by_condition'] = dict()
        for (
                level_i, level, route_i_in_level, route_i, lane
        ) in self.level_route_iterator():
            lane = cast(LeveledTojExperimentEgoRouteLane, lane)
            cond = lane.experiment_condition
            if level is None:
                break
            if cond not in stats['num_edges_in_levels_by_condition']:
                stats['num_edges_in_levels_by_condition'][cond] = 0
            stats['num_edges_in_levels_by_condition'][cond] += 1

    def set_offsets_for_last_edges_of_levels(
            self,
            poi_toj_lane_end_offset_at_level_end: float,
            **kwargs
    ):
        """
        Add an end offset for TOJ trials only for the last lane of a level
        (to avoid overlaps with end of level triggers).

        :param poi_toj_lane_end_offset_at_level_end:
        :param kwargs:
        :return:
        """
        print(f"Levels: {[level.num_edges for level in self.levels]}")
        for (
                level_i, level, route_i_in_level, route_i, lane
        ) in self.level_route_iterator():
            if level is None:
                break  # no more levels
            if route_i_in_level == level.num_edges - 1:
                lane = cast(LeveledTojExperimentEgoRouteLane, lane)
                # ^ safe to cast since this is a LeveledTojExperimentEgoRoute
                lane.toj_end_offset = poi_toj_lane_end_offset_at_level_end
