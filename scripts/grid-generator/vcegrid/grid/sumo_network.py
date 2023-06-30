from typing import Optional

import subprocess
import os

# import xml.etree.ElementTree as ET

# Use lxml's etree instead of xml.etree.ElementTree because the latter doesn't
# write line breaks
# (API is practically the same):
from lxml import etree as ET

from ..sumo_network import SUMO_XML_SETTINGS


def generate_grid_net(
        sumo_net_filename='grid.net.xml',
        grid_num_junctions_x=15,
        grid_num_junctions_y=15,
        grid_street_len_x=25,
        grid_street_len_y=25,
        grid_attach_len=100,
        lane_width=3.2,
        sumo_version='1.0.1',
        netgenerate_cmd='netgenerate',
        grid_default_speed=9,  # in m/s; 9 m/s = 32.4 km/h
        grid_default_lane_number=1,
        grid_no_turnarounds=True,
        # netgenerate default: 'priority':
        grid_default_junction_type='right_before_left',
        grid_default_junction_radius=1,
        grid_junctions_small_radius=0,
        grid_junctions_internal_link_detail: int = 12,
        grid_junctions_corner_detail: int = 5,
        # max. lateral acceleration in m/s^2:
        grid_junctions_limit_turn_speed: Optional[float] = None,
        **kwargs
):
    netgenerate_args = [
        netgenerate_cmd,
        '-o', sumo_net_filename,
        # '--no-warnings',  # TODO: make configurable
        '--grid',
        '--alphanumerical-ids',
        '--grid.x-number', str(grid_num_junctions_x),
        '--grid.y-number', str(grid_num_junctions_y),
        '--grid.x-length', str(grid_street_len_x),
        '--grid.y-length', str(grid_street_len_y),
        '--grid.attach-length', str(grid_attach_len),
        '--default.lanewidth', str(lane_width),
        '--default.speed', str(grid_default_speed),
        '--default.lanenumber', str(grid_default_lane_number),
        *(
            [
                '--default.junctions.radius',
                str(grid_default_junction_radius),
                '--junctions.small-radius', str(grid_junctions_small_radius),
                '--junctions.corner-detail', str(grid_junctions_corner_detail),
                *(
                    [
                        '--junctions.limit-turn-speed',
                        str(grid_junctions_limit_turn_speed)
                    ]
                    if grid_junctions_limit_turn_speed is not None else []
                ),
            ]
            if not sumo_version.startswith('0.') else []
            # TODO: verify that the above options really are only available
            #  for SUMO v1+
        ),
        '--junctions.internal-link-detail',
        str(grid_junctions_internal_link_detail),
        '--no-turnarounds' if grid_no_turnarounds else '',
        '--default-junction-type', str(grid_default_junction_type),
    ]
    print(f"Running netgenerate as:\n{' '.join(netgenerate_args)}\n")
    subprocess.run(
        args=netgenerate_args
    )


def generate_grid_buildings_simple(
        sumo_poly_filename='grid.poly.xml',
        grid_street_margin=0,
        grid_building_margin=6,
        grid_num_junctions_x=15,
        grid_num_junctions_y=15,
        grid_street_len_x=25,
        grid_street_len_y=25,
        grid_attach_len=100,
        **kwargs
):
    """
    This simple approach assumes the network was generated as a grid using
    netgenerate.
    In the future, this could project the network onto a texture to obtain
    road-free areas, read user-defined textures for guiding the type of
    buildings (suburban, urban, office buildings etc.),
    use blender and shape grammars to generate fancy 3D models from building
    outlines, …

    :param sumo_poly_filename:
    :param grid_street_margin: Constant offset determined by the offset of the
        first streets from (0, 0) (?).
        If you want symmetry and your streets have only two lanes,
        set this to 0.
    :param grid_building_margin:
    :param grid_num_junctions_x:
    :param grid_num_junctions_y:
    :param grid_street_len_x:
    :param grid_street_len_y:
    :param grid_attach_len:
    :param kwargs:
    :return:
    """
    if os.path.exists(sumo_poly_filename):
        additionals_xml_root = ET.parse(sumo_poly_filename).getroot()
    else:
        # Create new ElementTree to later store as XML:
        additionals_xml_root = ET.Element('additionals')
    additionals_xml_tree = ET.ElementTree(additionals_xml_root)

    building_count = 0
    for y_block in range(grid_num_junctions_y - 1):
        # y_block is the index of the current rectangular street block in
        # y-direction.
        for x_block in range(grid_num_junctions_x - 1):
            p1 = (
                x_block * grid_street_len_x + grid_street_margin
                + grid_building_margin + grid_attach_len,
                y_block * grid_street_len_y + grid_street_margin
                + grid_building_margin + grid_attach_len
            )
            p2 = (
                p1[0],
                (y_block + 1) * grid_street_len_y
                + grid_street_margin - grid_building_margin + grid_attach_len
            )
            p3 = (
                (x_block + 1) * grid_street_len_x
                + grid_street_margin - grid_building_margin + grid_attach_len,
                p2[1]
            )
            p4 = (
                p3[0],
                p1[1]
            )
            verts = [p1, p2, p3, p4]

            new_poly = ET.SubElement(additionals_xml_root, 'poly')
            new_poly.set('id', str(building_count))
            new_poly.set('type', 'building')
            new_poly.set('color', '0.7,0.3,0.1')
            new_poly.set('fill', '1')
            new_poly.set('layer', '4')
            new_poly.set(
                'shape',
                ' '.join([','.join([str(c) for c in v]) for v in verts])
            )  # e.g. "0,0 1,0 1,1 0,1"

            building_count += 1

    additionals_xml_tree.write(sumo_poly_filename, **SUMO_XML_SETTINGS)
