#!/usr/bin/env python3

from datetime import datetime
from pygame.locals import *

import math
import pygame
import threading
import time
import logging

logger = logging.getLogger("bikesim")
TRACER = logging.getLogger("tracing.bikesim")


class BikeSimulation(threading.Thread):
    """This holds the data on the location and orientation of the bike
    and allows its modification.
    Regularly polls it's given sensors for updates.
    Sensors can be either Tacx devices or DummySensors.
    """

    class DummySensor:
        """A Sensor providing dummy data. Use the lock for thread safety"""

        # For keyboard control:
        MAX_SPEED = 8  # m/s
        MAX_ACCELERATION = 1.5  # m/s^2
        MAX_DECELERATION = 3.3  # m/s^2
        CONST_DECELERATION = .5  # m/s^2
        MAX_REVERSE_SPEED = -1  # m/s
        MAX_STEER_ANGLE = 35  # deg

        def __init__(self):
            self.lock = threading.Lock()
            self.speed = 2  # m/s
            self.steer_angle = 20  # deg

        @staticmethod
        def clamp(val, min_val, max_val):
            return min(max_val, max(min_val, val))

        def game_tick(self, dt):
            # Apply constant deceleration (due to friction from wind, tires, etc.):
            with self.lock:
                self.speed = self.clamp(
                    self.speed - BikeSimulation.DummySensor.CONST_DECELERATION * dt,
                    0 if self.speed > 0 else BikeSimulation.DummySensor.MAX_REVERSE_SPEED,
                    BikeSimulation.DummySensor.MAX_SPEED if self.speed > 0 else 0
                )

        def turn_left(self, dt, rel_amount):
            with self.lock:
                self.steer_angle = BikeSimulation.DummySensor.MAX_STEER_ANGLE * rel_amount

        def accelerate(self, dt, rel_amount):
            with self.lock:
                if rel_amount > 0:
                    if self.speed >= 0:
                        # regular fwd acceleration
                        self.speed = self.clamp(
                            self.speed + self.MAX_ACCELERATION * rel_amount * dt,
                            0,
                            self.MAX_SPEED
                        )
                    else:
                        # braking from reverse "cycling":
                        self.speed = self.clamp(
                            self.speed + self.MAX_DECELERATION * rel_amount * dt,
                            self.MAX_REVERSE_SPEED,
                            0
                        )
                elif rel_amount < 0:
                    if self.speed > 0:
                        # regular braking
                        self.speed = self.clamp(
                            self.speed + self.MAX_DECELERATION * rel_amount * dt,
                            0,
                            self.MAX_SPEED
                        )
                    else:
                        # reverse acceleration
                        self.speed = self.clamp(
                            self.speed + self.MAX_DECELERATION * rel_amount * dt,
                            self.MAX_REVERSE_SPEED,
                            0
                        )

    def __init__(self, speed_sensor=None, steer_angle_sensor=None, initial_orientation_degrees=0):
        threading.Thread.__init__(self)

        speed_sensor = BikeSimulation.DummySensor() if speed_sensor is None else speed_sensor
        steer_angle_sensor = BikeSimulation.DummySensor() if steer_angle_sensor is None else steer_angle_sensor

        self.lock = threading.Lock()
        self.terminated = threading.Event()

        self.speed_sensor = speed_sensor
        self.steer_angle_sensor = steer_angle_sensor

        self.bike_len = 2  # in m
        self.bike_yaw = math.radians(initial_orientation_degrees)  # in radians
        self.front_wheel_x = 0
        self.front_wheel_y = 0
        self.back_wheel_x = math.sin(self.bike_yaw + math.pi) * self.bike_len
        self.back_wheel_y = math.cos(self.bike_yaw + math.pi) * self.bike_len

        self.speed = 0  # v in m/s
        self.steer_angle = 0  # in radians

    def stop(self):
        self.terminated.set()

    def run(self):
        """
        Bike model:
              dx
            ------FRONT
            |    a/|
            |    /b|
         dy |   /<--- Bike
            |  /   |
            |b/    |
            |/a    |
             ------
        
        We represent the bikes angle using a.
        All lengths are in meters.
        """

        interval = 0.01  # in sec

        while not self.terminated.is_set():
            # read data
            with self.speed_sensor.lock:
                self.speed = self.speed_sensor.speed
            with self.steer_angle_sensor.lock:
                self.steer_angle = math.radians(self.steer_angle_sensor.steer_angle)

            # Scale down speed proportionally to interval length
            speed_scaled = self.speed * interval
            start = datetime.now()

            with self.lock:
                # bike_yaw = a
                self.bike_yaw = math.atan2((self.front_wheel_y - self.back_wheel_y),
                                           (self.front_wheel_x - self.back_wheel_x))

                front_angle = self.bike_yaw + self.steer_angle
                self.front_wheel_x += math.cos(front_angle) * speed_scaled
                self.front_wheel_y += math.sin(front_angle) * speed_scaled

                # Not exactly, but good enough
                self.back_wheel_x += math.cos(self.bike_yaw) * speed_scaled
                self.back_wheel_y += math.sin(self.bike_yaw) * speed_scaled

                # now correct the bike length (distorted due to previous inaccuracy)
                self.bike_yaw = math.atan2((self.front_wheel_y - self.back_wheel_y),
                                           (self.front_wheel_x - self.back_wheel_x))
                self.back_wheel_x = self.front_wheel_x - math.cos(self.bike_yaw) * self.bike_len
                self.back_wheel_y = self.front_wheel_y - math.sin(self.bike_yaw) * self.bike_len

                logger.debug(
                    "front_wheel: ({}, {}), yaw: {}".format(self.front_wheel_x, self.front_wheel_y, self.bike_yaw))

            TRACER.debug("speed,{s.speed:.6f}".format(s=self))
            TRACER.debug("steer_angle,{s.steer_angle:.6f}".format(s=self))
            TRACER.debug("bike_yaw,{s.bike_yaw:.6f}".format(s=self))
            TRACER.debug("front_wheel_x,{s.front_wheel_x:.6f}".format(s=self))
            TRACER.debug("front_wheel_y,{s.front_wheel_y:.6f}".format(s=self))
            TRACER.debug("back_wheel_x,{s.back_wheel_x:.6f}".format(s=self))
            TRACER.debug("back_wheel_y,{s.back_wheel_y:.6f}".format(s=self))
            TRACER.debug("front_angle,{front_angle:.6f}".format(front_angle=front_angle))

            # We want this loop to execute as regularly timed as possible
            end = datetime.now()
            exec_time = end - start
            sleeptime = max(0, interval - exec_time.total_seconds())
            time.sleep(sleeptime)


class BikeVisualization(threading.Thread):
    """Uses pygame to visualize the bikes location and orientation.
    Regularly polls data from a BikeSimulation instance.
    """

    def __init__(
            self,
            bikesim,
            keyboard_steering=False,
            keyboard_acceleration=False,
    ):
        threading.Thread.__init__(self)
        self.bikesim = bikesim
        self.terminated = threading.Event()
        self.keyboard_steering = keyboard_steering
        self.keyboard_acceleration = keyboard_acceleration
        if keyboard_acceleration:
            with self.bikesim.speed_sensor.lock:
                self.bikesim.speed_sensor.speed = 0
        self.pos_trace = []
        """
        A cache of previous bicycle positions for
        drawing a trace of the bike's path.
        """
        self.pos_trace_len = 128

        self.height = 800
        self.width = 800

    def stop(self):
        self.terminated.set()

    def _to_pygame_coords(self, coords, scale=1):
        """assumes coords in form [[x1, y1], [x2, y2], ...]"""
        # Scale down
        for i, _ in enumerate(coords):
            for j, _ in enumerate(coords[i]):
                coords[i][j] *= scale

        # center green line
        for i, _ in enumerate(coords):
            coords[i][0] += self.width / 2
            coords[i][1] += self.height / 2

        # Flip y-axis so our origin is in bottom left
        for i, _ in enumerate(coords):
            coords[i][1] = self.height - coords[i][1]

        return coords

    def run(self):
        scale = 7  # scale of visual representation

        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        pygame.display.set_caption("Bike Simulation")

        # with self.bikesim.lock:
        #     self.bikesim.speed = 5
        #     self.bikesim.steer_angle = radians(25)

        clock = pygame.time.Clock()
        dt = 0
        while not self.terminated.is_set():
            for event in pygame.event.get():
                if event.type == QUIT:
                    logger.debug('pygame got a QUIT event')
                    self.stop()

            if self.keyboard_acceleration or self.keyboard_steering:
                keys = pygame.key.get_pressed()
                if keys[K_a] and self.keyboard_steering:
                    self.bikesim.steer_angle_sensor.turn_left(dt, 1)
                elif keys[K_d] and self.keyboard_steering:
                    self.bikesim.steer_angle_sensor.turn_left(dt, -1)
                elif self.keyboard_steering:
                    self.bikesim.steer_angle_sensor.turn_left(dt, 0)

                if keys[K_w] and self.keyboard_acceleration:
                    self.bikesim.speed_sensor.accelerate(dt, 1)
                elif keys[K_s] and self.keyboard_acceleration:
                    self.bikesim.speed_sensor.accelerate(dt, -1)

                # Sensors will be DummySensor instances, in these cases:
                if self.keyboard_steering:
                    self.bikesim.steer_angle_sensor.game_tick(dt)
                if self.keyboard_acceleration:
                    self.bikesim.speed_sensor.game_tick(dt)

            # We assume a cartesian coordinate system (origin in lower left)
            # convert it to pygames upper-left origin
            with self.bikesim.lock:
                bike_coords = [
                    [self.bikesim.back_wheel_x, self.bikesim.back_wheel_y],
                    [self.bikesim.front_wheel_x, self.bikesim.front_wheel_y]
                ]
            pygame_bike_coords = [
                pygame.math.Vector2(v)
                for v in
                self._to_pygame_coords(bike_coords, scale)
            ]
            v_bike_direction = pygame_bike_coords[1] - pygame_bike_coords[0]
            pygame_bike_len = v_bike_direction.length()
            v_bike_direction = v_bike_direction.normalize()
            # Vector pointing from the right of the bike:
            v_bike_right = pygame.math.Vector2(
                -v_bike_direction[1],
                v_bike_direction[0]
            )
            pygame_arrow_coords = [
                pygame_bike_coords[1]
                + 0.25 * pygame_bike_len * v_bike_right
                - 0.2 * pygame_bike_len * v_bike_direction,
                pygame_bike_coords[1],
                pygame_bike_coords[1]
                - 0.25 * pygame_bike_len * v_bike_right
                - 0.2 * pygame_bike_len * v_bike_direction,
            ]

            self.pos_trace.append(pygame_bike_coords[0])
            if len(self.pos_trace) > self.pos_trace_len:
                self.pos_trace.pop(0)

            screen.fill((0, 0, 0))
            if len(self.pos_trace) >= 2:
                # Draw a trace:
                pygame.draw.lines(
                    screen,
                    (128, 128, 128),
                    False,
                    self.pos_trace,
                )
            # Draw the bicycle:
            pygame.draw.lines(
                screen,
                (0, 255, 0),
                False,
                pygame_bike_coords
            )
            # Draw an arrow tip for the bicycle:
            pygame.draw.lines(
                screen,
                (100, 180, 0),
                False,
                pygame_arrow_coords
            )

            pygame.display.update()

            # time.sleep(0.01)
            dt = clock.tick(10) / 1000

        pygame.quit()

    def __del__(self):
        pygame.quit()
