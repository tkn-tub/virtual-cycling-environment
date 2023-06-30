from typing import List

from .trigger_generator import Trigger
# ^ TODO: shouldn't this be evi.sumo.triggers?
from ..route.abstract_ego_route import AbstractEgoRouteLane


class AbstractMetaTrigger:
    """
    Can be used by a TriggerGenerator to generate dynamic triggers and events.
    """

    def __init__(self):
        pass

    def generate_triggers(
            self,
            route_elem_index: int,
            ego_route_lane: AbstractEgoRouteLane,
            default_trigger: Trigger
    ) -> List[Trigger]:
        """
        Generate triggers and events for a given lane of a route.

        :param route_elem_index:
        :param ego_route_lane:
        :param default_trigger: If your events are to be triggered at the
            default offset from the start of the lane anyway,
            add them to this Trigger.
        :return:
        """
        # Abstract
        pass
