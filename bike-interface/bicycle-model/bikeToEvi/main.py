#!/usr/bin/env python3

from logging.handlers import SocketHandler
import logging
import time
import argparse

import bikesim
# import tacx  # import tacx later and only if required
import unity
from android import AndroidSensor
from irspeed import IRSpeedSensor
from irspeedesp32 import IRSpeedSensorEsp32


logger = logging.getLogger('main')
runners = []


class MyFilter(logging.Filter):
    def filter(self, record):
        allowed = [
            "main",
            "tacx",
            "main",
            "unity",
            "android",
            "irspeed",
            "irspeed_esp32",
        ]
        for prefix in allowed:
            if record.name.startswith(prefix):
                return 1

        return 0


def prepare_file_logger(
        logger_name,
        file_name=None,
        extra_headers=('key', 'value')
):
    """
    Prepare a custom logger for runtime recording to csv files.
    """
    new_logger = logging.getLogger(logger_name)
    new_logger.propagate = False
    if not file_name:
        new_logger.addHandler(logging.NullHandler())
        return

    new_logger.setLevel(0)
    with open(file_name, 'wt') as output_file:
        output_file.write(f'relativeTimeMs,module,{",".join(extra_headers)}\n')
    handler = logging.FileHandler(file_name)
    handler.setFormatter(
        logging.Formatter('%(relativeCreated).6f,%(name)s,%(message)s')
    )
    new_logger.addHandler(handler)


def main():
    """
    This just starts all the components in separate threads
    and then waits for a Ctrl+C or closing of the pygame window.
    Then it stops all the threads and terminates.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--logfile',
        default=None,
        help="Write log outputs to this file."
    )
    parser.add_argument(
        '--initial-orientation',
        type=float,
        help="Set an initial orientation clockwise in degrees matching "
             "that set for the bicycle's initial position in Unity. "
             "Consider this a temporary solution. (Ideally there should be "
             "a back channel at some point "
             "that Unity can use to tell this script the bike's "
             "initial position and orientation.)",
        default=0
    )
    parser.add_argument(
        '--speed-sensor',
        choices=[
            'tacx',
            'android',
            'irspeed',
            'irspeed_esp32',
            'keyboard',
            'flux-smart',
            'none',
        ],
        default='tacx',
        help="Sensor to use for speed readings ('keyboard' here means "
             "keyboard in PyGame)"
    )
    parser.add_argument(
        '--steering-sensor',
        choices=['tacx', 'android', 'keyboard', 'none'],
        default='tacx',
        help="Sensor to use for steering angle readings "
             "('keyboard' here means keyboard in PyGame)"
    )
    parser.add_argument(
        '--additional-sensors',
        choices=['tacx-speed', 'tacx-steering', 'android-steering'],
        nargs='*',
        help="Any additional sensors you want to be logged but that "
             "shouldn't contribute to the simulation"
    )
    parser.add_argument(
        '--android-port',
        default=15007,
        help="Which TCP port to use when using Android for any of the sensors",
        type=int,
    )
    parser.add_argument(
        '--android-deadzone',
        default=0,
        type=int,
        help="Dead zone for the Andorid steering angle sensor: "
             "Absolute value of the angle in degrees must be "
             "greater than this."
    )
    parser.add_argument(
        '--android-low-pass-cutoff',
        default=None,
        type=float,
        help="Apply a low-pass filter (equivalent to exponentially weighted "
             "moving average) "
             "to incoming steering angles from the Android app and use this "
             "value as the cutoff frequency. "
             "Note: It might be a better idea to apply smoothing in the "
             "Android app, i.e. at the source and where sensor readings "
             "can be processed at higher frequencies."
    )
    parser.add_argument(
        '--irspeed-port',
        default=4022,
        help='UDP port to listen on for updates from ir speed sensor.'
    )
    parser.add_argument(
        '--wheel-diameter',
        default=0.622,
        type=float,
        help="Wheel diameter in m used by the IR speed sensors.",
    )
    parser.add_argument(
        '--speed-factor',
        default=1,
        type=float,
        help="Speed multiplier, akin to gear ratio. So far only implemented "
             "for irspeedesp32."
    )
    parser.add_argument(
        '--num-spokes',
        default=9,
        type=int,
        help="Number of spokes with reflectors or magnets. "
             "Used by speed sensors.",
    )
    parser.add_argument(
        '--unity-ip',
        default='localhost',
        help=(
            "IP for connecting to the Unity simulation. "
            "WARNING: The old default was 131.234.121.241"
        )
    )
    parser.add_argument(
        '--unity-port',
        default=15006,
        help="UDP port for connecting to the Unity simulation",
        type=int,
    )
    parser.add_argument(
        '--unity-push-rate',
        default=40,
        help="Rate in Hz at which to send updates to the Unity simulation"
    )
    parser.add_argument(
        '--model-tracing-file',
        help='File to write bicycle model output to'
    )
    args = parser.parse_args()

    if args.additional_sensors is None:
        args.additional_sensors = []

    # socket_handler = SocketHandler('127.0.0.1', 19996)  # for cutelog
    my_handler = logging.StreamHandler()
    my_filter = MyFilter()
    my_handler.addFilter(my_filter)
    log_handlers = [my_handler]
    if args.logfile is not None:
        log_file_handler = logging.FileHandler(args.logfile, mode='w')
        log_file_handler.addFilter(my_filter)
        log_handlers.append(log_file_handler)
    else:
        print("Not logging to file")
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s %(name)-8.8s %(levelname)-4.4s "
               "%(funcName)-15.15s %(threadName)-15.15s] %(message)s",
        handlers=log_handlers
    )

    prepare_file_logger('tracing', args.model_tracing_file)

    tacx_names = ['tacx', 'flux-smart']
    if (
            args.speed_sensor in tacx_names
            or args.steering_sensor in tacx_names
            or 'tacx-steering' in args.additional_sensors
            or 'tacx-speed' in args.additional_sensors
            or 'flux-smart' in args.additional_sensors
    ):
        import tacx

    android_sensor = None
    speed_sensor = None
    if args.speed_sensor == 'tacx':
        speed_sensor = tacx.SpeedCadenceSmart()
        logger.debug('SpeedCadenceSmart() created')
    elif args.speed_sensor == 'flux-smart':
        speed_sensor = tacx.FluxSmart()
        logger.debug("FluxSmart() created")
    elif args.speed_sensor == 'android':
        android_sensor = AndroidSensor(
            port=args.android_port,
            deadzone=args.android_deadzone,
            low_pass_cutoff_frequency=args.android_low_pass_cutoff
        )
        speed_sensor = android_sensor
    elif args.speed_sensor == 'irspeed':
        speed_sensor = IRSpeedSensor(
            port=args.irspeed_port,
            wheel_diameter=args.wheel_diameter,
            magnets=args.num_spokes,
        )
    elif args.speed_sensor == 'irspeed_esp32':
        speed_sensor = IRSpeedSensorEsp32(
            port=args.irspeed_port,
            wheel_diameter_m=args.wheel_diameter,
            num_spokes=args.num_spokes,
            speed_factor=args.speed_factor,
        )

    angle_sensor = None
    if args.steering_sensor == 'tacx':
        angle_sensor = tacx.BlackTrack()
        logger.debug('BlackTrack() created')
    elif args.steering_sensor == 'android':
        angle_sensor = (
            android_sensor
            if android_sensor is not None
            else AndroidSensor(
                port=args.android_port,
                deadzone=args.android_deadzone,
            )
        )

    additional_sensors = []
    if args.additional_sensors is not None:
        for sensor_name in args.additional_sensors:
            if sensor_name == 'android-steering':
                additional_sensors.append(AndroidSensor(
                    port=args.android_port,
                    deadzone=args.android_deadzone,
                ))
            elif sensor_name == 'tacx-steering':
                additional_sensors.append(tacx.BlackTrack())
            elif sensor_name == 'tacx-speed':
                additional_sensors.append(tacx.SpeedCadenceSmart())
            elif sensor_name == 'flux-smart':
                additional_sensors.append(tacx.FluxSmart())

    simulation = bikesim.BikeSimulation(
        speed_sensor=speed_sensor,
        steer_angle_sensor=angle_sensor,
        initial_orientation_degrees=args.initial_orientation
    )
    # simulation = bikesim.BikeSimulation(speed_sensor=speed_sensor)
    # simulation = bikesim.BikeSimulation()  # use dummy sensors
    visualization = bikesim.BikeVisualization(
        bikesim=simulation,
        keyboard_steering=args.steering_sensor == 'keyboard',
        keyboard_acceleration=args.speed_sensor == 'keyboard'
    )
    unity_con = unity.UnityConnector(
        simulation,
        udp_ip=args.unity_ip,
        udp_port=args.unity_port,
        push_rate=args.unity_push_rate,
    )

    try:
        # order matters
        global runners
        runners = [simulation, visualization, unity_con, *additional_sensors]
        runners += [speed_sensor] if speed_sensor is not None else []
        runners += (
            [angle_sensor]
            if angle_sensor is not None and angle_sensor != speed_sensor
            else []
        )

        for runner in runners:
            runner.start()
            logger.debug("Started {}".format(runner))

        visualization.join()
        logger.debug("Visualization joined")
    except KeyboardInterrupt:
        logger.warning("Received KeyboardInterrupt. I'm dying now. Bye.")
    finally:
        logger.debug("executing finally")
        for runner in runners[::-1]:
            runner.stop()
            logger.debug("Stopped {}".format(runner))
        for runner in runners:
            runner.join()
            logger.debug("Joined {}".format(runner))


if __name__ == '__main__':
    main()
