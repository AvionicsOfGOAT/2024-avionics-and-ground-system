import asyncio
import logging
from datetime import datetime
from typing import Optional

import RPi.GPIO as GPIO

from config import PARACHUTE_CONFIG


class Parachute:
    def __init__(self):
        self.servo_pin = PARACHUTE_CONFIG["servo_pin"]
        self.relay_pin = PARACHUTE_CONFIG["relay_pin"]
        self.is_deployed = False
        self.pwm: Optional[GPIO.PWM] = None
        self.setup_gpio()

    def setup_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        GPIO.setup(self.relay_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.servo_pin, 50)
        self.pwm.start(0)
        GPIO.output(self.relay_pin, True)
        logging.info("GPIO setup completed.")

    async def set_angle(self, angle: float) -> None:
        if self.pwm is None:
            logging.error("PWM not initialised.")
            return

        duty_cycle = (angle / 18) + 2
        self.pwm.ChangeDutyCycle(duty_cycle)
        await asyncio.sleep(0.4)
        self.pwm.ChangeDutyCycle(0)
        logging.debug(f"Servo angle set to {angle}")

    async def deploy(self) -> None:
        if self.is_deployed:
            logging.warning("Parachute already deployed.")
            return

        try:
            logging.info("Deploying parachute.")
            self.is_deployed = True
            GPIO.output(self.relay_pin, False)
            await self.set_angle(180)
            self.log_deployment()
        except Exception as e:
            logging.error(f"Error while deploying parachute: {e}")
            self.is_deployed = False

    def log_deployment(self) -> None:
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("deploy.txt", "w") as file:
                file.write(current_time)
            logging.info(f"Deployment logged at {current_time}.")
        except Exception as e:
            logging.error(f"Error while logging deployment: {e}")

    def cleanup(self) -> None:
        if self.pwm:
            self.pwm.stop()
        GPIO.cleanup()
        logging.info("GPIO resources cleaned up.")


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    parachute = Parachute()
    try:
        await parachute.deploy()
    finally:
        parachute.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
