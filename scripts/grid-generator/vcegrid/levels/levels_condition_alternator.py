from typing import Any, Union, Callable
import typing

from ..experiments.condition_alternator import ConditionAlternator

if typing.TYPE_CHECKING:
    from .route.level_ego_route import LevelEgoRoute


class LevelsConditionAlternator(ConditionAlternator):
    """
    In contrast to the regular ConditionAlternator,
    this one will reset the alternation scheme at the start of every new level.

    Condition Alternator:
    Helper class for alternating between two different values
    over given intervals and given the number of road edges so far.
    Used primarily for alternating between low and high traffic.
    Intervals needn't be static.
    """

    def __init__(
            self,
            level_ego_route: 'LevelEgoRoute',
            seed=None,
            default_interval_min: Union[int, Callable[[int], int], None] = 1,
            default_interval_max: Union[int, Callable[[int], int], None] = 1,
    ):
        """
        :param seed:
        :param default_interval_min: For determining the next interval,
            unless the current interval hasn't yet reached its end.
            Used with interval_max for a random int in that range.
        :param default_interval_max: See interval_min.
        """
        super().__init__(
            seed=seed,
            default_interval_min=default_interval_min,
            default_interval_max=default_interval_max
        )
        self.level_ego_route = level_ego_route

    # override
    def __call__(
            self,
            num_edges_so_far: int,
            value: Any,
            alternative: Any = 0,
            interval_min: Union[int, Callable[[int], int], None] = None,
            interval_max: Union[int, Callable[[int], int], None] = None,
    ) -> Any:
        """
        Alternate between two different values over given intervals
        and given the number of road edges so far.
        Used primarily for alternating between low and high traffic.
        Intervals needn't be static.

        Example: If TRAFFIC_DENSITY_LOW_HIGH_INTERVAL = 3,
        value = 1, alternative = 0:
        [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, …]

        :param num_edges_so_far: Number of edges so far, usually starting at 0.
        :param value:
        :param alternative:
        :param interval_min: For determining the next interval,
            unless the current interval hasn't yet reached its end.
            Used with interval_max for a random int in that range.
        :param interval_max: See interval_min.
        :return: Either value or alternative, depending on
        """
        return super().__call__(
            num_edges_so_far=(
                self.level_ego_route.index_to_level_route_elem_index(
                    num_edges_so_far)
            ),
            value=value,
            alternative=alternative,
            interval_min=interval_min,
            interval_max=interval_max
        )
