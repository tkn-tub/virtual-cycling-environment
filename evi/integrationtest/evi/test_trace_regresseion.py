"""
test whole evi for regression against recorded traces.
"""

import asyncio
import csv
import glob
import os

import pytest

from evi.util import flex_open, launch_subproc

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# Fixtures


@pytest.fixture
def rti_port(unused_udp_port):
    """Get an free port for the RTI."""
    return unused_udp_port


@pytest.fixture
def scenario_dir():
    """Directory with all required scenario files."""
    return "networks/paderborn-hynets"


@pytest.fixture
def scenario_ini_file(scenario_dir):
    """Config file for evi."""
    ini_files = glob.glob("{}/*.evi.ini".format(scenario_dir))
    assert len(ini_files) == 1
    return ini_files[0]


@pytest.fixture
def ref_asm_trace(scenario_dir):
    return "{}/reference-traces/asm.csv.bz2".format(scenario_dir)


@pytest.fixture
def ref_protocol_trace(scenario_dir):
    return "{}/reference-traces/protocol.csv.bz2".format(scenario_dir)


@pytest.fixture
def ref_vehicle_trace(scenario_dir):
    return "{}/reference-traces/vehicle.csv.bz2".format(scenario_dir)


@pytest.fixture
def tmp_vehicle_trace(tmpdir):
    """File name for temporary vehicle trace file"""
    return "{}/vehicle.csv.bz2".format(tmpdir)


@pytest.fixture
def tmp_protocol_trace(tmpdir):
    """File name for temporary protocol trace file"""
    return "{}/protocol.csv.bz2".format(tmpdir)


@pytest.fixture
def pcap_replayer_config(rti_port, ref_asm_trace):
    return [
        'scripts/pcapreplay.py',
        '--csv-infile',
        ref_asm_trace,
        '--replay',
        '--period',
        '0.01',
        '--dport',
        str(rti_port),
    ]


@pytest.fixture
async def evid_instance(
        rti_port,
        tmp_vehicle_trace,
        tmp_protocol_trace,
        unused_sumo_port,
        scenario_ini_file
):
    """Start an evid instance ready for testing."""
    # start evi daemon (including sumo)
    evi_cmd = [
        'scripts/evid.py',
        '--config-file',
        scenario_ini_file,
        '--evi-port',
        str(rti_port),
        '--verbosity',
        'WARNING',
        '--sumo-port',
        str(unused_sumo_port),
    ]
    if tmp_protocol_trace is not None:
        evi_cmd += ['--protocol-trace-file', tmp_protocol_trace]
    if tmp_vehicle_trace is not None:
        evi_cmd += ['--vehicle-trace-file', tmp_vehicle_trace]
    evi_proc = await launch_subproc(evi_cmd, rti_port, 'udp', 'EVID', wait_times=400)
    try:
        yield evi_proc
    finally:
        if evi_proc.returncode is None:
            evi_proc.kill()
            await evi_proc.wait()  # so the loop will not be destroyed


@pytest.fixture
async def finished_regression_test(
        evid_instance,
        tmp_vehicle_trace,
        tmp_protocol_trace,
        pcap_replayer_config
):
    # run the pcap replayer
    replay_proc = await asyncio.create_subprocess_exec(*pcap_replayer_config)
    await replay_proc.wait()
    assert replay_proc.returncode == 0
    yield evid_instance


# Test helpers

def compare_result_files(ref_fname, cur_fname, fields, output_type):
    """Compare reference and current output file field-wise."""
    def parse_messages_from_result_file(fname):
        """Generate messages from a result file."""
        with flex_open(fname, 'rt') as csvfile:
            yield from csv.DictReader(csvfile)

    # get generators for reference and current outputs
    ref_gen = parse_messages_from_result_file(ref_fname)
    cur_gen = parse_messages_from_result_file(cur_fname)
    # combine and iterate over lines/messages
    for num, (ref, cur) in enumerate(zip(ref_gen, cur_gen)):
        # check for equality
        for field in fields:
            assert ref[field] == cur[field], (
                "Mismatch in field '{}' in line {} "
                "of filetype '{}': ref '{}' != cur '{}'".format(
                    field, num, output_type, ref[field], cur[field]
                )
            )
    # check for equal number of items (both generators exhausted)
    with pytest.raises(StopIteration):
        next(ref_gen)
    with pytest.raises(StopIteration):
        next(cur_gen)


# Tests

async def test_output_files_are_created(
        evid_instance,
        tmp_vehicle_trace,
        tmp_protocol_trace
):
    """Test that EVI creates output traces."""
    assert os.path.exists(str(tmp_protocol_trace))
    assert os.path.exists(str(tmp_vehicle_trace))


async def test_vehicle_trace_is_like_reference(
        finished_regression_test,
        tmp_vehicle_trace,
        ref_vehicle_trace,
):
    """Test that the vehicle output trace is like the reference trace."""
    compare_result_files(
        ref_vehicle_trace,
        tmp_vehicle_trace,
        [
            'module',
            'callName',
            'moduleSimTimeMs',
            'vehicleId',
            'laneId',
            'pos',
            'x',
            'y',
            'angle',
            'speed',
        ],
        'vehicle',
    )


async def test_protocol_trace_is_like_reference(
        finished_regression_test,
        tmp_vehicle_trace,
        tmp_protocol_trace,
        ref_vehicle_trace,
        ref_protocol_trace
):
    """Test that the protocol output trace is like the reference trace."""
    compare_result_files(
        ref_protocol_trace,
        tmp_protocol_trace,
        ['module', 'callName', 'message'],
        'protocol',
    )
