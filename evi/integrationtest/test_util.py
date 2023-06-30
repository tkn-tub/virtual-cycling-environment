"""
Test of utility functions that requre external data.
"""

from evi.util import extract_projection_data


def test_projection_data_extraction_on_paderborn_hynets():
    projection_params, offset = extract_projection_data(
        "networks/paderborn-hynets/paderborn-hynets.net.xml"
    )
    assert (
        projection_params
        == "+proj=utm +zone=32 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    )
    assert offset[0] == -474821.76
    assert offset[1] == -5723127.5
