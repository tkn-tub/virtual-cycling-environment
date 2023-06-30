"""
Common configuration options for the Ego Vehicle Interface.
"""

DEFAULT_EVI_PORT = 12346
MAX_MSG_SIZE = 1500
DEFAULT_SUMO_OPTS = [
    "--no-step-log",
    "--no-duration-log",
    "--start",
    "--quit-on-end",
    "--xml-validation.net",
    "never",
    "--xml-validation",
    "never",
]

DEFAULTS = {
    "evi_port": DEFAULT_EVI_PORT,
    "rt_simulator": "ASM",
    "rt_max_vehicles": "None",
    "rt_fellow_filter": "statically_distributed",
    "rt_override_remote_port": -1,
    "rt_override_remote_host": "",
    "sumo_port": 8813,
    "sumo_host": "127.0.0.1",
    "sumo_binary": "sumo",
    "sumo_timing_csv": None,
    "sumo_keep_route": 1,
    "veins_port": 12347,
    "sync_interval_ms": 100,
    "veins_max_vehicles": "None",
    "veins_fellow_filter": "statically_distributed",
    "verbosity": "WARNING",
    "ego_ids": ["ego-0"],
    "ego_type": "ego-type",
    "ego_route_name": "ego-route",
    "start_time": 0,
    "veins_config_name": "LanradioDisabled",
    "veins_scenario_dir": "./veins",
    "veins_runnr": 0,
}
