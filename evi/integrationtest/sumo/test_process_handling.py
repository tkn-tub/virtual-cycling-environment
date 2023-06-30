"""
sumo process handling tests

check if sumo and traci are installed and working as expeceted.
"""

import asyncio
import subprocess as sp

import pytest

from evi.util import launch_sumo


def test_sumo_available():
    assert sp.call(['sumo', '--version']) == 0


@pytest.mark.asyncio
async def test_sumo_launched(traci_connection):
    # check initial state
    assert traci_connection.simulation.getCurrentTime() == 0
