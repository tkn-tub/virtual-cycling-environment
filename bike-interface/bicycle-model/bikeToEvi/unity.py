import threading
import time
import struct
import math
import socket
import logging

logger = logging.getLogger("unity")


class UnityConnector(threading.Thread):
    """Polls data from a BikeSimulation and sends it via a UDP socket.
    The message format is targeted at the Unity3D implementation by Mario Franke
    """
    def __init__(self, bikesim, udp_ip='localhost', udp_port=15006, push_rate=20):
        threading.Thread.__init__(self)
        self.push_delay = 1 / push_rate
        self.bikesim = bikesim
        self.terminated = threading.Event()

        self.UDP_IP = udp_ip
        self.UDP_PORT = udp_port

    def stop(self):
        self.terminated.set()

    def run(self):
        while not self.terminated.is_set():
            with self.bikesim.lock:
                x = self.bikesim.back_wheel_x
                y = self.bikesim.back_wheel_y
                z = 0
                roll = 0
                pitch = 0
                yaw = math.degrees(self.bikesim.bike_yaw) - 90
                steering_angle = self.bikesim.steer_angle
                speed = self.bikesim.speed  # v in m/s
            
            # Deserialization-Code:
            # y = BitConverter.ToDouble(data, 0);
            # x = BitConverter.ToDouble(data, 8) * -1;
            # z = BitConverter.ToDouble(data, 16);
            # roll = BitConverter.ToDouble(data, 24);
            # pitch = BitConverter.ToDouble(data, 32);
            # yaw = BitConverter.ToDouble(data, 40);
            # steering_angle = BitConverter.ToDouble(data, 48);
            # speed = BitConverter.ToDouble(data, 56);
            
            # send UDP Packet
            msg = struct.pack('dddddddd', y, x*-1, z, roll, pitch, yaw, steering_angle, speed)

            sock = socket.socket(socket.AF_INET, # Internet
                                 socket.SOCK_DGRAM) # UDP
            sock.sendto(msg, (self.UDP_IP, self.UDP_PORT))

            time.sleep(self.push_delay)
