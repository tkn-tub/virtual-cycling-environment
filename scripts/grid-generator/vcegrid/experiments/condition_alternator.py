from typing import Any, Union, Callable

from random import Random


# TODO: generalize for an arbitrary number of conditions

class ConditionAlternator:
    """
    Helper class for alternating between two different values
    over given intervals and given the number of road edges so far.
    Used primarily for alternating between low and high traffic.
    Intervals needn't be static.
    """

    def __init__(
            self,
            seed=None,
            default_interval_min: Union[int, Callable[[int], int], None] = 1,
            default_interval_max: Union[int, Callable[[int], int], None] = 1,
    ):
        """
        :param seed:
        :param default_interval_min: For determining the next interval, unless the current interval hasn't yet reached its end.
            Used with interval_max for a random int in that range.
        :param default_interval_max: See interval_min.
        """
        self.default_interval_min = default_interval_min
        self.default_interval_max = default_interval_max

        self.current_interval_start = 0
        self.current_interval_length = 0
        self.use_alternative = True  # Will be flipped on first call

        # We need an internal RNG here to allow two alternators to produce the
        # same intervals if the intervals are to be randomized.
        # This is necessary because we need an alternator both for generating
        # the points of interest (POIs) for SUMO, as well as for generating
        # the vehicle spawn points and other level-based event triggers.
        self.random = Random(seed)

    @staticmethod
    def _eval_callable(v: Any, num_edges: int) -> Any:
        return v(num_edges) if callable(v) else v

    def __call__(
            self,
            num_edges_so_far: int,
            value: Any,
            alternative: Any = 0,
            interval_min: Union[int, Callable[[int], int], None] = None,
            interval_max: Union[int, Callable[[int], int], None] = None,
    ) -> Any:
        """
        Alternate between two different values over given intervals and given
        the number of road edges so far.
        Used primarily for alternating between low and high traffic.
        Intervals needn't be static.

        Example: If TRAFFIC_DENSITY_LOW_HIGH_INTERVAL = 3, value = 1,
        alternative = 0:
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
        interval_min = (
            interval_min
            if interval_min is not None
            else self.default_interval_min
        )
        interval_max = (
            interval_max
            if interval_max is not None
            else self.default_interval_max
        )

        if num_edges_so_far == 0:
            # Reset this alternator.
            # Necessary if num_edges_so_far repeatedly jumps back to 0, e.g.
            # because it is defined as the number of edges
            # so far in a current level.
            self.current_interval_start = 0
            self.current_interval_length = 0
        if (
                num_edges_so_far
                >= self.current_interval_start + self.current_interval_length
        ):
            self.current_interval_start = num_edges_so_far
            self.use_alternative = not self.use_alternative
            self.current_interval_length = self.random.randint(
                self._eval_callable(interval_min, num_edges_so_far),
                self._eval_callable(interval_max, num_edges_so_far)
            )
        if self.use_alternative:
            return self._eval_callable(alternative, num_edges_so_far)
        else:
            return self._eval_callable(value, num_edges_so_far)
