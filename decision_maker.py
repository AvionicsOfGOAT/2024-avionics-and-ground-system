import logging
from typing import List, Tuple

import numpy as np

from config import DECISION_MAKER_CONFIG
from database import Database

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DecisionMaker:
    def __init__(self):
        self.config = DECISION_MAKER_CONFIG
        self.db = Database()
        self.altitudes: List[float] = []
        self.moving_averages: List[float] = []
        self.falling_count = 0
        self.ma_count = 0

    def is_altitude_descent(self, altitude: float) -> bool:
        if (
            self.config["estimated_min_altitude"]
            <= altitude
            <= self.config["estimated_max_altitude"]
        ):
            self.altitudes.append(altitude)

        if len(self.altitudes) >= self.config["window_size"]:
            window = self.altitudes[-self.config["window_size"] :]
            mean = np.mean(window)
            self.moving_averages.append(mean)
            self.ma_count += 1

            if (
                self.ma_count > 1
                and self.moving_averages[-2] > self.moving_averages[-1]
            ):
                if mean > self.config["no_deploy_altitude"]:
                    self.falling_count += 1
                    logger.info(
                        f"Descent detected. Falling count: {self.falling_count}"
                    )
                else:
                    logger.info(
                        f"Descent detected but below no_deploy_altitude. Current altitude: {mean}"
                    )
            else:
                self.falling_count = 0
                logger.info("Ascent or stable altitude detected.")

            if self.falling_count >= self.config["falling_confirmation_threshold"]:
                logger.warning("Altitude descent confirmed")
                return True

        return False

    def is_descent_angle(self, orientation: Tuple[float, float, float]) -> bool:
        roll, pitch, _ = orientation
        angle_sum = abs(roll) + abs(pitch)

        if angle_sum >= self.config["critical_angle_threshold"]:
            logger.warning(
                f"Critical angle detected: Roll={roll}, Pitch={pitch}, Sum={angle_sum}"
            )
            return True

        logger.info(f"Current angle: Roll={roll}, Pitch={pitch}, Sum={angle_sum}")
        return False

    async def is_force_ejection_active(self) -> bool:
        try:
            response = await self.db.get_last("FE")
            if response and response[3] == "1":
                logger.warning("Force ejection active.")
                return True
            logger.info("Force ejection not active.")
            return False
        except Exception as e:
            logger.error(f"Error checking force ejection: {e}")
            return False

    def is_in_critical_area(self, position: Tuple[float, float, float]) -> bool:
        x, y, z = position
        length = np.sqrt(x**2 + y**2)
        height = length * self.config["initial_theta"]

        if height < abs(z):
            logger.warning(
                f"In critical area: calculated height={height}, actual z={z}"
            )
            return True

        logger.info(f"Not in critical area: calculated height={height}, actual z={z}")
        return False

    async def should_deploy_parachute(
        self,
        altitude: float,
        orientation: Tuple[float, float, float],
        position: Tuple[float, float, float],
    ) -> Tuple[bool, str]:
        if self.is_altitude_descent(altitude):
            return True, "Altitude descent"

        if self.is_descent_angle(orientation):
            return True, "Critical angle"

        if await self.is_force_ejection_active():
            return True, "Force ejection"

        if self.is_in_critical_area(position):
            return True, "Critical area"

        logger.info("No deployment criteria met")
        return False, "No deployment needed"

    def log_decision(
        self,
        should_deploy: bool,
        reason: str,
        altitude: float,
        orientation: Tuple[float, float, float],
        position: Tuple[float, float, float],
    ):
        log_data = {
            "decision": "Deploy" if should_deploy else "No Deploy",
            "reason": reason,
            "altitude": altitude,
            "orientation": orientation,
            "position": position,
            "falling_count": self.falling_count,
            "moving_average": (
                self.moving_averages[-1] if self.moving_averages else None
            ),
        }
        logger.info(f"Decision log: {log_data}")

    async def make_decision(
        self,
        altitude: float,
        orientation: Tuple[float, float, float],
        position: Tuple[float, float, float],
    ) -> Tuple[bool, str]:
        should_deploy, reason = await self.should_deploy_parachute(
            altitude, orientation, position
        )
        self.log_decision(should_deploy, reason, altitude, orientation, position)
        return should_deploy, reason


async def main():
    decision_maker = DecisionMaker()

    altitude = 350.0
    orientation = (30.0, 45.0, 0.0)
    position = (100.0, 100.0, 300.0)

    should_deploy, reason = await decision_maker.make_decision(
        altitude, orientation, position
    )
    print(f"Should deploy: {should_deploy}, Reason: {reason}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
