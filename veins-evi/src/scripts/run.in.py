#!/usr/bin/env python3

# ^-- contents of out/config.py go here

"""
Runs Veins simulation in current directory
"""

import os
import argparse
import subprocess


def relpath(s):
    veins_root = os.path.dirname(os.path.realpath(__file__))
    return os.path.relpath(os.path.join(veins_root, s), '.')


parser = argparse.ArgumentParser('Run a Veins simulation')
parser.add_argument(
    '-d',
    '--debug',
    action='store_true',
    help='Run using opp_run_dbg (instead of opp_run)'
)
parser.add_argument(
    '-t',
    '--tool',
    metavar='TOOL',
    dest='tool',
    choices=['lldb', 'gdb', 'memcheck'],
    help='Wrap opp_run execution in TOOL (lldb, gdb or memcheck)'
)
parser.add_argument(
    '-v',
    '--verbose',
    action='store_true',
    help='Print command line before executing'
)
parser.add_argument(
    '--',
    dest='arguments',
    help='Arguments to pass to opp_run'
)
args, omnet_args = parser.parse_known_args()
if (len(omnet_args) > 0) and omnet_args[0] == '--':
    omnet_args = omnet_args[1:]

# Assembled from variables defined in out/config.py:
run_libs = [relpath(s) for s in run_libs]  # noqa: F821
run_neds = [relpath(s) for s in run_neds] + ['.']  # noqa: F821
run_imgs = [relpath(s) for s in run_imgs]  # noqa: F821

opp_run = 'opp_run'
if args.debug:
    opp_run = 'opp_run_dbg'

lib_flags = [f"-l{s}" for s in run_libs]
ned_flags = ['-n' + ';'.join(run_neds)]
img_flags = ['--image-path=' + ';'.join(run_imgs)]

prefix = []
if args.tool == 'lldb':
    prefix = ['lldb', '--']
if args.tool == 'gdb':
    prefix = ['gdb', '--args']
if args.tool == 'memcheck':
    prefix = [
        'valgrind',
        '--tool=memcheck',
        '--leak-check=full',
        '--dsymutil=yes',
        '--log-file=valgrind.out'
    ]

cmdline = prefix + [opp_run] + lib_flags + ned_flags + img_flags + omnet_args

if args.verbose:

    print(
        "Running with command line arguments: "
        + {' '.join([f'"{arg}"' for arg in cmdline])}
    )

if os.name == 'nt':
    subprocess.call(['env'] + cmdline)
else:
    os.execvp('env', ['env'] + cmdline)
