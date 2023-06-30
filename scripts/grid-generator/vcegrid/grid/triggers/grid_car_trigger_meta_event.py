from typing import List, Union, Callable, Optional, Tuple

import numpy as np

from vcegrid.route import AbstractEgoRouteLane
from ...triggers.abstract_meta_trigger import AbstractMetaTrigger
from ..grid_edge_helper import GridEdgeHelper
from evi.triggers import (
    SpawnEvent,
    ResumeEvent,
    Trigger,
    SignalEvent,
    StopWaypoint,
)
from evi.state import VehicleSignal


class GridCarTriggerMetaEvent(AbstractMetaTrigger):
    """
    Can be used by a TriggerGenerator to generate dynamic triggers and events
    — in this case for a grid network.
    """

    def __init__(
            self,
            from_direction_allowed: List[str] = None,
            from_direction_blocked: List[str] = None,
            to_direction_allowed: List[str] = None,
            to_direction_blocked: List[str] = None,
            num_cars: Union[
                int, Callable[[int, 'AbstractEgoRouteLane'], int]
            ] = 1,
            exit_direction: str = None,
            stop: bool = False,
            stop_duration: Union[
                float, Callable[[int, AbstractEgoRouteLane], float]
            ] = 999999,
            resume_edge_pos: float = None,
            open_door_edge_pos: float = None,
            close_door_edge_pos: float = None,
            depart_delay: Union[
                float, Callable[[int, AbstractEgoRouteLane], float]
            ] = None,
            depart_pos_relative: Union[
                float, Callable[[int, AbstractEgoRouteLane, float], float]
            ] = None
    ):
        """
        Some arguments also accept callables, which will be given the current
            route element index as input, as well as the current ego vehicle
            route lane.

        :param from_direction_allowed: Allowed *from* directions relative to
            the ego vehicle route.
            Acceptable values: 'left', 'right', 'straight', 'behind', 'next',
            as well as 'next_if_condition={}', where
            '{}' may be replaced with any custom experiment condition, e.g.,
            'low-traffic', as potentially set in the *.toj-route.yaml for the
            next lane/edge.
        :param from_direction_blocked: Blocked *from* directions relative to
            the ego vehicle.
            Acceptable values: see from_direction_allowed
        :param to_direction: *To* direction relative to the new vehicle.
            Acceptable values:
            'left', 'right', 'straight', 'next', 'intersect', 'random'.
            Here, 'intersect' means that the new vehicle will intersect the
            route of the ego vehicle but not enter its route.
            'next' means that the new vehicle will enter the ego
            vehicle's route.
        :param num_cars: Number of cars to spawn either explicitly or as a
            callable taking as arguments the index of the current route lane,
            as well as that lane itself as an instance of AbstractEgoRouteLane.
        :param exit_direction:
        :param stop: If true, cars will be stopped on the second edge of the
            route to be added.
        :param stop_duration:
        :param resume_edge_pos: Where to place the resume trigger.
            No trigger if None.
            In [0, 1] as fraction of the length of the respective edge.
        :param open_door_edge_pos: Where to place the trigger for opening
            the car door. No trigger if None.
            In [0, 1] as fraction of the length of the respective edge.
        :param close_door_edge_pos: Where to place the trigger for closing
            the car door. No trigger if None.
            In [0, 1] as fraction of the length of the respective edge.
        :param depart_delay: Delay in seconds when to spawn a vehicle after
            the trigger event.
        :param depart_pos_relative: Where on the lane to spawn a vehicle as a
            value between 0 and 1.
            Unlike the other optionally callable arguments, if
            depart_pos_relative is callable, it will take the
            chosen depart_delay as a third argument!
        """
        super().__init__()

        self.from_direction_allowed = (
            from_direction_allowed
            if from_direction_allowed is not None else []
        )
        self.from_direction_blocked = (
            from_direction_blocked
            if from_direction_blocked is not None else []
        )
        self.to_direction_allowed = (
            to_direction_allowed
            if to_direction_allowed is not None else []
        )
        self.to_direction_blocked = (
            to_direction_blocked
            if to_direction_blocked is not None else []
        )
        self.num_cars = num_cars
        self.exit_direction = exit_direction
        self.stop = stop
        self.stop_duration = stop_duration
        self.resume_edge_pos = resume_edge_pos
        self.open_door_edge_pos = open_door_edge_pos
        self.close_door_edge_pos = close_door_edge_pos
        self.depart_delay = depart_delay
        self.depart_pos_relative = depart_pos_relative

        if exit_direction not in {
            'left', 'right', 'straight', 'left_or_right', 'random'
        }:
            raise ValueError(
                f"'{exit_direction}' is not a valid value for the argument "
                "exit_direction."
            )

    @staticmethod
    def apply_progress(
            val,
            route_elem_index: int,
            ego_route_lane: AbstractEgoRouteLane
    ):
        return val(route_elem_index, ego_route_lane) if callable(val) else val

    @staticmethod
    def _convert_source_directions(
            from_directions: List[str],
            current_edge_helper: GridEdgeHelper
    ) -> List[str]:
        """
        Takes a list of abstract directions from the perspective of the ego
        vehicle like, e.g.,
        'next', and converts them to one of the specific
        directions 'left', 'right', 'straight', 'behind'.
        """
        results = []
        for direction in from_directions:
            if direction in {'left', 'right', 'straight', 'behind'}:
                results.append(direction)
            elif (
                    direction.startswith('next')
                    and current_edge_helper.next
                    is not None
            ):
                if direction.startswith('next_if_condition='):
                    cond = direction[len('next_if_condition='):]
                    next_cond = current_edge_helper.next.ego_route_lane.get(
                        'experiment_condition',
                        ''
                    )
                    if cond != next_cond:
                        continue
                results.append(
                    current_edge_helper.get_direction_of(
                        current_edge_helper.next)
                )
            elif direction == 'inverse':
                results.append('behind')
        return results

    def _generate_start_edge(
            self,
            current_edge_helper: GridEdgeHelper,
            next_direction: str
    ) -> Tuple[Optional[GridEdgeHelper], Optional[str]]:
        from_directions = list(
            set(self._convert_source_directions(
                    self.from_direction_allowed,
                    current_edge_helper
            ))
            - set(self._convert_source_directions(
                self.from_direction_blocked,
                current_edge_helper
            ))
        )
        if len(from_directions) == 0:
            return None, None
        from_direction = np.random.choice(from_directions)

        if from_direction == 'behind':
            # car would spawn either on top of us or right behind…
            return current_edge_helper, from_direction
            # TODO?
            #  return (
            #      current_edge_helper.inverse.straight.inverse,
            #      from_direction
            #  )  # the street right behind us
        # i.e. 'left', 'right', or 'straight':
        return current_edge_helper[from_direction].inverse, from_direction

    def _convert_target_directions(
            self,
            to_directions: List[str],
            ego_from_direction: str,
            car_from_edge_h: GridEdgeHelper,
            ego_next_direction: Optional[str],
            ego_next_edge_h: Optional[GridEdgeHelper]
    ) -> List[str]:
        """
        Takes a list of abstract directions from the perspective of the car
        that is to be spawned,
        e.g., 'next' or 'intersect', and converts them to one of the
        specific directions
        'left', 'right', or 'straight'.

        Used in _generate_target_edge to find the set of possible
        target directions.
        """
        results = []
        for direction in to_directions:
            if direction in {'left', 'right', 'straight'}:
                results.append(direction)
            elif direction.startswith('next') and ego_next_edge_h is not None:
                if direction.startswith('next_if_condition='):
                    cond = direction[len('next_if_condition='):]
                    next_cond = ego_next_edge_h.ego_route_lane.get(
                        'condition',
                        ''
                    )
                    # ^ TODO: create a specific MetaEvent subclass for
                    # experiments
                    if cond != next_cond:
                        continue
                results.append(
                    car_from_edge_h.get_direction_of(ego_next_edge_h)
                )
            elif direction == 'intersect':
                intersecting_directions = []
                if ego_from_direction == 'left':
                    # Car is coming from my left
                    if ego_next_direction in {'left', 'straight'}:
                        # I intend to turn left or go straight…
                        intersecting_directions = ['left', 'straight']
                    elif ego_next_direction == 'right':
                        intersecting_directions = ['straight']
                elif ego_from_direction == 'right':
                    if ego_next_direction == 'left':
                        intersecting_directions = ['left', 'straight']
                    elif ego_next_direction == 'right':
                        # In this case, technically, no direction is
                        # intersecting.
                        # TODO: optionally prevent this case from happening by
                        #  catching it in _generate_start_edge?
                        intersecting_directions = ['left', 'right', 'straight']
                    elif ego_next_direction == 'straight':
                        # (Not 'right', because that would be equivalent
                        # to 'next'.)
                        intersecting_directions = ['left', 'straight']
                elif ego_from_direction == 'behind':
                    intersecting_directions = ['right']
                elif ego_from_direction == 'straight':
                    if ego_next_direction == 'left':
                        intersecting_directions = ['straight', 'right']
                    elif ego_next_direction in {'right', 'straight'}:
                        intersecting_directions = ['left']
                if len(intersecting_directions) == 0:
                    # TODO: no exception, just a warning instead?
                    raise Exception(
                        "Unable to intersect path "
                        f"for a car coming from '{ego_from_direction}' "
                        "(generated from allowed"
                        f"='{self.from_direction_allowed}', "
                        f"blocked='{self.from_direction_blocked}'), "
                        f"from_edge='{str(car_from_edge_h)}', "
                        f"next_edge='{str(ego_next_edge_h)}', "
                        f"next_direction='{ego_next_direction}'."
                    )
                results += intersecting_directions
        return results

    def _generate_target_edge(
            self,
            ego_from_direction: str,
            car_from_edge_h: GridEdgeHelper,
            ego_next_edge_h: Optional[GridEdgeHelper],
            ego_next_direction: Optional[str]
    ) -> Tuple[Optional[GridEdgeHelper], Optional[str]]:
        """
        :param ego_from_direction: Relative to ego vehicle;
            'left', 'right', 'straight', or 'behind'.
        :param car_from_edge_h: The edge *from* which the car will come
            (not the ego vehicle's current edge!).
        :param ego_next_edge_h: Next edge on the ego vehicle route.
        :param ego_next_direction: Relative to ego vehicle,
            which direction is the next edge of the experiment route.
        :return: the target edge and its direction relative to the from_edge_h.
            (None, None) if to_direction is 'next' but a next edge
            is not available and
            next_fallback_straight is False, or also if there are any other
            conflicts like
            to_allowed=['left'] and to_blocked=['left'].
        """
        to_directions = list(  # relative to from_edge_h
            set(self._convert_target_directions(
                self.to_direction_allowed,
                ego_from_direction,
                car_from_edge_h,
                ego_next_direction,
                ego_next_edge_h
            )) - set(self._convert_target_directions(
                self.to_direction_blocked,
                ego_from_direction,
                car_from_edge_h,
                ego_next_direction,
                ego_next_edge_h
            ))
        )
        if len(to_directions) == 0:
            return None, None
        to_direction = np.random.choice(to_directions)

        if to_direction in {'left', 'right', 'straight'}:
            return car_from_edge_h[to_direction], to_direction
        else:
            raise ValueError(
                "Unable to generate the target edge from "
                f"{str(car_from_edge_h)} "
                f"(with direction {ego_from_direction} "
                f"of ego vehicle) to '{to_direction}'"
            )

    # override
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
            default offset
            from the start of the lane anyway, add them to this Trigger.
        :return:
        """
        triggers = []

        ego_route = ego_route_lane.ego_route
        current_edge_helper = ego_route.get_edge_helper(route_elem_index)
        assert isinstance(current_edge_helper, GridEdgeHelper)
        net = ego_route.sumo_net
        num_cars = self.apply_progress(
            self.num_cars,
            route_elem_index,
            ego_route_lane
        )

        for car_i in range(num_cars):
            next_direction = (
                current_edge_helper.get_direction_of(current_edge_helper.next)
                if current_edge_helper.next is not None
                else None
            )
            car_route_edge_helpers = []

            # Determine the starting edge and add an edge helper to the list
            # of edges accordingly:
            from_edge_h, from_direction = self._generate_start_edge(
                current_edge_helper,
                next_direction
            )
            if from_edge_h is None:
                return []
            car_route_edge_helpers.append(from_edge_h)

            # "To" edge (sometimes not the final edge):
            to_edge_h, to_direction = self._generate_target_edge(
                ego_from_direction=from_direction,
                car_from_edge_h=from_edge_h,
                ego_next_edge_h=current_edge_helper.next,
                # ^ may turn out to be None
                ego_next_direction=next_direction
            )
            if to_edge_h is None:
                return []
            car_route_edge_helpers.append(to_edge_h)

            # Which final edge to use in order to get out of the ego vehicle's
            # field of view:
            if self.exit_direction is not None:
                exit_direction = self.exit_direction
                exit_direction = (
                    np.random.choice(['left', 'right'])
                    if exit_direction == 'left_or_right'
                    else (
                        np.random.choice(['left', 'right', 'straight'])
                        if exit_direction == 'random'
                        else exit_direction
                    )
                )
                car_route_edge_helpers.append(
                    car_route_edge_helpers[-1][exit_direction]
                )

            depart_delay = self.apply_progress(
                self.depart_delay,
                route_elem_index,
                ego_route_lane
            )
            depart_pos = None
            if self.depart_pos_relative is not None:
                depart_pos = (
                     self.depart_pos_relative
                     if not callable(self.depart_pos_relative)
                     else self.depart_pos_relative(
                         route_elem_index,
                         ego_route_lane,
                         # Additional argument not present via apply_progress;
                         # allows dynamically choosing a higher depart
                         # pos if depart_delay is low, for example:
                         depart_delay
                     )
                 ) * car_route_edge_helpers[0].length
            spawn_event = SpawnEvent(
                num_vehicles=1,
                route_edges=[str(eh) for eh in car_route_edge_helpers],
                depart_delay_seconds=depart_delay,
                depart_pos=depart_pos,
                arrival_pos='max',
            )
            if self.stop:
                stop_edge_h = car_route_edge_helpers[1]
                stop_duration = self.apply_progress(
                    self.stop_duration,
                    route_elem_index,
                    ego_route_lane
                )
                stopped_car_id = (
                    f'parked_car_{np.random.randint(int(1e10), int(1e13))}'
                )

                spawn_event.vehicle_id = stopped_car_id
                # Make this car keep to the right of the edge by using this
                # vType
                # (must be defined in *.rou.xml and SUMO's sublane model must
                # be active):
                spawn_event.vehicle_type = 'parker'
                spawn_event.stops.append(StopWaypoint(
                    edge=str(stop_edge_h),
                    end_pos=.98 * stop_edge_h.length,
                    start_pos=.6 * stop_edge_h.length,
                    duration=stop_duration
                ))

                # TODO: callable edge positions for resuming and
                # opening/closing doors
                # (Ensure there won't be conflicts, i.e. all door events must
                # happen before the car resumes)

                if self.resume_edge_pos is not None:
                    # xy = get_cartesian_from_edge_pos(
                    #     net,
                    #     str(stop_edge_h),
                    #     self.resume_edge_pos * stop_edge_h.length
                    # )
                    # TODO: optionally use xy instead of ego_edge and
                    #  ego_edge_pos
                    #  (which still can be useful for debugging, though!)
                    # TODO: optionally apply an offset in the direction of the
                    # lane to these coordinates!
                    triggers.append(Trigger(
                        note=f"Resume stopped car \"{stopped_car_id}\"",
                        ego_edge=str(stop_edge_h),
                        ego_edge_pos=self.resume_edge_pos * stop_edge_h.length,
                        events=[ResumeEvent(vehicle_id=stopped_car_id)]
                    ))

                if self.open_door_edge_pos is not None:
                    triggers.append(Trigger(
                        note=f"Open door of car \"{stopped_car_id}\"",
                        ego_edge=str(stop_edge_h),
                        ego_edge_pos=self.open_door_edge_pos
                        * stop_edge_h.length,
                        events=[SignalEvent(
                            vehicle_id=stopped_car_id,
                            active_signals=[VehicleSignal.DOOR_OPEN_LEFT]
                        )]
                    ))
                if self.close_door_edge_pos is not None:
                    triggers.append(Trigger(
                        note=f"Close door of car \"{stopped_car_id}\"",
                        ego_edge=str(stop_edge_h),
                        ego_edge_pos=self.close_door_edge_pos
                        * stop_edge_h.length,
                        events=[SignalEvent(
                            vehicle_id=stopped_car_id,
                            active_signals=None
                        )]
                    ))

            default_trigger.events.append(spawn_event)
        return triggers
