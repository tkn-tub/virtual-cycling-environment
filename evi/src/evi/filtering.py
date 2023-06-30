"""
Filter out a subset of vehicles
"""

import math


def distances_to_ego_vehicle(vehicles, ego_vehicle):
    """
    Compute distances for all vehicles to ego_vehicle.
    """
    for vehicle in vehicles:
        distance = math.sqrt(
            ((vehicle.position.x - ego_vehicle.position.x) ** 2)
            + ((vehicle.position.y - ego_vehicle.position.y) ** 2)
        )
        yield (distance, vehicle.id)


def select_vehicles_by_distance(vehicles, ego_vehicle, max_vehicles):
    """
    Return up to max_vehicles from vehicles closest to the ego vehicle.

    The passed in vehicles should not contain any ego vehicle!
    Result does *not* contain ego_vehicle.
    """
    if max_vehicles is None or len(vehicles) < max_vehicles:
        return vehicles
    distances = list(sorted(distances_to_ego_vehicle(vehicles, ego_vehicle)))
    assert len(distances) == len(vehicles)
    vehicle_ids = {
        vehicle_id for distance, vehicle_id in distances[:max_vehicles]
    }
    assert (
        len(vehicles) >= max_vehicles and len(vehicle_ids) == max_vehicles
    ) or len(vehicle_ids) == len(distances)
    return frozenset(
        vehicle for vehicle in vehicles if vehicle.id in vehicle_ids
    )


def select_fellows_equally_distributed(vehicles, ego_vehicles, max_vehicles):
    """
    Select closest fellows for ego_vehicles, dividing max_vehicles equally.

    Returns a frozenset of up to max_vehicles from traffic.
    """
    fellows_per_ego = (
        (max_vehicles // len(ego_vehicles))
        if max_vehicles is not None
        else None
    )
    fellows = set()
    for ego_vehicle in ego_vehicles:
        fellows |= select_vehicles_by_distance(
            vehicles, ego_vehicle, fellows_per_ego
        )
    return frozenset(fellows)


def select_fellows_round_robin(vehicles, ego_vehicles, max_vehicles):
    """
    Select fellows from vehicles by selecting the closest one to each ego.

    Returns a frozenset of up to max_vehicles from traffic.
    """
    if max_vehicles is None or len(vehicles) < max_vehicles:
        return vehicles
    distance_queues = [
        list(sorted(distances_to_ego_vehicle(vehicles, ego_vehicle)))
        for ego_vehicle in ego_vehicles
    ]
    fellow_ids = set()
    ego_index = 0
    max_vehicles = min(max_vehicles, len(vehicles))
    while len(fellow_ids) < max_vehicles:
        assert any(distance_queues)
        current_queue = distance_queues[ego_index]
        ego_index = (ego_index + 1) % len(distance_queues)

        # find the next new fellow for the current ego vehicle
        while current_queue:
            _, candidate_id = current_queue.pop(0)
            if candidate_id not in fellow_ids:
                fellow_ids.add(candidate_id)
                break
    return frozenset(
        vehicle for vehicle in vehicles if vehicle.id in fellow_ids
    )


FELLOW_FILTERS = {
    "statically_distributed": select_fellows_equally_distributed,
    "round_robin": select_fellows_round_robin,
}


def split_vehicles(new_fellows, old_fellows):
    """
    Split vehicles up in added, removed, and modified vehicles.
    """
    veh_newer = {v.id: v for v in new_fellows}
    veh_older = {v.id: v for v in old_fellows}
    ids_newer = frozenset(veh_newer)
    ids_older = frozenset(veh_older)
    return dict(
        add=frozenset(veh_newer[i] for i in ids_newer.difference(ids_older)),
        rem=frozenset(veh_older[i] for i in ids_older.difference(ids_newer)),
        mod=frozenset(veh_newer[i] for i in ids_newer.intersection(ids_older)),
    )


class TrafficFilter:
    """
    Stateful filter to derive traffic changes from vehicle updates.
    """

    def __init__(
        self,
        filter_function,
        prune_egos,
        filter_kwargs=None,
        initial_traffic=frozenset(),
    ):
        self._filter_function = filter_function
        self._prune_egos = prune_egos
        self._filter_kwargs = (
            filter_kwargs if filter_kwargs is not None else dict()
        )
        self._last_fellows = initial_traffic

    def derive_changes(self, traffic, ego_vehicles):
        """
        Derive changes in filtered traffic compared to previous traffic.
        """
        fellows = self._filter_function(
            traffic, ego_vehicles, **self._filter_kwargs
        )
        if self._prune_egos:
            assert not {ego.id for ego in ego_vehicles}.intersection(
                {veh.id for veh in traffic}
            )
        else:
            fellows = fellows | ego_vehicles
        # compare new fellows to old ones
        traffic_changes = split_vehicles(fellows, self._last_fellows)
        assert self.check_consistency(traffic_changes)
        self._last_fellows = fellows
        return traffic_changes

    def check_consistency(self, traffic_changes):
        """Check consistency of fellow updates with previous fellow state."""
        if "max_vehicles" in self._filter_kwargs:
            max_vehicles = self._filter_kwargs["max_vehicles"]
            assert max_vehicles is None or (
                len(traffic_changes["add"])
                + len(traffic_changes["mod"])
                - len(traffic_changes["rem"])
                <= max_vehicles
            )
        last_ids = {veh.id for veh in self._last_fellows}
        for add_vehicle in traffic_changes["add"]:
            assert add_vehicle.id not in last_ids
        for rem_vehicle in traffic_changes["rem"]:
            assert rem_vehicle.id in last_ids
        for mod_vehicle in traffic_changes["mod"]:
            assert mod_vehicle.id in last_ids
        return True
