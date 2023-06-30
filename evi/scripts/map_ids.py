"""
Map sumo edge ids to evi hashed int ids for all edges in a network.

Write this mapping to a csv file.
"""

import argparse

from sumolib.net import readNet

from evi.util import to_uint

header = "#string_id\tuint_value\n"
tpl = "{}\t{}\n"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--road-mapping', '-r', default='road_id_mapping.csv')
    parser.add_argument('netfile')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    sumonet = readNet(args.netfile)
    edgemap = {e.getID(): to_uint(e.getID()) for e in sumonet.getEdges()}
    lines = [tpl.format(e_id, hash_int) for e_id, hash_int in edgemap.items()]
    lines = [header] + lines

    with open(args.road_mapping, 'w') as f:
        f.writelines(lines)
