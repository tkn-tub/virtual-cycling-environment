from typing import List, Any, Iterator

import yaml
from sumolib.net import Net as SumolibNet

from evi.util import lane_to_edge
import vcegrid


class AbstractEgoRouteLane:
    """
    Designed to work with multiple inheritance,
    provided this class is used right.
    """

    def __init__(
            self,
            ego_route: 'AbstractEgoRoute',
            lane_id: str = None,
            existing_yaml_dict: dict = None
    ):
        """
        :param ego_route:
        :param lane_id: SUMO lane ID,
            has precedence over setting in existing_yaml_dict!
        :param existing_yaml_dict:
        """
        if lane_id is None and existing_yaml_dict is None:
            raise ValueError(
                "Either a lane ID or an existing YAML dict is required!"
            )

        self.ego_route = ego_route
        self.lane_id = lane_id

        self.remaining_yaml_properties = {}
        """
        dict holding all properties not readable by the current
        AbstractEgoRouteLane subclass.
        This should allow for editing an existing YAML file non-destructively.
        """

        if existing_yaml_dict is not None:
            yaml_lane_id, properties = list(existing_yaml_dict.items())[0]
            # ^ There should only be one item
            self.remaining_yaml_properties = properties
            if self.lane_id is None:
                self.lane_id = yaml_lane_id

    def __getattr__(self, item):
        """
        Is called if self.item does not exist.

        :param item:
        :return: The item if it can be found in the remaining attributes
            not specific to this class,
            None otherwise.
        """
        if item not in self.remaining_yaml_properties:
            # raise AttributeError(
            #     f"Class '{self.__class__.__name__}' "
            #     f"has no attribute '{item}'."
            # )
            return None
        return self.remaining_yaml_properties[item]

    @property
    def sumolib_lane(self):
        return self.ego_route.sumo_net.getLane(self.lane_id)

    def get(self, key: str, default: Any):
        v = (
            self.__getattribute__(key)
            if key in self.__dict__
            else self.__getattr__(key)
        )
        # ^ hasattr(self, key) doesn't work;
        # probably because __getattr__ is implemented…
        return v if v is not None else default

    def _try_set_remaining_property(self, key: str):
        if key not in self.remaining_yaml_properties:
            return
        self.__dict__[key] = self.remaining_yaml_properties.pop(key)

    def to_yaml_dict(self) -> dict:
        return {self.lane_id: self.remaining_yaml_properties}


class AbstractEgoRoute:

    LANE_CLASS = AbstractEgoRouteLane

    def __init__(
            self,
            sumo_net: SumolibNet,
            existing_yaml_list: List[dict] = None,
            **kwargs
    ):
        lane_class = self.__class__.LANE_CLASS
        if not hasattr(self, 'lanes'):
            # Check is necessary because when using multiple inheritance,
            # self.lanes may already exist.
            self.lanes: List[lane_class] = []
        self.sumo_net = sumo_net

        if existing_yaml_list is not None and len(self.lanes) == 0:
            # (If self.lanes is not empty, assume that some grandchild class
            # is using multiple inheritance and calling this constructor more
            # than once.)
            self.lanes = [
                lane_class(ego_route=self, existing_yaml_dict=d)
                for d in existing_yaml_list
            ]

    def __iter__(self) -> Iterator[AbstractEgoRouteLane]:
        for lane in enumerate(self.lanes):
            yield lane

    def get_edge_helper(
            self,
            route_elem_index: int
    ) -> 'vcegrid.AbstractEdgeHelper':
        return vcegrid.AbstractEdgeHelper(
            edge_id=lane_to_edge(self.lanes[route_elem_index].lane_id),
            sumolib_net=self.sumo_net,
            ego_route=self,
            route_elem_index=route_elem_index
        )

    def to_yaml_list(self) -> List[dict]:
        return [lane.to_yaml_dict() for lane in self.lanes]

    @classmethod
    def load(
            cls,
            sumo_net: SumolibNet,
            filename: str,
            **kwargs
    ) -> 'AbstractEgoRoute':
        """
        :param sumo_net:
        :param filename: YAML file name.
        :param kwargs: IMPORTANT: Please make sure that this includes any
            additional arguments that the constructor of this class might need!
        :return:
        """
        with open(filename, 'r') as f:
            yaml_list = yaml.load(f)
        return cls(sumo_net=sumo_net, existing_yaml_list=yaml_list, **kwargs)

    def save(self, filename):
        with open(filename, 'w') as f:
            yaml.dump(self.to_yaml_list(), f, default_flow_style=False)

    def calculate_stats(self, stats: dict):
        stats['route_num_lanes'] = len(self.lanes)
        stats['route_length_meters'] = 0
        for lane in self.lanes:
            stats['route_length_meters'] += lane.sumolib_lane.getLength()
