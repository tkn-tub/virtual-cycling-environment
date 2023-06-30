from typing import List, Callable, Any

from sumolib.net import Net as SumolibNet

from ...route.abstract_ego_route import AbstractEgoRoute, AbstractEgoRouteLane
from ...util import empty_dict_if_none


class ExperimentEgoRouteLane(AbstractEgoRouteLane):

    def __init__(
            self,
            ego_route: 'ExperimentEgoRoute',
            lane_id: str = None,
            experiment_condition: Any = None,
            existing_yaml_dict: dict = None
    ):
        """
        :param ego_route:
        :param lane_id: SUMO lane ID
        """
        super().__init__(
            ego_route=ego_route,
            lane_id=lane_id,
            existing_yaml_dict=existing_yaml_dict,
        )
        self.experiment_condition = experiment_condition

        if existing_yaml_dict is not None:
            self._try_set_remaining_property('experiment_condition')

    def to_yaml_dict(self) -> dict:
        result = super().to_yaml_dict()
        properties = result[self.lane_id]
        properties.update({**empty_dict_if_none(
            'experiment_condition',
            self.experiment_condition
        )})
        return result


class ExperimentEgoRoute(AbstractEgoRoute):

    # override
    LANE_CLASS = ExperimentEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            existing_yaml_list: List[dict] = None,
            **kwargs
    ):
        AbstractEgoRoute.__init__(
            self,
            sumo_net=sumo_net,
            existing_yaml_list=existing_yaml_list,
            **kwargs
        )
        # Not strictly necessary, but makes code completion work in PyCharm:
        lane_class = self.__class__.LANE_CLASS
        self.lanes: List[lane_class] = self.lanes

    def add_experiment_condition_markers(
            self,
            markers_gen: Callable[[int, ExperimentEgoRouteLane], Any]
    ):
        for route_elem_index, route_lane in enumerate(self.lanes):
            route_lane.experiment_condition = markers_gen(
                route_elem_index,
                route_lane
            )

