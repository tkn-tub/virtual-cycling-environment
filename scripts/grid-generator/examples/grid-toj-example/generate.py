#! /usr/bin/env python3

from typing import List

import numpy as np
import yaml
from sumolib.net import readNet
import vcegrid.grid
from vcegrid.experiments import (
    LeveledTojExperimentEgoRoute,
)
from vcegrid.levels import (
    Level,
    LevelsConditionAlternator,
    LevelTriggerGenerator,
    TutorialInstruction
)
from vcegrid.grid import GridCarTriggerMetaEvent, GridLevelEgoRoute
from vcegrid.points_of_interest import (
    PoiGenerator,
    create_pois_toj_trials,
    create_poi_ego_vehicle_start,
    create_pois_direction_signs,
    create_pois_priority_signs,
    create_pois_end_of_level,
    create_pois_tutorial_banners,
)
from vcegrid.levels import LevelEgoRoute
from vcegrid.sumo_network import (
    initialize_routes_file,
    write_evi_configuration,
    write_sumo_configuration
)


EDGES_PER_LEVEL = 26


def get_levels(block: int) -> List[Level]:
    if block == 0:
        return [  # experiment block 0
            Level(
                difficulty='tutorial',
                num_edges=4,
                tutorial_instructions=[
                    TutorialInstruction(
                        message="",
                        step=0,
                        lane_index_in_level=0,
                        offset_from_edge_start=0,
                        lateral_offset=0
                    ),
                    TutorialInstruction(
                        message="",
                        step=1,
                        lane_index_in_level=0,
                        offset_from_edge_start=10,
                        lateral_offset=0
                    ),
                    TutorialInstruction(
                        message="",
                        step=2,
                        lane_index_in_level=0,
                        offset_from_edge_start=17,
                        lateral_offset=0
                    ),
                ]
            ),
            Level(
                difficulty='level-1',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=1, p_per_car=1),
                    spawn_cars_from_lr_to_lrs(n=2, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=2, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=1, p_per_car=.5),
                ]
            ),
            Level(
                difficulty='level-2',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=3, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=2, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=1, p_per_car=.5),
                ]
            ),
            Level(
                difficulty='level-3',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=3, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=2, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=1, p_per_car=.5),
                ]
            ),
        ]
    else:
        return [  # experiment block 1
            Level(
                difficulty='level-4',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=3, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=2, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=1, p_per_car=.5),
                ]
            ),
            Level(
                difficulty='level-5',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=3, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=2, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=1, p_per_car=.5),
                ]
            ),
            Level(
                difficulty='level-6',
                num_edges=EDGES_PER_LEVEL,
                meta_triggers=[
                    spawn_cars_from_lr_to_lrs(n=3, p_per_car=.666),
                    spawn_intersecting_cars_from_lr(n=3, p_per_car=.5),
                    spawn_oncoming_intersecting_cars(n=2, p_per_car=.5),
                ]
            ),
        ]

    # Please note:
    # In the previous implementation, it was possible to define meta triggers
    # in groups for every junction, where the meta triggers of the first group
    # would be applied to the current junction, those of the second group to
    # the next junction (but triggered at the current junction), and so on.
    # This is useful, e.g., for cars that are supposed to stop in some
    # distance farther ahead.
    #
    # Previously, this was implemented in the triggers generation loop.
    # Now it would probably be more elegant and similarly easy/difficulty to
    # just adapt the meta trigger implementation and use a chain like
    # lane.next.next…


def get_settings(block: int):
    """
    Generates a settings dict.
    For possible settings and how to use them, look into the documentation of
    the functions used in main(),
    if available, or their respective code.

    :param block: Return different settings for different experiment blocks.
    :return:
    """
    scenario = f'grid-toj_block{block}'
    update_interval = .1
    # ^ in seconds; set here for SUMO and EVI, but must also be set in Unity!!!
    return {
        'sumo_version': '1.1.0',
        'sumo_use_sublane_model': True,
        'sumo_sublane_lateral_resolution': .6,
        'sumo_step_length': update_interval,
        'evi_sync_interval_ms': update_interval * 1e3,
        'evi_sumo_keep_route': 0,  # see EVI documentation and
        # https://sumo.dlr.de/wiki/TraCI/Change_Vehicle_State#move_to_XY_.280xb4.29
        # (probably important for not being ignored by other vehicles)

        'sumo_net_filename': f'{scenario}.net.xml',
        'sumo_poly_filename': f'{scenario}.poly.xml',
        'sumo_rou_filename': f'{scenario}.rou.xml',
        'sumo_cfg_filename': f'{scenario}.sumo.cfg',
        'sumo_remote_cfg_filename': f'{scenario}.remote-sumo.cfg',
        # ^ used by *.evi-remote-sumo.ini
        'evi_cfg_filename': f'{scenario}.evi.ini',
        'evi_remote_sumo_cfg_filename': f'{scenario}.evi-remote-sumo.ini',
        # ^ if you don't want EVI to launch SUMO
        'triggers_filename': f'{scenario}.triggers.yaml',
        'toj_route_filename': f'{scenario}.toj-route.yaml',
        'stats_filename': f'{scenario}.stats.txt',

        'grid_num_junctions_x': 15,
        'grid_num_junctions_y': 15,
        'grid_street_len_x': 35,
        'grid_street_len_y': 35,
        'grid_attach_len': 100,
        'lane_width': 3.8,
        'netgenerate_cmd': 'netgenerate',
        'grid_default_speed': 9,  # in m/s; 9 m/s = 32.4 km/h
        'grid_default_lane_number': 1,
        'grid_no_turnarounds': True,
        'grid_default_junction_type': 'priority',
        # ^ 'right_before_left', 'priority', …
        # See `netgenerate --help` for all options (netgenerate default is
        # 'priority')
        'grid_default_junction_radius': 5,
        'grid_junctions_small_radius': 0,
        'grid_junctions_internal_link_detail': 16,
        'grid_junctions_corner_detail': 5,
        'grid_junctions_limit_turn_speed': .85,
        # ^ max. lateral acceleration in m/s^2
        'grid_street_margin': 0,
        # ^ for buildings generation; when in doubt, set to 0
        'grid_building_margin': 8,
        'grid_route_margin_x': 1,
        'grid_route_margin_y': 1,
        'grid_route_seed': 424244 if block == 0 else 434348,
        # ^ seeds chosen s.t. the first edges are South to North
        'grid_route_randomization_steps': 1000,
        'grid_route_print_progress': True,

        'triggers_max_radius': 3,  # m
        'default_vehicle_type': 'default',
        # ^ for vehicle spawning and for the generation of SUMO's *.rou.xml
        'triggers_default_offset': -2.5,  # m from the start of each lane
        'triggers_seed': 128128,

        'poi_start_pos_backwards_offset': 10,
        # ^ Let the ego vehicle spawn 10 meters in front of the first lane.
        'poi_default_toj_trial_interval': 9,  # in m
        'poi_default_toj_trial_lateral_offset': 3.8 / 4,
        # ^ in m to the right from center of the lane
        'poi_reset_toj_trial_offset_for_every_lane': True,
        # ^ fine in a grid network, not so good if lanes are directly attached
        # to one another
        'poi_toj_default_lane_start_offset': -2,
        # ^ default offset in m of trial POIs from the start of a lane
        'poi_toj_default_lane_end_offset': 0,
        # ^ default offset in m of trial POIs from the end of a lane
        'poi_toj_lane_end_offset_at_level_end': 12,
        'poi_direction_signs_offset_from_lane_center': 3.8 / 2 + .3,
        # ^ half the street width + offset
        'poi_priority_direction': 'vertical',  # 'horizontal' or 'vertical'
        'poi_priority_signs_offset_from_lane_center': 1.8,  # in m to the right
        'poi_end_of_level_end_of_lane_offset': 4,  # m
        'poi_end_of_level_lateral_offset': -3.8 / 2,
        # ^ in m to the right -> Move to center of the (entire) street
    }


def main():
    for block in [0, 1]:
        print(f"\n\n##### GENERATING SCENARIO FOR BLOCK {block}\n\n")

        stats = {}  # later to be written to YAML

        settings = get_settings(block=block)
        levels = get_levels(block=block)

        vcegrid.grid.generate_grid_net(**settings)
        vcegrid.grid.generate_grid_buildings_simple(**settings)

        # Read the net we just generated for future use:
        sumo_net = readNet(settings['sumo_net_filename'])

        # --- ROUTE GENERATION ---

        route = vcegrid.grid.GridEgoRoute.generate_random(sumo_net, **settings)
        route.generate_direction_sign_markers()
        # ^ TODO: is this even necessary or can this be merged w/ POI
        # generation?

        # Convert route to LeveledTojExperimentEgoRoute for generation of
        # condition and level markers:
        route = LeveledTojExperimentEgoRoute(
            sumo_net=sumo_net,
            levels=levels,
            existing_yaml_list=route.to_yaml_list(),
            stats=stats
        )
        # Alternator for switching between low and high traffic every couple
        # of lanes:
        traffic_alternator = LevelsConditionAlternator(
            level_ego_route=route,
            seed=323234 if block == 0 else 333335,
            # ^ Seeds chosen s.t. the number of trials per condition is
            # somewhat balanced (see *.stats.txt).
            default_interval_min=2,  # min number of lanes per condition
            default_interval_max=5  # max number of lanes per condition
        )
        # Mark edges of the route as either 'high-traffic' or 'low-traffic'.
        # This will later be used when generating traffic events.
        route.add_experiment_condition_markers(
            markers_gen=lambda lane_i, exp_lane: traffic_alternator(
                num_edges_so_far=lane_i,
                value='high-traffic',
                alternative='low-traffic'
            )
        )
        route.set_offsets_for_last_edges_of_levels(route=route, **settings)

        route.save(settings['toj_route_filename'])

        # --- TRIGGERS GENERATION ---

        # Convert route to GridLevelEgoRoute for trigger generation:
        # (Will need to get GridEdgeHelper, but also the lengths of levels,
        # etc.
        # Trigger generation will also read the current lane's experiment
        # condition, but that will also work without subclassing
        # ExperimentEgoRoute.)
        route = GridLevelEgoRoute(
            sumo_net=sumo_net,
            levels=levels,
            grid_num_junctions_x=settings['grid_num_junctions_x'],
            grid_num_junctions_y=settings['grid_num_junctions_y'],
            sumo_version=settings['sumo_version'],
            existing_yaml_list=route.to_yaml_list()
        )
        trigger_gen = LevelTriggerGenerator(
            ego_route=route,
            # ^ must be a subclass of GridEgoRoute and LevelEgoRoute, and for
            # my purposes it should additionally
            # also be either a subclass of ExperimentEgoRoute or, equivalently,
            # have an experiment_condition
            # attribute for every edge that is part of a level.
            sumolib_net=sumo_net,
            sumo_version=settings['sumo_version'],
            triggers_max_radius=settings['triggers_max_radius'],
            default_vehicle_type=settings['default_vehicle_type'],
            triggers_default_offset=settings['triggers_default_offset'],
            triggers_seed=settings['triggers_seed']
        )
        trigger_gen.generate()  # TODO: seed(s)?
        trigger_gen.save(filename=settings['triggers_filename'])

        # --- POINTS OF INTEREST (POI) GENERATION ---

        stats['poi'] = {}
        poi_generator = PoiGenerator(
            ego_route=route,
            # ^ should be a subclass of LevelEgoRoute for some of the functions
            # below
            sumo_additionals_filename=settings['sumo_poly_filename']
        )
        create_pois_toj_trials(
            poi_generator=poi_generator,
            # Specify trial POI name suffixes to be read by Unity.
            # At present, Unity expects names of the format
            # "Psych_Trial_<integer index>_<level-name>_<condition,
            # e.g. low-traffic>".
            poi_toj_id_suffix=lambda lane_i, trial_i: get_poi_toj_id_suffix(
                route, lane_i, trial_i),
            stats=stats['poi'],
            # ^ Will store number of trials for each lane of the route
            # (used below for end of level POIs so we can calculate the maximum
            # number of points per level in Unity)
            **settings
        )
        num_trials_by_level = get_num_trials_by_level(stats, route)
        create_poi_ego_vehicle_start(poi_generator=poi_generator, **settings)
        create_pois_direction_signs(poi_generator=poi_generator, **settings)
        create_pois_priority_signs(poi_generator=poi_generator, **settings)
        create_pois_end_of_level(
            poi_generator=poi_generator,
            # We need to encode the number of trials per level in the POI ID so
            # we can determine the maximum number of points in Unity at the end
            # of each level:
            poi_end_of_level_id_generator=(
                lambda level_i, level, lane_i_in_level, lane_i, lane:
                f'endOfLevel_{level_i}/{len(route.levels)}_'
                f'{num_trials_by_level[level_i]}trials_{level.difficulty}'
            ),
            **settings,
        ),
        create_pois_tutorial_banners(
            poi_generator=poi_generator,
            **settings,
        )
        # ^ (At this point, the implementation of tutorial banners in Unity
        # still is hard-coded to display help messages for a TOJ experiment.
        # This should be relatively easy to generalize, though.)
        poi_generator.save()

        # --- CONFIG FILES GENERATION ---

        initialize_routes_file(
            filename=settings['sumo_rou_filename'],
            route=route,
            **settings,
        )
        write_sumo_configuration(
            filename=settings['sumo_cfg_filename'],
            **settings,
        )
        write_sumo_configuration(
            filename=settings['sumo_remote_cfg_filename'],
            sumo_remote_port=8813,
            **settings,
        )
        write_evi_configuration(
            filename=settings['evi_cfg_filename'],
            **settings,
        )
        write_evi_configuration(
            filename=settings['evi_remote_sumo_cfg_filename'],
            remote_sumo=True,
            **settings,
        )

        # --- SAVE STATS ---

        stats['poi'].pop('num_trials_by_route_elem_index')
        # ^ too long and irrelevant (intermediate result)

        with open(settings['stats_filename'], 'w') as f:
            yaml.dump(stats, f, default_flow_style=False)


def get_poi_toj_id_suffix(
        route: GridLevelEgoRoute,
        lane_i: int,
        trial_i: int,
) -> str:
    level_i, level = route.level_from_route_elem_index(lane_i)
    route_lane = route.lanes[lane_i]
    return (
        f'{level.difficulty if level is not None else "NO-LEVEL-NAME"}'
        f'_{route_lane.experiment_condition}'
    )


def get_num_trials_by_level(
        stats: dict,
        route: LevelEgoRoute
) -> List[int]:
    num_trials_by_route_elem_index = stats[
        'poi'
    ]['num_trials_by_route_elem_index']
    num_trials_by_level = [0] * len(route.levels)
    for level_i, level, lane_i_in_level, lane_i, route_lane in (
            route.level_route_iterator()):
        if level_i is None:
            break
        num_trials_by_level[level_i] += num_trials_by_route_elem_index[lane_i]
    return num_trials_by_level


def spawn_cars_from_lr_to_lrs(n: int, p_per_car: float):
    """
    :param n: n for the binomial distribution: how many cars to spawn with
        probability p_per_car
    :param p_per_car:
    :return:
    """
    return GridCarTriggerMetaEvent(
        from_direction_allowed=['left', 'right'],
        from_direction_blocked=['next_if_condition=low-traffic'],
        to_direction_allowed=['left', 'right', 'straight'],
        to_direction_blocked=['next_if_condition=low-traffic'],
        num_cars=lambda route_i, lane: (
            np.random.binomial(n, p_per_car)
            if lane.experiment_condition == 'high-traffic'
            else 0
        ),
        exit_direction='left_or_right',
        depart_delay=lambda route_i, lane: get_random_depart_delay(),
        depart_pos_relative=lambda route_i, lane, depart_delay: (
            get_random_relative_depart_pos(depart_delay)
        )
    )


def spawn_intersecting_cars_from_lr(n: int, p_per_car: float):
    return GridCarTriggerMetaEvent(
        from_direction_allowed=['left', 'right'],
        from_direction_blocked=['next_if_condition=low-traffic'],
        to_direction_allowed=['intersect'],
        to_direction_blocked=['next_if_condition=low-traffic'],
        num_cars=lambda route_i, lane: (
            np.random.binomial(n, p_per_car)
            if lane.experiment_condition == 'high-traffic'
            else 0
        ),
        exit_direction='left_or_right',
        depart_delay=lambda route_i, lane: get_random_depart_delay(),
        depart_pos_relative=lambda route_i, lane, depart_delay: (
            get_random_relative_depart_pos(depart_delay)
        )
    )


def spawn_oncoming_intersecting_cars(n: int, p_per_car: float):
    return GridCarTriggerMetaEvent(
        from_direction_allowed=['straight'],
        to_direction_allowed=['intersect'],
        to_direction_blocked=['next_if_condition=low-traffic'],
        num_cars=lambda route_i, lane: (
            np.random.binomial(n, p_per_car)
            if lane.experiment_condition == 'high-traffic'
            else 0
        ),
        exit_direction='random',
        depart_delay=None,  # for now
        depart_pos_relative=None
    )


def spawn_stopping_cars(
        n: int,
        p_per_car: float,
        open_door=False,
        resume=True,
):
    return GridCarTriggerMetaEvent(
        from_direction_allowed=['left', 'right', 'straight'],
        from_direction_blocked=['next', 'next_if_condition=low-traffic'],
        to_direction_allowed=['next_if_condition=high-traffic'],
        # ^ TODO: fallback?
        num_cars=lambda route_i, lane: (
            np.random.binomial(n, p_per_car)
            if lane.experiment_condition == 'high-traffic'
            else 0
        ),
        exit_direction='random',
        stop=True,
        stop_duration=999999,  # TODO? randomize
        **(
            {
                'open_door_edge_pos': .2,
                'close_door_edge_pos': .4
            } if open_door else dict()
        ),
        **(
            {
                'resume_edge_pos': .5
            } if resume else dict()
        ),
        depart_delay=None,  # for now
        depart_pos_relative=None
    )


def get_random_depart_delay(max_delay: float = 7):
    # Beta distribution determined by trial and error.
    # Makes low delays more likely. E[x] ~= .2 * max_delay.
    return np.random.beta(.82, 3.35) * max_delay


def get_random_relative_depart_pos(
        depart_delay: float,
        max_early: float = .75,
        max_late: float = .5,
):
    if depart_delay > 3.5:
        # After 3 s, I assume there's a good chance that the cyclist can now
        # see some distance left and right into the intersection.
        # -> Pick a random distribution that favors low values for
        # departure positions:
        return np.random.beta(1.44, 3.35) * max_late  # E[x] ~= .3 * max_late
    else:
        # The ego vehicle just entered the lane (assuming all car spawning
        # trigger points are still located at the beginning of lanes).
        # -> Pick a random distribution that favors high values for
        # departure positions:
        return np.random.beta(4.37, 3.71) * max_early


if __name__ == '__main__':
    main()
