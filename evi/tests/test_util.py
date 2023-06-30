import pytest  # noqa

from evi.util import (
    edge_lane_nr_to_lane_id,
    lane_to_edge,
    lane_to_nr,
    make_edge_to_lane_map,
    make_uint_mapping,
)


def test_edge_lane_nr_to_lane_id():
    assert edge_lane_nr_to_lane_id('edgename', 0) == 'edgename_0'
    assert edge_lane_nr_to_lane_id('edgename', 1) == 'edgename_1'


def test_lane_to_edge():
    assert lane_to_edge('edgename_0') == 'edgename'
    assert lane_to_edge('edgename_1') == 'edgename'
    assert lane_to_edge('crazy_edge_name_55') == 'crazy_edge_name'
    assert lane_to_edge(':internaledgename_0') == ':internaledgename'


def test_lane_to_nr():
    assert lane_to_nr('edgename_0') == 0
    assert lane_to_nr('edgename_1') == 1
    assert lane_to_nr('crazy_edge_name_55') == 55
    assert lane_to_nr(':internaledgename_0') == 0


def test_make_edge_to_lane_map():
    assert make_edge_to_lane_map([]) == dict()
    assert make_edge_to_lane_map(['edge_0']) == {'edge': ['edge_0']}
    assert make_edge_to_lane_map(['edge_0', 'edge_1']) == {'edge': ['edge_0', 'edge_1']}
    assert make_edge_to_lane_map(['edge_0', 'edgeb_1']) == {'edge': ['edge_0'], 'edgeb': ['edgeb_1']}


class TestUIntMapping():

    def test_empty_sequence(self):
        fw, bw = make_uint_mapping([])
        assert fw == {}
        assert bw == {}

    def test_single_entry(self):
        mystr = 'teststring'
        fw, bw = make_uint_mapping([mystr])
        assert len(fw) == 1
        assert len(bw) == 1
        assert mystr in fw
        assert fw[mystr] in bw
        assert fw[mystr] < 2**32
