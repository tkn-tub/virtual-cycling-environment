from typing import Any, List

from sumolib.net import Net as SumolibNet

from .experiment_ego_route import ExperimentEgoRoute, ExperimentEgoRouteLane
from evi.util import empty_dict_if_none


class TojExperimentEgoRouteLane(ExperimentEgoRouteLane):

    def __init__(
            self,
            ego_route: 'TojExperimentEgoRoute',
            lane_id: str = None,
            experiment_condition: Any = None,
            toj_start_offset: float = None,
            toj_end_offset: float = None,
            toj_trial_interval: float = None,
            toj_trials_lateral_offset: float = None,
            existing_yaml_dict: dict = None
    ):
        """
        :param ego_route:
        :param lane_id: SUMO lane ID
        :param toj_start_offset: Minimum distance in m of TOJ points of
            interest (POIs) from the start of a lane.
            Overrides the default of the POI generation settings.
        :param toj_end_offset: Minimum distance in m of TOJ
            points of interest (POIs) from the end of a lane.
            Overrides the default of the POI generation settings.
        """
        super().__init__(
            ego_route=ego_route,
            lane_id=lane_id,
            experiment_condition=experiment_condition,
            existing_yaml_dict=existing_yaml_dict
        )
        self.toj_start_offset = toj_start_offset
        self.toj_end_offset = toj_end_offset
        self.toj_trial_interval = toj_trial_interval
        self.toj_trials_lateral_offset = toj_trials_lateral_offset

        if existing_yaml_dict is not None:
            self._try_set_remaining_property('toj_start_offset')
            self._try_set_remaining_property('toj_end_offset')

    def to_yaml_dict(self) -> dict:
        result = super().to_yaml_dict()
        properties = result[self.lane_id]
        properties.update({
            **empty_dict_if_none('toj_start_offset', self.toj_start_offset),
            **empty_dict_if_none('toj_end_offset', self.toj_end_offset),
            **empty_dict_if_none(
                'toj_trial_interval',
                self.toj_trial_interval
            ),
            **empty_dict_if_none(
                'toj_trials_lateral_offset',
                self.toj_trials_lateral_offset
            )
        })
        return result


class TojExperimentEgoRoute(ExperimentEgoRoute):

    # override
    LANE_CLASS = TojExperimentEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            existing_yaml_list: List[dict] = None
    ):
        super().__init__(
            sumo_net=sumo_net,
            existing_yaml_list=existing_yaml_list
        )
        # Not strictly necessary, but makes code completion work in PyCharm:
        lane_class = self.__class__.LANE_CLASS
        self.lanes: List[lane_class] = self.lanes
