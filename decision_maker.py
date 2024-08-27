import math

import numpy as np

from database import Database
from sensor import Bmp


class DecisionMaker:
    def __init__(self):
        self.db = Database()
        self.init_theta()
        self.datas = []
        self.moving_averages = []
        self.falling_count = 0
        self.ma_count = 0

        self.WINDOW = 10
        self.FALLING_CONFIRMATION = 5
        self.NO_DEPLOY_ALTITUDE = 100
        self.ESTIMATED_MAX_ALTITUDE = 400
        self.ESTIMATED_MIN_ALTITUDE = -10
        self.theta = 0

    def init_theta(self):
        self.theta = 9.514

    def is_altitude_descent(self, bmp_value):
        altitude = bmp_value

        if self.ESTIMATED_MIN_ALTITUDE <= altitude <= self.ESTIMATED_MAX_ALTITUDE:
            self.datas.append(altitude)

        mean = np.mean(self.datas[-self.WINDOW :])
        self.moving_averages.append(mean)
        self.ma_count += 1

        is_valid_falling = False
        if self.moving_averages[-1] > self.NO_DEPLOY_ALTITUDE:
            is_valid_falling = True

        if (
            self.ma_count > 2
            and (self.moving_averages[-2] - self.moving_averages[-1]) > 0.0
        ):
            if is_valid_falling:
                print("down")
                self.falling_count += 1
        else:
            self.falling_count = 0
            print("up")
        if self.falling_count >= self.FALLING_CONFIRMATION:
            # print("deployed")
            return True
        return False

    def is_descent_angle(self, ebimu_value):
        return False
        r = ebimu_value[0]
        p = ebimu_value[1]
        if abs(r) + abs(p) >= 80:
            #            print(ebimu_value)
            return True
        else:
            return False

    def is_force_ejection_active(self):
        try:

            response = self.db.get_last("FE")
            # print(response)
            if response == "1":
                return True
            return False
        except:
            return False

    def is_in_critical_area(self, exact_position):
        x = exact_position[0]
        y = exact_position[1]
        z = exact_position[2]

        length = math.sqrt(x**2 + y**2)
        height = length * self.theta

        if height < abs(z):
            return True
        else:
            return False
