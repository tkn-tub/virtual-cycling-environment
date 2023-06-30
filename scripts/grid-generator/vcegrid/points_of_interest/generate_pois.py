from typing import Optional, Callable, List

# import sumolib.shapes.poi as sumo_poi
# ^ No point importing this. It doesn't even support setting an angle
# and XML support seems limited:
# http://sumo.dlr.de/wiki/Simulation/Shapes#POI_.28Point_of_interest.29_Definitions

# import xml.etree.ElementTree as ET

# Use lxml's etree instead of xml.etree.ElementTree because the latter doesn't
# write line breaks
# (API is practically the same):
from lxml import etree as et

import numpy as np
import math
from collections import deque

from ..route.abstract_ego_route import AbstractEgoRoute, AbstractEgoRouteLane
from ..grid.route.grid_ego_route import GridEgoRoute
from ..levels.route.level_ego_route import LevelEgoRoute
from ..levels.level import Level, TutorialInstruction


# POI Reference:
# http://sumo.dlr.de/wiki/Simulation/Shapes#POI_.28Point_of_interest.29_Definitions

TRIAL_POI = {
    'imgFile': 'arrow.png',
    'width': '3',
    'height': '3',
    'layer': '5',
    'type': 'Psych_Trial',
    'posLat': '0',
    'color': '1,0.3725,0',  # orange
}

START_POI = {
    'width': '7',
    'height': '7',
    'layer': '5',
    'type': 'EgoVehicleStart',
    'posLat': '0',
    'color': '1,1,0',  # yellow
}

NEXT_TURN_STREET_SIGN_POI = {
    'width': '3',
    'height': '3',
    'layer': '5',
    'type': 'streetSign_nextTurn_',  # To be changed on use
    'posLat': '0',
    'color': '0,0.4,.8',  # blue
}

END_OF_LEVEL_POI = {
    'type': 'EndOfLevel',
    'width': '7',
    'height': '7',
    'posLat': '0',
    'color': '0.5,.7,1',  # light blue
}

TUTORIAL_POI = {
    'type': 'TutorialBanner',
    'width': '7',
    'height': '7',
    'color': '0.5,1,0.5',  # light green
}


class PoiGenerator:
    """
    Helps writing new points of interest (POIs) to a SUMO additionals
    *.xml file.
    """

    def __init__(
            self,
            ego_route: AbstractEgoRoute,
            sumo_additionals_filename: str = None,
    ):
        """
        :param ego_route:
        :param sumo_additionals_filename: Filename of a SUMO additionals XML
            file.
            If not given, a new XML tree will be created.
            In that case, keep in mind that PoiGenerator.save will require a
            filename!
        """
        self.ego_route = ego_route
        self.sumo_additionals_filename = sumo_additionals_filename

        if sumo_additionals_filename is not None:
            # Read existing additionals *.xml file as basis for appending POIs:
            # Use a parser w/ remove_blank_text=True for indentation to work
            # correctly later
            # (see https://stackoverflow.com/a/7904066/1018176).
            parser = et.XMLParser(remove_blank_text=True)
            self.xml_root = et.parse(
                sumo_additionals_filename,
                parser
            ).getroot()
        else:
            # Create a new ElementTree to later store as XML:
            self.xml_root = et.Element('additionals')
        self.xml_tree = et.ElementTree(self.xml_root)

    def add_poi(self, xml_properties: dict):
        new_poi = et.SubElement(self.xml_root, 'poi')
        for k, v in xml_properties.items():
            new_poi.set(k, v)
        return new_poi

    def save(self, sumo_additionals_filename=None):
        filename = (
            self.sumo_additionals_filename
            if sumo_additionals_filename is None
            else sumo_additionals_filename
        )
        self.xml_tree.write(
            filename,
            encoding="iso-8859-1",
            xml_declaration=True,
            pretty_print=True
        )


def create_poi_ego_vehicle_start(
        poi_generator: PoiGenerator,
        poi_start_pos_backwards_offset: float = 0,
        **kwargs
):
    """
    Add exactly one POI as an indicator for the ego vehicle start position.
    """
    eh = poi_generator.ego_route.get_edge_helper(0)
    start_coord, v_dir, start_angle_deg = (
        eh.get_cartesian_and_direction_and_angle_at(0)
    )

    start_coord = (
        np.array(start_coord)
        - v_dir * poi_start_pos_backwards_offset
    )

    properties = START_POI.copy()
    properties.update({
        'id': 'EgoVehicleStart0',
        'x': f'{start_coord[0]}',
        'y': f'{start_coord[1]}',
        'angle': f'{start_angle_deg}'
    })
    poi_generator.add_poi(xml_properties=properties)


def create_pois_toj_trials(
        poi_generator: PoiGenerator,
        poi_default_toj_trial_interval: float = 10,
        poi_default_toj_trial_lateral_offset: float = 0,  # from lane center
        poi_reset_toj_trial_offset_for_every_lane=False,
        poi_toj_default_lane_start_offset: float = 0,
        poi_toj_default_lane_end_offset: float = 0,
        poi_toj_id_suffix: Optional[Callable[[int, int], str]] = None,
        stats: dict = None,
        **kwargs
):
    """
    Generate SUMO points of interest (POIs) for
    - temporal order judgment (TOJ) trials

    :param poi_generator:
    :param poi_default_toj_trial_interval: Trial interval in meters.
    :param poi_default_toj_trial_lateral_offset: Lateral offset from the center
        of a lane towards the right in meters.
    :param poi_reset_toj_trial_offset_for_every_lane: If False, treat connected
        lanes like connected lane segments,
        i.e. if a POI is placed at the very end of a lane,
        the configured distance between POIs will
        be used as a start offset for the next lane.
    :param poi_toj_default_lane_start_offset: Default minimum distance in m
        from the beginning of a lane where the first
        point of interest should be placed.
    :param poi_toj_default_lane_end_offset: Default minimum distance in m of
        TOJ POIs from the end of a lane.
    :param poi_toj_id_suffix: An optional callable mapping the current lane
        count and the current POI count (0-based)
        to a suffix for the POI identifier.
        When running a TOJ experiment in Unity,
        the POI IDs of a TOJ trial will be logged.
        Therefore, this option can be very useful if you wish to categorize
        TOJ trials in some way based on their position.
    :param stats:
    :return:
    """

    if stats is not None:
        stats['num_trials_by_route_elem_index'] = []

    trial_count = 0

    # Place the first POI on the current lane only after this offset in meters:
    # (Can be extended via route lane properties;
    # will be updated at the end of processing of each lane.)
    lane_offset = 0

    for route_elem_index, route_lane in enumerate(
            poi_generator.ego_route.lanes
    ):
        poi_interval = route_lane.get(
            'toj_trial_interval',
            poi_default_toj_trial_interval
        )
        poi_lateral_offset = route_lane.get(
            'toj_trials_lateral_offset',
            poi_default_toj_trial_lateral_offset
        )

        sumo_lane = route_lane.sumolib_lane
        verts = sumo_lane.getShape3D()

        if poi_reset_toj_trial_offset_for_every_lane:
            lane_offset = route_lane.get(
                'toj_start_offset',
                poi_toj_default_lane_start_offset
            )
        else:
            # lane_offset is set to the remaining segment_offset after every
            # iteration, but the route YAML may also configure a (minimum)
            # offset for this lane:
            lane_offset = max(
                route_lane.get(
                    'toj_start_offset',
                    poi_toj_default_lane_start_offset
                ),
                lane_offset
            )
        lane_end_offset = route_lane.get(
            'toj_end_offset',
            poi_toj_default_lane_end_offset
        )

        # Place the first POI on the current lane segment only after this
        # offset in meters:
        segment_offset = lane_offset

        # Distance covered so far within the current lane in meters
        # (excluding offsets!):
        distance_in_lane = 0

        num_trials_in_lane = 0

        for segment_i, segment in enumerate(zip(verts, verts[1:])):
            # A lane consists of segments, each segment being defined by two
            # consecutive vertices v_start and v_end in verts.
            v_start, v_end = np.array(segment)

            segment_length = np.linalg.norm(v_end - v_start)
            v_direction = (v_end - v_start) / segment_length
            v_dir_ortho_right = np.array([v_direction[1], -v_direction[0]])

            poi_distances_from_segment_start = np.arange(
                start=segment_offset,
                # stop:  |----|---|---|,
                # end offset = 4 -> |----|--<end offset>-|---|
                #   lane.length - distance_in_lane = remaining length in lane
                stop=(
                    min(
                        segment_length,
                        sumo_lane.getLength()
                        - lane_end_offset
                        - distance_in_lane
                    )
                    if segment_i < len(verts) - 2 else
                    # last segment: allow negative offset:
                    sumo_lane.getLength() - lane_end_offset - distance_in_lane
                ),
                step=poi_interval
            )

            angle = -math.degrees(math.atan2(v_direction[1], v_direction[0]))

            for poi_distance_from_segment_start in (
                    poi_distances_from_segment_start
            ):
                v_poi = v_start + poi_distance_from_segment_start * v_direction
                v_poi = v_poi[:2]  # we need only x and y
                v_poi += v_dir_ortho_right * poi_lateral_offset

                poi_properties = TRIAL_POI.copy()
                poi_id = f'Psych_Trial_{trial_count:d}'
                if poi_toj_id_suffix is not None:
                    poi_id += '_' + poi_toj_id_suffix(
                        route_elem_index,
                        trial_count
                    )
                poi_properties.update({
                    'id': poi_id,
                    # To make positioning in Unity easier, we'll also provide
                    # x and y even though "lane" and "pos" would suffice
                    # in other applications:
                    'x': f'{v_poi[0]}',
                    'y': f'{v_poi[1]}',
                    # Providing 'lane' and 'pos' would only make sense if we
                    # didn't allow negative offsets
                    # 'lane': lane_id,
                    # pos: Offsets are contained in
                    # poi_distance_from_segment_start, not in distance_in_lane!
                    # 'pos':
                    # f'{distance_in_lane + poi_distance_from_segment_start}',
                    'angle': f'{angle}',
                })
                poi_generator.add_poi(poi_properties)

                trial_count += 1
                # num_trials_in_level_so_far += 1  # TODO: re-enable?
                num_trials_in_lane += 1

            # Stats:
            # if current_difficulty_level is not None:
            #     if 'num_trials_in_levels_by_condition' not in stats:
            #         stats['num_trials_in_levels_by_condition'] = dict()
            #     if 'condition' in lane_params:
            #         condition = lane_params['condition']
            #         if condition not in stats[
            #                'num_trials_in_levels_by_condition'
            #         ]:
            #             stats['num_trials_in_levels_by_condition'][
            #                 condition
            #             ] = 0
            #         else:
            #             stats['num_trials_in_levels_by_condition'][
            #                 condition
            #             ] += num_trials_in_lane

            remaining_distance_to_segment_end = (
                segment_length
                - (len(poi_distances_from_segment_start) - 1) * poi_interval
                - segment_offset
            )
            segment_offset = poi_interval - remaining_distance_to_segment_end
            distance_in_lane += segment_length

        if stats is not None:
            stats['num_trials_by_route_elem_index'].append(num_trials_in_lane)

        lane_offset = segment_offset


def create_pois_direction_signs(
        poi_generator: PoiGenerator,
        poi_direction_signs_offset_from_lane_center: float = 1.8,
        **kwargs
):
    """

    :param poi_generator: Please make sure that the AbstractEgoRoute subclass
        that his PoiGenerator operates on is a GridEgoRoute!
    :param poi_direction_signs_offset_from_lane_center: Offset from the center
        of a lane in meters to the right.
    :return:
    """
    for route_elem_index, route_lane in enumerate(
            poi_generator.ego_route.lanes
    ):
        next_turn_sign = route_lane.grid_next_turn_sign
        if next_turn_sign is None:
            continue
        eh = poi_generator.ego_route.get_edge_helper(route_elem_index)
        sumo_lane = route_lane.sumolib_lane
        coord, v_direction, angle_deg = (
            eh.get_cartesian_and_direction_and_angle_at(
                edge_pos=sumo_lane.getLength() - .1
                # TODO: make offset configurable
            )
        )

        v_dir_ortho_right = np.array([v_direction[1], -v_direction[0]])
        sign_pos = (
            coord
            + poi_direction_signs_offset_from_lane_center
            * v_dir_ortho_right
        )

        properties = NEXT_TURN_STREET_SIGN_POI.copy()
        properties.update({
            'type': properties['type'] + next_turn_sign,
            # ^ e.g. "NextTurn_left" (or right or straight)
            'x': f'{sign_pos[0]}',
            'y': f'{sign_pos[1]}',
            'angle': f'{angle_deg - 90}',
            'id': f'next_turn_from_{route_lane.lane_id}'
        })
        poi_generator.add_poi(properties)


def create_pois_priority_signs(
        poi_generator: PoiGenerator,
        poi_priority_direction='horizontal',
        poi_priority_signs_offset_from_lane_center=1.8,
        **kwargs
):
    """

    :param poi_generator: Please make sure that the AbstractEgoRoute subclass
        that his PoiGenerator operates on is a GridEgoRoute!
    :param poi_priority_signs_offset_from_lane_center: Offset from the center
        of a lane in meters to the right.
    :return:
    """
    all_properties = {
        'priority': {
            'type': 'streetSign_priority',
            'imgFile': 'priority.png',
            'color': '1,1,1'
        },
        'yield': {
            'type': 'streetSign_yield',
            'imgFile': 'yield.png',
            'color': '1,1,1'
        }
    }
    ego_route = poi_generator.ego_route
    assert isinstance(ego_route, GridEgoRoute)

    for route_elem_index, route_lane in enumerate(ego_route.lanes):
        eh = ego_route.get_edge_helper(route_elem_index)

        edges = deque([
            eh,
            eh.right.inverse,
            eh.straight.inverse,
            eh.left.inverse
        ])
        h_cdir = eh.cardinal_direction
        h_is_horizontal = h_cdir == "East" or h_cdir == "West"
        if ((poi_priority_direction == 'horizontal' and not h_is_horizontal) or
                (poi_priority_direction == 'vertical' and h_is_horizontal)):
            # We want the list of edges to be 'priority', 'yield', 'priority',
            # 'yield'.
            # Shift all items to the right by one (last will be the first):
            edges.rotate(1)

        for e, sign_type in zip(edges, ['priority', 'yield'] * 2):
            pos, v_dir, angle_deg = e.get_cartesian_and_direction_and_angle_at(
                e.length - .001
            )
            v_dir_ortho_right = np.array([v_dir[1], -v_dir[0]])
            pos += (
                poi_priority_signs_offset_from_lane_center
                * v_dir_ortho_right
            )

            properties = all_properties[sign_type].copy()
            properties.update({
                'x': str(pos[0]),
                'y': str(pos[1]),
                'angle': f'{angle_deg - 90}',
                'id': f'streetSign_{sign_type}_{e}'
            })
            poi_generator.add_poi(properties)


def create_pois_end_of_level(
        poi_generator: PoiGenerator,
        poi_end_of_level_end_of_lane_offset: float,
        poi_end_of_level_lateral_offset: float,
        poi_end_of_level_id_generator: Callable[
            [int, Level, int, int, AbstractEgoRouteLane], str
        ] = None,
        **kwargs
):
    """
    POIs for marking the ends of levels.

    """
    ego_route = poi_generator.ego_route
    assert isinstance(ego_route, LevelEgoRoute)

    for level_i, level, lane_i_in_level, route_elem_index, route_lane in (
            ego_route.level_route_iterator()
    ):
        if level_i is None:
            break  # no more levels
        if lane_i_in_level != level.num_edges - 1:
            # TODO: make sure there's no off-by-one error here
            continue  # not the end of a level
        eh = ego_route.get_edge_helper(route_elem_index)
        coord, v_dir, angle_deg = eh.get_cartesian_and_direction_and_angle_at(
            eh.length - poi_end_of_level_end_of_lane_offset)
        v_dir_ortho_right = np.array([v_dir[1], -v_dir[0]])
        coord += poi_end_of_level_lateral_offset * v_dir_ortho_right

        if poi_end_of_level_id_generator is not None:
            poi_id = poi_end_of_level_id_generator(
                level_i,
                level,
                lane_i_in_level,
                route_elem_index,
                route_lane
            )
        else:
            # Default if not doing a TOJ experiment where the format should
            # instead be
            # f'endOfLevel_{level_i}/{len(ego_route.levels)}_{num_trials}trials_{level.difficulty}'.
            # (See implementation of the EndOfLevelHandler in our Unity
            # project.)
            poi_id = (
                f'endOfLevel_{level_i}/'
                f'{len(ego_route.levels)}_{level.difficulty}'
            )

        properties = END_OF_LEVEL_POI.copy()
        properties.update({
            'id': poi_id,
            'x': f'{coord[0]}',
            'y': f'{coord[1]}',
            'angle': f'{angle_deg}'
        })
        poi_generator.add_poi(properties)


def create_pois_tutorial_banners(
        poi_generator: PoiGenerator,
        **kwargs
):
    """
    Generate points of interest for tutorial banners.
    Requires that there are some levels defined in the PoiGenerator's
    (Level)EgoRoute
    which contain TutorialInstructions.

    :param poi_generator:
    :param kwargs:
    :return:
    """
    ego_route = poi_generator.ego_route
    assert isinstance(ego_route, LevelEgoRoute)

    instructions_by_level_by_lane_in_level = dict()
    for level_i, level in enumerate(ego_route.levels):
        instructions_by_level_by_lane_in_level[level_i] = dict()
        for instruction in level.tutorial_instructions:
            if (
                    instruction.lane_index_in_level
                    not in instructions_by_level_by_lane_in_level[level_i]
            ):
                instructions_by_level_by_lane_in_level[level_i][
                    instruction.lane_index_in_level
                ] = []
            instructions_by_level_by_lane_in_level[level_i][
                instruction.lane_index_in_level
            ].append(instruction)

    for level_i, level, lane_i_in_level, route_elem_index, route_lane in (
            ego_route.level_route_iterator()
    ):
        if level_i is None:
            break  # no more levels
        if (
                lane_i_in_level
                not in instructions_by_level_by_lane_in_level[level_i]
        ):
            continue
        instructions: List[TutorialInstruction] = (
            instructions_by_level_by_lane_in_level[level_i][lane_i_in_level]
        )
        for instruction in instructions:
            eh = ego_route.get_edge_helper(route_elem_index)
            pos = (
                eh.length - instruction.offset_from_edge_end
                if instruction.offset_from_edge_start is None
                else instruction.offset_from_edge_start
            )
            coord, v_dir, angle_deg = (
                eh.get_cartesian_and_direction_and_angle_at(pos)
            )
            v_dir_ortho_right = np.array([v_dir[1], -v_dir[0]])
            coord += instruction.lateral_offset * v_dir_ortho_right

            properties = TUTORIAL_POI.copy()
            properties.update({
                'id': (
                    f'Tutorial_Step-{instruction.step}'
                    if instruction.step is not None
                    else f'Tutorial_{instruction.message}'
                    # BEWARE: this is not yet implemented to be parsed in Unity
                ),
                'x': f'{coord[0]}',
                'y': f'{coord[1]}',
                'angle': f'{angle_deg}'
            })
            poi_generator.add_poi(properties)
