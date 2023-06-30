from typing import List, Callable
import typing

from sumolib.net import Net as SumolibNet

from evi.triggers import (
    # TriggerCollection,
    # Trigger,
    TriggerEvent,
    # SpawnEvent,
    # ResumeEvent,
    # SignalEvent,
    # ParkingStopWaypoint,
    # StopWaypoint
)

from ...triggers.trigger_generator import (
    TriggerGenerator,
    TriggerOrMetaTrigger
)

from ...levels.route.level_ego_route import (
    LevelEgoRoute,
    LevelEgoRouteLane
)
# from ...triggers.abstract_meta_trigger import AbstractMetaTrigger

if typing.TYPE_CHECKING:
    from ...route.abstract_ego_route import (
        # AbstractEgoRoute,
        AbstractEgoRouteLane
    )


class LevelTriggerGenerator(TriggerGenerator):
    """
    Helps generating triggers along a predefined route that is divided into
    levels.
    """

    def __init__(
            self,
            ego_route: LevelEgoRoute,
            sumolib_net: SumolibNet,
            sumo_version: str,
            triggers_max_radius: float,
            default_vehicle_type: str,
            events_at_every_lane: List[TriggerEvent] = None,
            events_by_route_index: Callable[
                [int, 'AbstractEgoRouteLane'], List[TriggerEvent]
            ] = None,
            triggers_at_every_lane: List[TriggerOrMetaTrigger] = None,
            triggers_by_route_index: Callable[
                [int, 'AbstractEgoRouteLane'], List[TriggerOrMetaTrigger]
            ] = None,
            triggers_default_offset: float = 0,
            triggers_seed: int = None
    ):
        super().__init__(
            ego_route=ego_route,
            sumolib_net=sumolib_net,
            sumo_version=sumo_version,
            triggers_max_radius=triggers_max_radius,
            default_vehicle_type=default_vehicle_type,
            events_at_every_lane=events_at_every_lane,
            events_by_route_index=events_by_route_index,
            triggers_at_every_lane=triggers_at_every_lane,
            triggers_by_route_index=self._level_triggers_by_route_index,
            triggers_default_offset=triggers_default_offset,
            triggers_seed=triggers_seed
        )
        # In super class, self.triggers_by_route_index is now the same
        # as self._level_triggers_by_route_index.
        # In order to still be able to pass triggers_by_route_index to the
        # constructor,
        # use the following callable in self._level_triggers_by_route_index:
        self._base_triggers_by_route_index = (
            triggers_by_route_index
            if triggers_by_route_index is not None
            else lambda route_elem_index, ego_route_lane: []
        )

        # Update type hints:
        self.ego_route: LevelEgoRoute = self.ego_route

    def _level_triggers_by_route_index(
            self,
            route_elem_index: int,
            route_lane: LevelEgoRouteLane
    ) -> List[TriggerOrMetaTrigger]:
        level_index, level = self.ego_route.level_from_route_elem_index(
            route_elem_index
        )
        if level is None:
            return self._base_triggers_by_route_index(
                route_elem_index,
                route_lane
            )
        return (
            level.meta_triggers
            + self._base_triggers_by_route_index(route_elem_index, route_lane)
        )
