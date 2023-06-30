#!/usr/bin/env python3

"""
Provides sensor instances for speed sensing via ir detector.
"""

import collections
import logging
import math
import select
import socket
import threading
import time

LOGGER = logging.getLogger("irspeed")
TRACER = logging.getLogger("tracing.irspeed")


class WheelModel:
    """
    Model computing rear wheel speed from reflector detection intervals.
    """

    def __init__(self, diameter, magnets, windowsize=3, filter_factor=0.75):
        self._tick_circumfence = diameter * math.pi / magnets
        self._timeout_factor = windowsize
        self._filter_factor = filter_factor
        self._intervals = collections.deque(maxlen=windowsize)
        self._last_tick_nr = None
        self._last_update_time = None

    def update(self, tick_nr, interval):
        """Update model from new inputs."""
        # update recent values
        self._intervals.append(interval)
        # remove outdated ticks (if ticks were lost since last update)
        if self._last_tick_nr:
            intervals_to_remove = tick_nr - (self._last_tick_nr + 1)
            for _ in range(intervals_to_remove):
                self._intervals.popleft()
        self._last_tick_nr = tick_nr
        self._last_update_time = time.time()

    def is_timed_out(self):
        """
        Return whether there have been recent updates.

        Timeout window is adaped to recent intervals.
        """
        if self._last_update_time is None or not self._intervals:
            return True
        timeout_delta = (
            sum(self._intervals) / len(self._intervals) * self._timeout_factor
        )
        return self._last_update_time + timeout_delta < time.time()

    def clear(self):
        """Clear history and reset to empty state."""
        self._intervals.clear()
        self._last_tick_nr = None
        self._last_update_time = None

    def speed(self):
        """Compute current speed."""
        if self.is_timed_out():
            # LOGGER.debug("Wheel is currently timed out.")
            # timed out, assume wheel is standing still (e.g., brakes enagaged)
            self.clear()
            return 0

        mean_interval = self._intervals[0]
        for prev_interval in list(self._intervals)[1:]:
            mean_interval = (mean_interval * self._filter_factor) + (
                prev_interval * (1 - self._filter_factor)
            )
        speed = self._tick_circumfence / mean_interval
        return speed


class IRSpeedSensor:
    """
    IR speed sensor receiver and model.
    """

    def __init__(self, port=4022, wheel_diameter=0.622, magnets=9):
        # networking
        local_address = ("0.0.0.0", port)
        self._sock = socket.socket(type=socket.SOCK_DGRAM)
        self._sock.bind(local_address)
        LOGGER.info("Set up socket waiting for ir speed on %s.", local_address)

        # wheel model
        self._wheel = WheelModel(wheel_diameter, magnets)

        # Member variables required by the bikesim sensor interface:
        self.lock = threading.Lock()

        self._terminated = threading.Event()
        self._recv_thread = threading.Thread(
            target=self._receive_sensor_data, name="IRSpeedSensor_worker"
        )
        LOGGER.info(
            "Listener thread for ir speed sensor created (not started yet)."
        )

    @property
    def speed(self):
        """Current speed of the wheel in meters per second."""
        return self._wheel.speed()

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
            LOGGER.debug("Received message '%s' at %s", msg, time.time())
            msg_parts = msg.decode('ascii').replace("\n", "").split(",")
            tick_nr = int(msg_parts[0])
            interval = float(msg_parts[1])
            with self.lock:
                self._wheel.update(tick_nr, interval)
            TRACER.debug("irspeed_tick,{tick_nr:06d}".format(tick_nr=tick_nr))
            TRACER.debug("irspeed_interval,{interval:.6f}".format(interval=interval))
