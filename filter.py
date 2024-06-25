import math
import random
import time

import numpy as np


class ComplementaryFilter(object):
    def __init__(self, alpha):
        self.alpha = alpha
        self.attitude = np.zeros(3)

    def update(self, accel, gyro, dt):
        accel_norm = accel / np.linalg.norm(accel)

        pitch_accel = math.atan2(
            -accel_norm[0], math.sqrt(accel_norm[1] ** 2 + accel_norm[2] ** 2)
        )
        roll_accel = math.atan2(accel_norm[1], accel_norm[2])

        self.attitude[0] += gyro[0] * dt  # Roll
        self.attitude[1] += gyro[1] * dt  # Pitch
        self.attitude[2] += gyro[2] * dt  # Yaw

        self.attitude[0] = (1 - self.alpha) * self.attitude[0] + self.alpha * roll_accel
        self.attitude[1] = (1 - self.alpha) * self.attitude[
            1
        ] + self.alpha * pitch_accel

        return self.attitude


if __name__ == "__main__":
    # trunk-ignore(bandit/B311)
    alpha = random.random()
    filter = ComplementaryFilter(alpha)

    position = np.zeros(3)
    velocity = np.zeros(3)

    # Simulated IMU and GPS data
    accel_data = np.random.rand(3)  # Accelerometer data (x, y, z)
    gyro_data = np.random.rand(3)   # Gyroscope data (roll, pitch, yaw)
    gps_data = np.random.rand(3)    # GPS data (latitude, longitude, altitude)

    d = 0.1

    while True:
        attitude = filter.update(accel_data, gyro_data, d)
        position = gps_data - np.array([0.0, 0.0, 200.0])

        velocity += accel_data * d

        print("Attitude (roll, pitch, yaw):", attitude)
        print("Position (latitude, longitude, altitude):", position)
        print("Velocity (x, y, z):", velocity)
        print("=" * 50)

        # Simulate new data for the next iteration
        accel_data = np.random.rand(3)
        gyro_data = np.random.rand(3) * 0.1
        gps_data += np.random.rand(3) * 0.1

        time.sleep(d)

