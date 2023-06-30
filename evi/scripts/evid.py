#!/usr/bin/env python3
"""
Runs the ego vehicle interface.
"""
import argparse
import asyncio
import collections
import configparser
import logging
import logging.handlers
import os
import queue
import signal

from evi.asm import ASMCodec, ASMProtocol
from evi.defaultconfig import DEFAULT_SUMO_OPTS, DEFAULTS
from evi.filtering import FELLOW_FILTERS
from evi.request_handlers import (
    EgoVehicleUpdateHandler,
    HorizonEgoTrafficLightHandler,
    RequestDispatcher,
    UnityEgoVehicleUpdateHandler,
)
from evi.sumo import SumoInterface
from evi.unity import UnityProtocol
from evi.util import (
    ID_MAPPER,
    TRACER,
    extract_projection_data,
    flex_open,
    kill_subproc_after,
    launch_sumo,
    launch_veins,
    make_event_setting_handler,
    make_geo_mapper,
)
from evi.veins import VeinsInterface

LOG = logging.getLogger(__name__)


def logging_parser(defaults):
    """Return parser configuration for logging and tracing."""
    parser = argparse.ArgumentParser(add_help=False)
    logging_group = parser.add_argument_group("Logging/Tracing")
    logging_group.add_argument(
        "--logfile",
        help="File name to write EVI text log to (instead of stdout).",
    )
    logging_group.add_argument(
        "--event-trace-file",
        help="File name to write chrome-style event trace to.",
    )
    logging_group.add_argument(
        "--protocol-trace-file",
        help="File name to write all network protocol traces to.",
    )
    logging_group.add_argument(
        "--vehicle-trace-file",
        help="File name to write (ego) vehicle state traces to.",
    )
    logging_group.add_argument(
        "--verbosity",
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR"],
        default=defaults["verbosity"],
        help="Set loging level/verbosity (default: {}).".format(
            defaults["verbosity"]
        ),
    )
    return parser


def evid_parser(rt_interfaces, defaults):
    """Return parser configuration for the EVI daemon script."""
    parser = argparse.ArgumentParser(add_help=False)
    evid_group = parser.add_argument_group("EVI Daemon")
    evid_group.add_argument(
        "--ego-ids",
        type=lambda string: list(string.split(",")),
        help="String IDs of the ego-vehicles in SUMO (default: {}).".format(
            defaults["ego_ids"]
        ),
    )
    evid_group.add_argument(
        "--start-time",
        type=int,
        default=defaults["start_time"],
        help="Maneuver start time in milliseconds (default: {}ms).".format(
            defaults["start_time"]
        ),
    )
    evid_group.add_argument(
        "--sumo-config-file",
        help="Start own instance of SUMO using the given config file.",
    )
    evid_group.add_argument(
        "--sumo-binary",
        default=defaults["sumo_binary"],
        help="Path to the sumo binary (default: {}).".format(
            defaults["sumo_binary"]
        ),
    )
    evid_group.add_argument(
        "--sumo-network-file", help="Network xml file as read by SUMO."
    )
    evid_group.add_argument(
        "--sumo-seed", help="Seed for SUMO (default: SUMO default)"
    )
    evid_group.add_argument(
        "--veins-binary", help="Path to the veins binary or run script."
    )
    evid_group.add_argument(
        "--veins-scenario-dir",
        help=(
            "Path to the veins scenario dir containing the omnepp.ini file "
            "(relative to evi config file)."
        ),
    )
    evid_group.add_argument(
        "--veins-config-name",
        help="Configuration name in omnetpp.ini file to run in Veins.",
    )
    evid_group.add_argument(
        "--veins-runnr",
        type=int,
        help="Run number to use when spawning Veins (default: {}).".format(
            defaults["veins_runnr"]
        ),
    )
    evid_group.add_argument(
        "--veins-result-dir",
        help="Directory for Veins to write its results when spawning Veins.",
    )
    evid_group.add_argument(
        "--write-id-mapping-file",
        help="Dump the ID mapping at the end of the simulation to this file.",
    )
    evid_group.add_argument(
        "--disable-geo-mapper",
        action="store_true",
        help="Disable geometry mapping of x/y to lat/lon coordinates.",
    )
    rt_group = parser.add_argument_group("All Real-Time Interfaces")
    rt_group.add_argument(
        "--evi-port",
        help="Port that evid will listen on (default: {}).".format(
            defaults["evi_port"]
        ),
    )
    rt_group.add_argument(
        "--rt-simulator",
        choices=rt_interfaces,
        help="Real-time simulator to connect to (default: {}).".format(
            defaults["rt_simulator"]
        ),
    )
    rt_group.add_argument(
        "--rt-max-vehicles",
        type=lambda string: int(string) if string != "None" else None,
        help=(
            "Maximum number of fellow vehicles synced to the rt simulator "
            "(None means unlimited, (default: {}).".format(
                defaults["rt_max_vehicles"]
            )
        ),
    )
    rt_group.add_argument(
        "--rt-fellow-filter",
        choices=list(FELLOW_FILTERS.keys()),
        default=defaults["rt_fellow_filter"],
        help="Filter mechanism to select fellows for the rt simulator.",
    )
    rt_group.add_argument(
        "--register-from-update",
        action="store_true",
        help="Allow to convert update msgs to registration msgs.",
    )
    rt_group.add_argument(
        "--rt-override-remote-port",
        type=int,
        default=defaults["rt_override_remote_port"],
        help="Override port of remote real time interface, disabled at -1",
    )
    rt_group.add_argument(
        "--rt-override-remote-host",
        type=str,
        default=defaults.get("rt_override_remote_host", ""),
        help="Override host/ip of remote real time interface, disabled at ''",
    )
    return parser


def parse_args(rt_interfaces):
    """
    Build multi-stage command line and config parser, return parsed arguments.
    """
    # get config file name via command line
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_argument = conf_parser.add_argument(
        "--config-file",
        required=False,
        help="Config file for a scenario to run.",
    )
    conf_args, _ = conf_parser.parse_known_args()

    # prepare defaults
    program_defaults = {**DEFAULTS, **vars(conf_args)}
    # open and parse config file
    if conf_args.config_file:
        if not os.path.exists(conf_args.config_file):
            raise FileNotFoundError(
                "Config file {} not found".format(conf_args.config_file)
            )
        config = configparser.ConfigParser()
        config.read([conf_args.config_file])
        program_defaults = {
            **program_defaults,
            **config["evi"],
            **config["ego_vehicle"],
        }

    # read and apply environment variables
    env_prefix = "EVI_"
    env_vars = {
        k[len(env_prefix) :].lower(): v
        for k, v in os.environ.items()
        if k.startswith(env_prefix)
    }
    program_defaults.update(env_vars)

    defaults = {
        k: v for k, v in program_defaults.items() if v is not None and v != ""
    }
    parser = argparse.ArgumentParser(
        parents=[
            conf_parser,
            SumoInterface.get_parser(defaults=defaults),
            VeinsInterface.get_parser(defaults=defaults),
            logging_parser(defaults=defaults),
            evid_parser(rt_interfaces, defaults=defaults),
        ],
    )
    parser.set_defaults(**defaults)

    # general config
    # enable requirement later on to allow -h without giving a conf file
    conf_argument.required = True
    args = parser.parse_known_args()[0]
    return args


class LocalQueueHandler(logging.handlers.QueueHandler):
    """Version without need to prepare messages for IPC."""

    def emit(self, record):
        try:
            self.enqueue(record)
        except Exception:
            self.handleError(record)


def prepare_file_logger(
    logger_name, file_name=None, level="DEBUG", extra_headers=("message",)
):
    """
    Prepare a custom logger for runtime recording to csv files.
    """
    logger = logging.getLogger(logger_name)
    logger.propagate = False
    if not file_name:
        logger.addHandler(logging.NullHandler())
        return

    logger.setLevel(level)
    with flex_open(file_name, "wt") as output_file:
        output_file.write(
            "relativeTimeMs,module,debugLevel,callName,{}\n".format(
                ",".join(extra_headers)
            )
        )
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(relativeCreated).6f,%(name)s,%(levelname)s,%(message)s"
        )
    )
    log_queue = queue.Queue()
    queue_handler = LocalQueueHandler(log_queue)
    logger.addHandler(queue_handler)
    listener = logging.handlers.QueueListener(
        log_queue, file_handler, respect_handler_level=True
    )
    listener.start()


def setup_logging(args):
    """
    Setup and configure logging and tracing.
    """
    # general logging
    logging.basicConfig(level=args.verbosity, filename=args.logfile)
    logging.debug(
        "Configuration: {\n\t%s\n}",
        "\n\t".join("%s: %s" % (k, v) for k, v in sorted(vars(args).items())),
    )
    # protocol trace logging
    prepare_file_logger("proto", args.protocol_trace_file)
    # ego vehicle tracing
    prepare_file_logger(
        "trace",
        args.vehicle_trace_file,
        extra_headers=[
            "moduleSimTimeMs",
            "vehicleId",
            "laneId",
            "pos",
            "x",
            "y",
            "angle",
            "speed",
        ],
    )


def prepare_launch_configs(args):
    """
    Configure coroutines to launch coupled simulators.
    """
    to_launch = collections.OrderedDict()
    if args.sumo_config_file:
        sumo_config_file = os.path.join(
            os.path.dirname(args.config_file), args.sumo_config_file
        )
        to_launch["Sumo"] = launch_sumo(
            config=sumo_config_file,
            port=args.sumo_port,
            binary=args.sumo_binary,
            extra_opts=DEFAULT_SUMO_OPTS,
        )
        args.sumo_host = "127.0.0.1"

    if args.veins_binary and args.veins_scenario_dir:
        assert (
            args.veins_config_name is not None
        ), "No config name to run for Veins given."

        if os.path.isabs(args.veins_scenario_dir):
            veins_scenario_dir = args.veins_scenario_dir
        else:
            veins_scenario_dir = os.path.relpath(
                os.path.join(
                    os.path.dirname(args.config_file), args.veins_scenario_dir
                )
            )

        to_launch["Veins"] = launch_veins(
            config_name=args.veins_config_name,
            port=args.veins_port,
            binary=args.veins_binary,
            scenario_dir=veins_scenario_dir,
            runnr=args.veins_runnr,
            extra_opts=[
                "-u",
                "Cmdenv",
                *(
                    ("--result-dir", args.veins_result_dir)
                    if args.veins_result_dir
                    else []
                ),
            ],
        )
        args.veins_host = "127.0.0.1"
    return to_launch


async def simulate(parsed_args):
    """
    Set up and run the simulation.
    """

    # connect to sumo and retrieve scnario data
    sumo_interface = SumoInterface(**parsed_args)
    # connect to veins (if configured) and transfer scenario settings
    veins_interface = None
    if parsed_args.get("veins_host", None):
        veins_interface = VeinsInterface(**parsed_args)
        network_init_data = await sumo_interface.network_init_data()
        await veins_interface.init(
            parsed_args.get("start_time"), network_init_data
        )

    # advance to start time
    await sumo_interface.warm_up_traffic(parsed_args.get("start_time"))

    # set up server handler and protocol
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    # TODO: refactor
    if parsed_args["rt_simulator"] == "ASM":
        handlers = [
            EgoVehicleUpdateHandler(
                sumo_interface, veins_interface, shutdown_event, **parsed_args
            ),
            HorizonEgoTrafficLightHandler(
                sumo_network_file=os.path.join(
                    os.path.dirname(parsed_args["config_file"]),
                    parsed_args["sumo_network_file"],
                ),
                sumo_interface=sumo_interface,
            ),
        ]
        dispatcher = RequestDispatcher(handlers, shutdown_event)
        _transport, _protocol = await loop.create_datagram_endpoint(
            lambda: ASMProtocol(
                ASMCodec(),
                dispatcher,
                shutdown_event,
                override_remote_port=parsed_args["rt_override_remote_port"],
                override_remote_host=parsed_args["rt_override_remote_host"],
            ),
            local_addr=("0.0.0.0", parsed_args.get("evi_port")),
        )
    elif parsed_args["rt_simulator"] == "Unity":
        handlers = [
            UnityEgoVehicleUpdateHandler(
                sumo_interface, veins_interface, shutdown_event, **parsed_args
            ),
        ]
        dispatcher = RequestDispatcher(handlers, shutdown_event)
        unity_protocol = UnityProtocol(
            dispatcher, shutdown_event, parsed_args.get("evi_port")
        )
        asyncio.create_task(unity_protocol.serve())

    # setup signals for graceful shutdown
    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig, make_event_setting_handler(sig, shutdown_event)
        )

    # let the server run
    LOG.info("Protocol set up, waiting for requests.")
    with TRACER.complete("serving"):
        await shutdown_event.wait()

    # shut down
    LOG.info("Shutting down EVI")
    teardowns = [sumo_interface.teardown()]
    if veins_interface:
        teardowns += [veins_interface.teardown()]
    with TRACER.complete("teardownInterfaces"):
        await asyncio.gather(*teardowns)


async def main():
    """
    Run Ego Vehicle Interface Daemon.
    """
    TRACER.instant("mainStart")

    # register available real time simulator interfaces
    rt_interfaces = ["ASM", "Unity"]

    args = parse_args(rt_interfaces)
    setup_logging(args)

    # prime id mapping with ego vehicle
    if args.rt_simulator == "ASM":
        # TODO: ensure reliable mapping between ego uint_ids and string_ids
        for ego_nr, ego_name in enumerate(sorted(args.ego_ids)):
            ID_MAPPER.force_add_mapping(string_id=ego_name, uint_id=ego_nr)
    elif args.rt_simulator == "Unity":
        ID_MAPPER.prime(args.ego_ids)  # prime with real id for Unity
    # prepare geo-projection mapper (lat/lon <-> x/y)
    geo_projection = None
    if not args.disable_geo_mapper:
        geo_projection = make_geo_mapper(
            *extract_projection_data(
                os.path.join(
                    os.path.dirname(args.config_file), args.sumo_network_file
                )
            )
        )
    setattr(args, "geo_projection", geo_projection)

    # collect simulator subprocesses to lanch before ynode itself
    to_launch = prepare_launch_configs(args)

    sim_subprocesses = dict()
    try:
        # launch simulator subprocesses
        with TRACER.complete("launcSubprocs"):
            sim_subproc_list = await asyncio.gather(
                *to_launch.values(), return_exceptions=True
            )
        sim_subprocesses.update(
            {
                proc: result
                for proc, result in zip(to_launch.keys(), sim_subproc_list)
                if not isinstance(result, BaseException)
            }
        )
        exceptions = [
            exc for exc in sim_subproc_list if isinstance(exc, Exception)
        ]
        if exceptions:
            raise exceptions[0]

        # run the simulation
        with TRACER.complete("simulate"):
            await simulate(parsed_args=vars(args))
    finally:
        # kill simulator subprocesses that did not stop by themselves
        with TRACER.complete("shutdownSubprocs"):
            shutdown_coros = [
                kill_subproc_after(sim_subproc, 1.0, name)
                for name, sim_subproc in sim_subprocesses.items()
            ]
            await asyncio.gather(*shutdown_coros)

    # write final data
    if args.write_id_mapping_file:
        with open(args.write_id_mapping_file, "w") as id_mapping_file:
            LOG.debug(
                "Writing final id mapping to %s", args.write_id_mapping_file
            )
            id_mapping_file.write(ID_MAPPER.dump_mapping())
    if TRACER.messages and args.event_trace_file:
        with flex_open(args.event_trace_file, "wt") as event_trace_file:
            num_traces = TRACER.write(event_trace_file, True)
            LOG.info("Wrote %d trace event messages.", num_traces)


if __name__ == "__main__":
    asyncio.run(main())
