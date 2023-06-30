#!/usr/bin/env python3

import sys
from ant.easy.channel import Channel
from ant.easy.node import Node
import ant.easy
from datetime import datetime
from collections import deque
# from threading import Timer
import time

import array
import threading
import logging
import configparser
import math

logger = logging.getLogger('tacx')
TRACER = logging.getLogger("tracing.tacx")

# Constants
NETWORK_KEY_ANT_PLUS = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]
NETWORK_KEY_PUBLIC = [0xE8, 0xE4, 0x21, 0x3B, 0x55, 0x7A, 0x67, 0xC1]

# Executed on module load
try:
    node = Node()
    node_started = threading.Event()
except ant.base.driver.DriverNotFound:
    sys.exit(
        "Driver not found. "
        "Please make sure the ANT+ dongle is connected."
    )


class BlackTrack():
    """
    An implementation of a steering angle sensor using the Tacx
    BlackTrack (T2420)
    """
    def __init__(self):
        node.set_network_key(network=0x00, key=NETWORK_KEY_PUBLIC)
        self._channel = node.new_channel(
            Channel.Type.BIDIRECTIONAL_RECEIVE,
            0x00,
        )
        self.keep_alive_thread = threading.Thread(target=self._keep_alive)

        self.terminated = threading.Event()
        self.lock = threading.Lock()
        self._worker_thread = threading.Thread(
            target=self._worker,
            name='BlackTrack_worker',
        )

        self.calibration = configparser.ConfigParser()
        self.calibration.read("calibration.ini")

        with self.lock:
            self.raw_angle = 0
            self.steer_angle = 0

    def start(self):
        self._open_channel()
        self.keep_alive_thread.start()
        self._worker_thread.start()

    def stop(self):
        logger.debug("BlackTrack.stop() called")
        node.stop()
        self.terminated.set()
        self.join()
        logger.debug("BlackTrack worker and keepalive thread joined")

    def join(self):
        self._worker_thread.join()
        self.keep_alive_thread.join()

    def __del__(self):
        self.stop()

    @staticmethod
    def _worker():
        if not node_started.is_set():
            logger.debug("Starting node now")
            node_started.set()
            node.start()
            node_started.clear()
            logger.debug("Node start() returned")

    def _open_channel(self):
        # These parameters are documented in the ccs wiki
        self._channel.on_broadcast_data = self.data_update
        # ^ openant will crash if this is unset
        self._channel.set_search_timeout(20)
        # TODO: Find a good period that minimizes lost packets
        self._channel.set_period(2048 * 8)
        # ^ too frequent updates make it lag behind
        self._channel.set_rf_freq(60)  # Ch57 = 2.457 GHz
        self._channel.set_id(deviceNum=3209, deviceType=84, transmissionType=1)
        self._channel.open()  # blocks until connected

    def _keep_alive(self):
        while not self.terminated.is_set():
            logger.debug('sending keep_alive')
            self._channel.send_broadcast_data(array.array(
                'B',
                [0x01, 00, 00, 00, 00, 00, 00, 00]
            ))
            self.terminated.wait(10)  # interruptable sleep

    def normalize_angle(self, angle_raw):
        # Enter Calibration Data here:
        cal_left = float(self.calibration['BlackTrack']['left'])
        cal_center = float(self.calibration['BlackTrack']['center'])
        cal_right = float(self.calibration['BlackTrack']['right'])

        # Shift center to 0
        cal_left -= cal_center
        cal_right -= cal_center
        angle_raw -= cal_center
        cal_center = 0

        if angle_raw < cal_center:
            angle = angle_raw / cal_left * -45
        else:
            angle = angle_raw / cal_right * 45

        # make left-turns positive
        angle *= -1
        return angle

    def data_update(self, data):
        """Called when data from the blacktrack angle-meter is received"""
        angle_raw = int.from_bytes(data[1:3], byteorder="big", signed=True)
        angle = self.normalize_angle(angle_raw)
        # battery = data[3] / 0xff
        # ^ TODO is this really battery? just an assumption
        logger.info("angle_raw: {}, angle: {:.2f}, at time {}".format(
            angle_raw,
            angle,
            time.time()
        ))

        with self.lock:
            self.raw_angle = angle_raw
            self.steer_angle = angle


class SpeedCadenceSmart():
    """
    An implementation of a speed sensor using the Tacx Speed and
    Cadence Smart (T2015)
    """
    def __init__(self):
        node.set_network_key(network=0x01, key=NETWORK_KEY_ANT_PLUS)
        self._channel = node.new_channel(
            Channel.Type.BIDIRECTIONAL_RECEIVE,
            0x01,
        )
        self.lock = threading.Lock()

        self.magnets = 9
        self.wheelsize = 0.622 * math.pi / self.magnets  # in meters
        # holds a history of (time, wheel_revolutions) tuples
        self.revolution_queue = deque(maxlen=10)
        self.data_age_threshold = 4  # in s

        self.speed_log_file = open("speedlog.csv", 'w')
        self.speed_log_file.write('timestamp,speed\n')

        with self.lock:
            self.speed = 0  # in m/s

    def start(self):
        self._open_channel()

        self._worker_thread = threading.Thread(
            target=self._worker,
            name='SpeedCadenceSmart_worker',
        )
        self._worker_thread.start()

    def stop(self):
        logger.debug("SpeedCadenceSmart.stop() called")
        node.stop()
        self.join()
        logger.debug("SpeedCadenceSmart worker thread joined")
        self.speed_log_file.close()

    def join(self):
        self._worker_thread.join()

    def __del__(self):
        self.stop()

    def _open_channel(self):
        """Blocks until connected to Sensor"""
        # These parameters are defined in the ANT+ device profile
        self._channel.on_broadcast_data = self.data_update_raw
        self._channel.set_search_timeout(20)
        # TODO: Find a good period that minimizes lost packets
        self._channel.set_period(8086 * 2)
        self._channel.set_rf_freq(57)  # Ch57 = 2.457 GHz
        self._channel.set_id(deviceNum=0, deviceType=121, transmissionType=0)
        self._channel.open()  # blocks until connected

    @staticmethod
    def _worker():
        if not node_started.is_set():
            logger.debug("Starting node now")
            node_started.set()
            node.start()
            node_started.clear()
            logger.debug("Node start() returned")

    def data_update_raw(self, data):
        # pedal_revolutions = int(str(data[3]*256 + data[2]))
        wheel_revolutions = int(str(data[7]*256 + data[6]))
        TRACER.debug(f"tacx_revolutions_raw,{wheel_revolutions:.6f}")
        self.data_update(wheel_revolutions)

    def data_update(self, wheel_revolutions):
        """Call this on data from the speed sensor"""
        now = datetime.now()
        if (len(self.revolution_queue) == 0 or
                wheel_revolutions != self.revolution_queue[-1][1]):
            self.revolution_queue.append((now, wheel_revolutions))

        # discard data older than X sec
        while len(self.revolution_queue) > 0:
            old = self.revolution_queue[0]
            if (now - old[0]).total_seconds() > self.data_age_threshold:
                self.revolution_queue.popleft()
                logger.debug("Removed old element")
            else:
                break

        # we did not receive anything for at least 3 seconds
        # assume speed=0 and stop calculation
        if len(self.revolution_queue) == 0:
            self.speed = 0
            logger.info(
                "Revolutions: {:4}, Speed: {:6.2f} m/s, at time {}".format(
                    wheel_revolutions,
                    self.speed,
                    time.time()
                )
            )
            self.print_queue()
            return

        old = self.revolution_queue[0]
        delta_time = (now - old[0]).total_seconds()
        delta_dist = (wheel_revolutions - old[1]) * self.wheelsize
        if delta_time != 0:
            self.speed = delta_dist / delta_time

        logger.info(
            f"Revolutions: {wheel_revolutions:4}, "
            f"Speed: {self.speed:6.2f} m/s, "
            f"Queuesize: {len(self.revolution_queue)}, "
            f"at time {time.time()}"
        )
        self.speed_log_file.write(f'{now.timestampe()},{self.speed}\n')

    def print_queue(self):
        for i, elem in enumerate(self.revolution_queue):
            print("{}: ({}, {})".format(i, elem[0].strftime("%X.%f"), elem[1]))


class FluxSmart():
    """
    An implementation of a smart trainer using TacxFlux 2
    """
    def __init__(self):
        ready = False
        while not ready:
            try:
                node.set_network_key(network=0x01, key=NETWORK_KEY_ANT_PLUS)
                self._channel = node.new_channel(
                    Channel.Type.BIDIRECTIONAL_RECEIVE,
                    0x01,
                )
                ready = True
                logger.info("FluxSmart ready")
            except ant.easy.AntException as e:
                logger.warning(
                    "Encountered an AntException while trying to set up a "
                    f"channel: {e}\n\n"
                    "Trying again…"
                )
                # likely a timeout, try again by not setting ready = True

        self.lock = threading.Lock()
        self._worker_thread = threading.Thread(
            target=self._worker,
            name='FluxSmart',
        )

        # def on_press(key):  # For braking purpose
        #     try:
        #         if key.char == 'b':
        #             print("                                                        Brakes Applied")
        #             self._channel.send_broadcast_data(array.array('B', [0x30,255,255,255,255,255,255,200])) # Basic resistance data page is sent from controller to set total resistance. 200 is max
        #             #self._channel.send_broadcast_data(array.array('B', [0x46,255,255,255,255,255,71,255])) # Common page #70 sent from controller to request FE Capabilities page
        #         if key.char == 'r':
        #             print("                                                        Brakes Released")
        #             self._channel.send_broadcast_data(array.array('B', [0x30,255,255,255,255,255,255,0])) # Basic resistance data page is sent from controller to set total resistance. 0 is min
        #             #self._channel.send_broadcast_data(array.array('B', [0x46,255,255,255,255,255,71,255])) # Common page #70 sent from controller to request FE Capabilities page
        #     except AttributeError:
        #         print("in catch released")

        with self.lock:
            self.speed = 0 # in Kmph
            self.power = 0 # in Watt
            self.cadence = 0 # in Rpm
        #     listener = Listener(on_press=on_press)
        #     listener.start()

    def start(self):
        self._open_channel()
        self._worker_thread.start()

    def stop(self):
        logger.debug("FluxSmart.stop() called")
        node.stop()
        self.join()
        logger.debug("FluxSmart worker thread joined")

    def join(self):
        self._worker_thread.join()

    def __del__(self):
        self.stop()

    def _open_channel(self):
        """Blocks until connected to Sensor"""
        # These parameters are defined in the ANT+ device profile document
        self._channel.on_broadcast_data = self.data_update_raw
        self._channel.set_search_timeout(30)
        # Channel period value that has minimum packet loss:
        self._channel.set_period(8192)
        # Ch57 = 2.457 GHz:
        self._channel.set_rf_freq(57)
        # Device number/serial number is present on the trainer i.e. 4605:
        self._channel.set_id(deviceNum=0, deviceType=17, transmissionType=5)
        # Blocks until connected
        self._channel.open()

    @staticmethod
    def _worker():
        if not node_started.is_set():
            logger.debug("Starting node now")
            node_started.set()
            node.start()
            node_started.clear()
            logger.debug("Node start() returned")

    def data_update_raw(self, data):
        # print(data)
        if data[0] == 16:  # 0x10 for speed
            v_mm_per_second = data[5] * 256 + data[4]
            with self.lock:
                self.speed = v_mm_per_second * 1e-3
            logger.debug(f"FluxSmart speed: {self.speed} m/s")
        # elif data[0] == 25: #0x19 for power
        #     power_MSN = data[6] & 0x0F #MSN of byte 6 ie 0-3
        #     power_MSN = power_MSN << 8
        #     power_MSN = int(str(power_MSN + data[5]))
        #     self.power = power_MSN
        #     self.cadence = data[2]
        #     print("                                                              Power" + str(power_MSN) + " Watts")
        #     print("                                                              Cadence " + str(data[2]) + " Rpm")

