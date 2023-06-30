#!/usr/bin/env python3

"""
Provides sensor instances for speed sensing via ir detector.
"""

import logging
import select
import socket
import threading
import time
import math

LOGGER = logging.getLogger("irspeed")
TRACER = logging.getLogger("tracing.irspeed")


class IRSpeedSensorEsp32:
    """
    IR speed sensor receiver and model
    for the IR sensor implemented on an ESP32 microcontroller.

    I.e., not the Raspberry Pi version that sends an update every
    time a spoke passes the sensor, but rather the version that
    transmits the averaged number of spokes per second at regular
    intervals.
    """

    def __init__(
            self,
            port=4022,
            wheel_diameter_m=0.622,
            num_spokes=3,
            speed_factor=1,
    ):
        # networking
        local_address = ("0.0.0.0", port)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.bind(local_address)
        LOGGER.info("Set up socket waiting for ir speed on %s.", local_address)

        self.spokes_per_second = 0
        self.wheel_diameter_m = wheel_diameter_m
        self.num_spokes = num_spokes
        self.speed_factor = speed_factor

        # Member variables required by the bikesim sensor interface:
        self.lock = threading.Lock()

        self._terminated = threading.Event()
        self._recv_thread = threading.Thread(
            target=self._receive_sensor_data, name="IRSpeedSensor_worker"
        )
        LOGGER.info(
            "Listener thread for ir speed sensor (ESP32 variant) "
            "created (not started yet)."
        )

    @property
    def speed(self):
        """Current speed of the wheel in meters per second."""
        speed = (
            self.speed_factor
            * self.spokes_per_second
            * self.wheel_diameter_m * math.pi
            / self.num_spokes
        )
        LOGGER.debug(
            f"spokes / s = {self.spokes_per_second:02.1f}, "
            f"speed = {speed:02.1f} m/s, "
            f"nspokes = {self.num_spokes}"
        )
        return speed

    def start(self):
        """Start receiving thread."""
        self._recv_thread.start()

    def stop(self):
        """Stop and join receiving thread."""
        LOGGER.debug("IRSpeedSensor.stop() called")
        self._terminated.set()
        self.join()
        LOGGER.debug("IRSpeedSensor successfully stopped")

    def join(self):
        """Join receiving thread."""
        self._recv_thread.join()
        self._sock.close()

    def __del__(self):
        self.stop()

    def _receive_sensor_data(self):
        poller = select.poll()
        poller.register(self._sock, select.POLLIN)
        while not self._terminated.is_set():
            if not poller.poll(10):
                # avoid getting stuck in recv calls that prohibit shutdown
                continue
            msg = self._sock.recv(1500)
            with self.lock:
                self.spokes_per_second = float(
                    msg.decode('ascii').replace("\n", "")
                )
                # LOGGER.debug(
                #     f"Received message '{msg}' "
                #     f"-> spokes per second = {self.spokes_per_second} "
                #     f"at {time.time()}, "
                # )
