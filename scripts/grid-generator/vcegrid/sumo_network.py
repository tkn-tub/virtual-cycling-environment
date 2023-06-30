import yaml
from sumolib.net import readNet
from .route.abstract_ego_route import AbstractEgoRoute
import evi

# import xml.etree.ElementTree as ET

# Use lxml's etree instead of xml.etree.ElementTree because the latter doesn't
# write line breaks
# (API is practically the same):
from lxml import etree as ET


SUMO_XML_SETTINGS = {
    'encoding': 'iso-8859-1',
    'xml_declaration': True,
    'pretty_print': True
}


def initialize_routes_file(
        filename,
        route: AbstractEgoRoute,
        ego_vehicle_is_bicycle=True,
        sumo_use_sublane_model: bool = True,
        **kwargs
):
    """
    Just add the bare minimum to a new routes file with the given filename,
    i.e. the vehicle types for "ego-type" and "default" and a dummy route for
    the ego vehicle.
    """
    rou_root = ET.Element('routes')
    rou_xml_tree = ET.ElementTree(rou_root)

    vtype_ego = ET.SubElement(rou_root, 'vType')
    vtype_ego.set('id', 'ego-type')
    vtype_ego.set('sigma', '0.5')
    vtype_ego.set('length', '1.75' if ego_vehicle_is_bicycle else '3.5')
    # ^ realistic?
    vtype_ego.set('minGap', '2.5')
    vtype_ego.set('color', '1,0,0')

    ego_route_edges = [
        evi.util.lane_to_edge(lane.lane_id)
        for lane in route.lanes
    ]

    # Even though we set keep_route to 2 (meaning 'no'),
    # EVI still expects an ego-route to be set with a valid list of edges.
    route_ego = ET.SubElement(rou_root, 'route')
    route_ego.set('id', 'ego-route')
    route_ego.set('edges', ' '.join(ego_route_edges))

    default_vehicle_settings = {
        'vClass': 'passenger',
        'color': '0.1,0.6,1.0',
        'length': '5.0',  # length in meters (default: 5)
        'width': '1.8',  # width in meters (default: 1.8)
    }
    if sumo_use_sublane_model:
        # Enable SUMO's sublane model by setting an appropriate lane change
        # model.
        # If there's enough room on an edge, this should allow other cars to
        # overtake the ego vehicle (assuming the latter is a bicycle),
        # as well as cars that are stopped at the side of the road.
        # (The latter is supposed to be an alternative to parking because SUMO
        # doesn't animate actual parking.)
        # http://www.sumo.dlr.de/userdoc/Definition_of_Vehicles,_Vehicle_Types,_and_Routes.html#Lane-Changing_Models
        default_vehicle_settings.update({
            'laneChangeModel': 'SL2015',
            'lcKeepRight': '1.0',
            # ^ "The eagerness for following the obligation
            #  to keep right.", [0,inf[
            'latAlignment': 'center'
            # ^ "prefered [sic] lateral alignment within a lane."
        })

    vtype_default = ET.SubElement(rou_root, 'vType')
    vtype_default.set('id', 'default')
    for key, value in default_vehicle_settings.items():
        vtype_default.set(key, value)

    vtype_parking = ET.SubElement(rou_root, 'vType')
    vtype_parking.set('id', 'parker')
    parking_vehicle_settings = default_vehicle_settings.copy()
    # Make only this car keep on the right side of the lane so only it can be
    # overtaken:
    parking_vehicle_settings['latAlignment'] = 'right'
    for key, value in parking_vehicle_settings.items():
        vtype_parking.set(key, value)

    rou_xml_tree.write(filename, **SUMO_XML_SETTINGS)


def write_sumo_configuration(
        filename,
        sumo_remote_port=None,
        sumo_net_filename='grid.net.xml',
        sumo_poly_filename='grid.poly.xml',
        sumo_rou_filename='grid.rou.xml',
        sumo_use_sublane_model=True,
        sumo_sublane_lateral_resolution=.8,
        sumo_step_length=.1,
        **kwargs
):
    cfg_root = ET.Element('configuration')
    cfg_xml_tree = ET.ElementTree(cfg_root)

    cfg_input = ET.SubElement(cfg_root, 'input')
    ET.SubElement(cfg_input, 'net-file').set('value', sumo_net_filename)
    ET.SubElement(cfg_input, 'additional-files').set(
        'value',
        sumo_poly_filename
    )
    ET.SubElement(cfg_input, 'route-files').set('value', sumo_rou_filename)
    if sumo_use_sublane_model:
        ET.SubElement(cfg_input, 'lateral-resolution').set(
            'value',
            str(sumo_sublane_lateral_resolution)
        )
    if sumo_remote_port is not None:
        ET.SubElement(cfg_input, 'remote-port').set(
            'value',
            str(sumo_remote_port)
        )

    cfg_time = ET.SubElement(cfg_root, 'time')
    ET.SubElement(cfg_time, 'begin').set('value', '0')
    ET.SubElement(cfg_time, 'end').set('value', '10000')
    # ^ doesn't matter w/ EVI (b/c of TraCI?)
    ET.SubElement(cfg_time, 'step-length').set('value', f'{sumo_step_length}')

    cfg_xml_tree.write(filename, **SUMO_XML_SETTINGS)


# TODO: this file is called sumo_network.py, but the function is for EVI
#  configs
def write_evi_configuration(
        filename,
        remote_sumo=False,
        evi_sync_interval_ms: int = 100,
        sumo_cfg_filename='grid.sumo.cfg',
        sumo_net_filename='grid.net.xml',
        evi_sumo_keep_route: int = 0,
        triggers_filename: str = None,
        **kwargs
):
    with open(filename, 'w') as f:
        f.write('[evi]\n')
        f.write(
            'sumo_config_file = '
            f'{sumo_cfg_filename if not remote_sumo else ""}\n'
        )  # TODO: fix this in EVI?
        f.write(f'sumo_network_file = {sumo_net_filename}\n')
        f.write('sumo_egoroute_file =\n')
        # ^ usually empty for virtual cycling environment
        f.write('neighborhood_radius = 150\n')
        f.write('steps =\n')  # usually empty
        f.write(f'sync_interval_ms = {evi_sync_interval_ms:.0f}\n')
        f.write(f'sumo_keep_route = {evi_sumo_keep_route}\n')
        # ^ allow ego vehicle (bicycle) to leave lanes
        if remote_sumo:
            f.write('sumo_host = localhost\n')
            f.write('sumo_port = 8813\n')
        f.write('rt_simulator = Unity\n')
        f.write('unity_port = 12346\n')
        if triggers_filename is not None:
            f.write(f'dynamic_spawn_points_file = {triggers_filename}\n')

        f.write('\n')

        f.write('[ego_vehicle]\n')
        f.write('ego_id = ego-vehicle\n')
        f.write('ego_type = ego-type\n')
        f.write('ego_route_name = ego-route\n')
        f.write('ego_route_edges =\n')  # usually empty
        f.write('ego_route_trafficlights =\n')  # usually empty
        f.write('ego_ensure_subscription = False\n')
        # f.write('\n')
        # One newline at the end of a file is enough.
        # This would add a second one.


def generate_parking_areas_along_toj_route(
        net_file_out,
        toj_route_file,
        parking_margin_fraction=.1,
        parking_roadside_capacity=2,
        parking_angle_deg=20,
        parking_spot_length=7,
        **kwargs
):
    """
    This will create parking areas off the actual roads.
    http://www.sumo.dlr.de/userdoc/Simulation/ParkingArea.html

    Currently not in use because SUMO doesn't animate the transition from roads
    to parking areas (vehicles are teleported).

    :param parking_angle_deg:
    :param parking_spot_length:
    :param parking_roadside_capacity:
    :param net_file_out: file must exist
    :param toj_route_file: file must exist
    :param parking_margin_fraction: fraction of edge where parking areas are
        supposed to begin/end
    :param kwargs:
    :return:
    """
    net = readNet(net_file_out)

    parser = ET.XMLParser(remove_blank_text=True)
    net_root = ET.parse(net_file_out, parser).getroot()
    net_tree = ET.ElementTree(net_root)

    with open(toj_route_file, 'r') as f:
        route = yaml.load(f)

    for lane_dict in route:
        lane_id_name = list(lane_dict.keys())[0]
        edge_id_name = lane_id_name.split('_')[0]

        net_lane = net.getLane(lane_id_name)
        lane_length = net_lane.getLength()

        new_parking = ET.SubElement(net_root, 'parkingArea')
        new_parking.set('id', 'parking_' + edge_id_name)
        new_parking.set('lane', lane_id_name)
        new_parking.set('startPos', str(parking_margin_fraction * lane_length))
        new_parking.set(
            'endPos',
            str((1 - parking_margin_fraction) * lane_length)
        )
        new_parking.set('roadsideCapacity', str(parking_roadside_capacity))
        new_parking.set('angle', str(parking_angle_deg))
        new_parking.set('length', str(parking_spot_length))
        # alternatively specify parking <space> elems individually?

        # TODO: stops in routes or vehicles…
        # TODO: use with argparse and in main()

    net_tree.write(net_file_out, **SUMO_XML_SETTINGS)

