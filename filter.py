import time

import numpy as np


class ComplementaryFilter(object):
    def __init__(self, alpha_pos=0.98, alpha_att=0.98, dt=0.01):
        self.alpha_pos = alpha_pos
        self.alpha_att = alpha_att

        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.attitude = np.zeros(3)

        self.dt = dt  # 100Hz update rate

    def update(self, gps_pos, imu_accel, imu_gyro):
        # Update position
        gps_vel = (gps_pos - self.position) / self.dt
        imu_pos = self.position + self.velocity * self.dt + 0.5 * imu_accel * self.dt**2
        self.position = self.alpha_pos * imu_pos + (1 - self.alpha_pos) * gps_pos

        # Update velocity
        imu_vel = self.velocity + imu_accel * self.dt
        self.velocity = self.alpha_pos * imu_vel + (1 - self.alpha_pos) * gps_vel

        # Update attitude
        gyro_attitude = self.attitude + imu_gyro * self.dt
        accel_attitude = np.array(
            [
                np.arctan2(imu_accel[1], imu_accel[2]),
                np.arctan2(
                    -imu_accel[0], np.sqrt(imu_accel[1] ** 2 + imu_accel[2] ** 2)
                ),
                0,
            ]
        )
        self.attitude = (
            self.alpha_att * gyro_attitude + (1 - self.alpha_att) * accel_attitude
        )

    def get_state(self):
        return {
            "position": self.position,
            "velocity": self.velocity,
            "attitude": self.attitude,
        }


if __name__ == "__main__":
    alpha_pos = 0.98
    alpha_att = 0.98
    dt = 0.01

    cf = ComplementaryFilter(alpha_pos=alpha_pos, alpha_att=alpha_att, dt=dt)

    # Simulated IMU and GPS data
    gps_position = np.array([1.0, 2.0, 3.0])                # GPS data (latitude, longitude, altitude)
    imu_acceleration = np.array([0.1, 0.2, 9.8])            # Accelerometer data (x, y, z)
    imu_angular_velocity = np.array([0.01, 0.02, 0.03])     # Gyroscope data (roll, pitch, yaw)

    while True:
        cf.update(gps_position, imu_acceleration, imu_angular_velocity)

        state = cf.get_state()
        print("Position:", state["position"])
        print("Velocity:", state["velocity"])
        print("Attitude:", state["attitude"])


        # Replace this with actual IMU and GPS data acquisition
        imu_acceleration = np.random.rand(3)
        imu_angular_velocity = np.random.rand(3) * 0.1
        gps_position += np.random.rand(3) * 0.1

        # Replace this with actual timing control
        time.sleep(dt)
