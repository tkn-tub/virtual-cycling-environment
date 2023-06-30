Run-Time Configuration
======================

EVI supports multiple layers of ways to pass configuration options:

1. command line arguments
1. os environment variables
1. configuration (`.ini`) file contents
1. program (hard-coded) defaults

Settings made using a method higher in this list override settings made using lower ones.
E.g., environment variables override config file values and program defaults; command line arguments override everything else.

Naming of options is very similar across all options.
The reference format is the one used in configuration files and the code itself.
Option names are all lowercase and split with underscores (snake-case).
For command line arguments, prepend with `--` and convert separating underscores to dashes (`-`), this is symmetric to what `argparse` does.
For environment variables, convert to all uppercase and prepend `EVI_` (the prefix is removed (once) when parsing environment variables).
Examples:

- config/code: `evi_port`; command line arguments: `--evi-port`; environment variables: `EVI_EVI_PORT`
- config/code: `rt_max_vehicles`; command line arguments: `--rt-max-vehicles`; environment variables: `EVI_RT_MAX_VEHICLES`

Config files utilize the `.ini` file format.
Only the sections `[evi]` and `[ego_vehicle]` are considered.
Of the two, `[ego_vehicle]` is deprecated.

Internally, the values are parsed through the `argparse` module.
This allows consistent checking and type conversions.

To see all available configuration options, run `scripts/evid.py --help`.
Configuration options not known to the configuration parser are silently ignored.
When running `evid.py` with `--verbosity==DEBUG`, a table of final configuration options is logged on program startup.
