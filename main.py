import asyncio
import logging
import signal
from typing import Any, Dict

from config import Config
from database import Database
from decision_maker import DecisionMaker
from parachute import Parachute
from sensor import BMP, EBIMU, GPS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FlightController:
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.decision_maker = DecisionMaker()
        self.parachute = Parachute()
        self.sensors = {"BMP": BMP(), "GPS": GPS(), "EBIMU": EBIMU()}
        self.data_queues: Dict[str, asyncio.Queue] = {
            sensor_name: asyncio.Queue() for sensor_name in self.sensors
        }
        self.database_queue = asyncio.Queue()
        self.running = True
        self.current_data = {"altitude": None, "orientation": None, "position": None}

    async def process_sensor_data(self):
        while self.running:
            for sensor_name, queue in self.data_queues.items():
                try:
                    sensor_data = queue.get_nowait()
                    await self.handle_sensor_data(sensor_name, sensor_data)
                except asyncio.QueueEmpty:
                    pass
                except Exception as e:
                    logger.error(f"Error processing {sensor_name} data: {e}")

            if all(self.current_data.values()):
                await self.make_deployment_decision()

            await asyncio.sleep(0.01)

    async def handle_sensor_data(self, sensor_name: str, data: Any):
        await self.database_queue.put((sensor_name, data))

        if sensor_name == "BMP":
            self.current_data["altitude"] = data
        elif sensor_name == "EBIMU":
            self.current_data["orientation"] = data
        elif sensor_name == "GPS":
            self.current_data["position"] = data

    async def make_deployment_decision(self):
        should_deploy, reason = await self.decision_maker.make_decision(
            self.current_data["altitude"],
            self.current_data["orientation"],
            self.current_data["position"],
        )

        if should_deploy:
            await self.deploy_parachute(reason)

    async def deploy_parachute(self, reason: str):
        if not self.parachute.is_deployed:
            await self.parachute.deploy()
            await self.database_queue.put(("PARACHUTE", reason))
            logger.warning(f"Parachute deployed. {reason}")

    async def save_to_database(self):
        while self.running:
            try:
                name, data = await self.database_queue.get()
                await self.db.save([(0, name, data)])
            except Exception as e:
                logger.error(f"Error saving to database: {e}")

    async def run_sensor(self, sensor_name: str):
        sensor = self.sensors[sensor_name]
        queue = self.data_queues[sensor_name]
        await sensor.run(queue)

    async def run(self):
        tasks = [
            self.process_sensor_data(),
            self.save_to_database(),
        ]

        for sensor_name in self.sensors:
            tasks.append(self.run_sensor(sensor_name))

        await asyncio.gather(*tasks)

    def stop(self):
        self.running = False
        logger.info("Stopping Flight Controller.")


async def main():
    controller = FlightController()

    def signal_handler():
        logger.info("Received stop signal.")
        controller.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(sig, signal_handler)

    try:
        await controller.run()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        controller.parachute.cleanup()
        logger.info("Flight controller stopped.")


if __name__ == "__main__":
    asyncio.run(main())
