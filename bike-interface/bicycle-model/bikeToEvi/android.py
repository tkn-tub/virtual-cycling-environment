#!/usr/bin/env python3

"""
Provides sensor instances for connecting to our Bicycle Telemetry Android app.
"""

import threading
import logging
import math
import time
import socket
import select


LOGGER = logging.getLogger('android')
TRACER = logging.getLogger("tracing.android")


class AndroidSensor:

    def __init__(
            self,
            port: int = 4021,
            deadzone=None,
            low_pass_cutoff_frequency=None
    ):
        # Member variables required by the bikesim sensor interface:
        self.lock = threading.Lock()
        self.speed = 2  # m/s
        self.steer_angle = 0  # deg
        self._last_update_time = time.time()
        self._deadzone = deadzone

        # Low-pass filter:
        self._low_pass_cutoff_frequency = low_pass_cutoff_frequency
        self._low_pass_prev_output_angle = 0

        local_address = ("0.0.0.0", port)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.bind(local_address)
        LOGGER.info(
            f"Set up socket waiting for Android telemetry on {local_address}."
        )

        self._terminated = threading.Event()
        self._recv_thread = threading.Thread(
            target=self._receive_sensor_data,
            name='AndroidSensor_worker'
        )
        LOGGER.info(
            "Listener thread for Android steering angles created "
            "(not started yet)"
        )

    def start(self):
        self._recv_thread.start()

    def stop(self):
        LOGGER.debug("AndroidSensor.stop() called")
        self._terminated.set()
        self.join()
        LOGGER.debug("AndroidSensor successfully stopped")

    def join(self):
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
            LOGGER.debug(
                f"Received android message '{msg}' at {time.time()}"
            )
            msg = msg.decode('utf-8').replace('\n', '')
            new_angle = -math.degrees(float(msg.split(',')[0]))
            if self._low_pass_cutoff_frequency is not None:
                # Apply low-pass filter
                # (equivalent to exponentially weighted moving average)
                dt = time.time() - self._last_update_time
                # Calculate the smoothing factor from a given cutoff frequency:
                alpha = ((360.0 * dt * self._low_pass_cutoff_frequency) /
                         (360.0 * dt * self._low_pass_cutoff_frequency + 1))
                new_angle = (
                    alpha * new_angle
                    + (1.0 - alpha) * self._low_pass_prev_output_angle
                )
                self._low_pass_prev_output_angle = new_angle
            if self._deadzone is not None:
                if abs(new_angle) > self._deadzone:
                    # valid angle, reduce by deadzone
                    if new_angle > 0:
                        new_angle -= self._deadzone
                    else:
                        new_angle += self._deadzone
                else:
                    # invalid (too small) angle, discard as zero
                    new_angle = 0
            with self.lock:
                self.steer_angle = new_angle
            TRACER.debug(f"steering_angle,{self.steer_angle:.6f}")
            self._last_update_time = time.time()
