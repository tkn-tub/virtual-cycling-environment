# Overview

An Ego Vehicle Interface for real-time communication between Sumo, Veins and a real-time simulator.

# Installation

## Requirements

To run `python-evi`, you will need at least

- python 3.8+ (we test with 3.7 and 3.8)
- the python `venv` module (may need an extra package, e.g. on Debian)
- Sumo 1.1+
- The spatialindex library

*Note:*
Sumo is only needed at runtime and not necessarily on the same machine.
By default `python-evi` will start sumo for you.
But you can also start it in advance (maybe on another host) and point `evid.py` to it.

## Quick Dev Installation using venv

Simply run the following script to install `python-evi` in development mode and all dependencies into a venv:

```bash
./setup-evi.sh
```

Then source the virtual environment like so (also available for *fish* and *zsh*):

```bash
source .venv/bin/activate
```

## Detailed Installation Instructions

For `python-evi` to run, you need a number of dependencies installed.
Some of these dependencies are not (yet) available from the official pypi.
But `python-evi` comes with a `pyproject.toml` and `poetry.lock` file that can install all dependencies using `poetry`.
Make sure you have `poetry` installed and run:

```bash
poetry install
```

This also installs evi in development mode.

It is up to you where you want to install this.
By default, `poetry` will create a virtual environment for you, but you could also install it into your system directory.

For development there are useful packages available by default.
If you do not need them, use `poetry install --no-dev` instead.

When using `poetry` for installation, either run `poetry shell` afterwards to enter the virtualenv.
Or prepend all script calls with `poetry run`, e.g.: `poetry run scripts/evid.py -h`.

# Running

To run `python-evi`, you need a configuration file for your scenario.
A number of pre-defined scenarios are bundled with `python-evi` in the `networks` directory.
We recommended: *paderborn-north* for usage with the Unity3D visualization and *paderborn-hynets* for running with ASM.

Run `python-evi` starting the `scripts/evid.py` file.
Supply the configuration file and any other options you want to set.
Configuration options can be given int the configuration file or ad-hoc on the command line (overriding configuration
file settings).
For a list of available settings, run `scripts/evid.py --help`.

For example:

```bash
scripts/evid.py --config-file networks/paderborn-hynets/paderborn-hynets.evi.ini --verbosity INFO
```

## ASM PCAP Replay

To emulate a running instance of ASM, you can replay a recorded trace of messages:

```bash
scripts/pcapreplay.py --csv-infile networks/paderborn-hynets/reference-traces/asm.csv.bz2 --replay --interactive
```

Then press enter to send the next message.

The `--period <period-in-seconds>` option can be used instead of the `--interactive` option.
This will send messages automatically with the given period in between.

# Citing

If you are working with `python-evi` please cite (at least one of) the following papers:

> Dominik S. Buse and Falko Dressler, "Towards Real-Time Interactive V2X Simulation," Proceedings of 11th IEEE Vehicular Networking Conference (VNC 2019), Los Angeles, CA, December 2019, pp. 114–121.

```bibtex
@inproceedings{buse2019towards,
author = {Buse, Dominik S. and Dressler, Falko},
doi = {10.1109/VNC48660.2019.9062812},
title = {{Towards Real-Time Interactive V2X Simulation}},
pages = {114--121},
publisher = {IEEE},
issn = {2157-9865},
isbn = {978-1-7281-4571-6},
address = {Los Angeles, CA},
booktitle = {11th IEEE Vehicular Networking Conference (VNC 2019)},
month = {12},
year = {2019},
}
```

> Dominik S. Buse, Max Schettler, Nils Kothe, Peter Reinold, Christoph Sommer and Falko Dressler, "Bridging Worlds: Integrating Hardware-in-the-Loop Testing with Large-Scale VANET Simulation," Proceedings of 14th IEEE/IFIP Conference on Wireless On demand Network Systems and Services (WONS 2018), Isola 2000, France, February 2018, 

```bibtex
@inproceedings{buse2018bridging,
author = {Buse, Dominik S. and Schettler, Max and Kothe, Nils and Reinold, Peter and Sommer, Christoph and Dressler, Falko},
doi = {10.23919/WONS.2018.8311659},
title = {{Bridging Worlds: Integrating Hardware-in-the-Loop Testing with Large-Scale VANET Simulation}},
pages = {33--36},
publisher = {IEEE},
address = {Isola 2000, France},
booktitle = {14th IEEE/IFIP Conference on Wireless On demand Network Systems and Services (WONS 2018)},
month = {2},
year = {2018},
}
```

# Development and Testing

To run the all tests run:

```bash
tox
```

This may take a while, as all tests including the long-running integrationtests are performed.
To only run the faster (pure-python) unit tests, run:
```bash
tox -e py37
```

Note, to combine the coverage data from all the tox environments run:

```bash
PYTEST_ADDOPTS=--cov-append tox
```

## Update Docs

Whenever you add, remove, or rename a module (or package), re-generate the stubs for sphinx:

```bash
tox -e docs
source .tox/docs/bin/activate
cd docs
sphinx-apidoc -o reference/ ../src/evi
tox -e docs
```

Commit the updated `.rst` files in the `docs` dir (not `dist/docs` though!).
