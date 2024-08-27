import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

import adafruit_bmp280
import board
import serial
from pyubx2 import UBXReader
from tenacity import retry, stop_after_attempt, wait_exponential

from config import BMP_CONFIG, EBIMU_CONFIG, GPS_CONFIG

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class Sensor(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def read(self) -> Optional[Any]:
        pass

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def safe_initialize(self) -> None:
        try:
            await self.initialize()
            self.initialized = True
            self.logger.info(f"{self.name} sensor initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing {self.name} sensor: {e}")
            raise

    async def run(self, queue: asyncio.Queue) -> None:
        self.logger.info(f"{self.name} process started.")
        while True:
            try:
                if not self.initialized:
                    await self.safe_initialize()
                data = await self.read()
                if data is not None:
                    await queue.put((self.name, data))
            except Exception as e:
                self.logger.error(f"Error in {self.name}: {e}")
                self.initialized = False
            await asyncio.sleep(0.1)


class BMP(Sensor):
    def __init__(self):
        super().__init__("BMP")
        self.i2c_address = BMP_CONFIG["i2c_address"]
        self.sensor = None
        self.init_altitude = 0

    async def initialize(self) -> None:
        i2c = board.I2C()
        self.sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        self.sensor.sea_level_pressure = 1013.25
        self.init_altitude = await self.calculate_init_altitude()

    async def calculate_init_altitude(self, init_times: int = 50) -> float:
        self.logger.info("Calculating initial altitude...")
        init_buffer = []
        for i in range(init_times):
            init_buffer.append(self.sensor.altitude)
            if (i + 1) % 10 == 0:
                self.logger.info(f"Initialization progress: {(i + 1) * 2}%")
            await asyncio.sleep(0.1)
        init_altitude = sum(init_buffer) / init_times
        self.logger.info(f"Initial altitude calculated: {init_altitude}")
        return init_altitude

    async def read(self) -> Optional[float]:
        try:
            return self.sensor.altitude - self.init_altitude
        except Exception as e:
            self.logger.error(f"Error reading BMP sensor: {e}")
            return None


class GPS(Sensor):
    def __init__(self):
        super().__init__("GPS")
        self.serial_port = GPS_CONFIG["serial_port"]
        self.baud_rate = GPS_CONFIG["baud_rate"]
        self.sensor = None
        self.reader = None

    async def initialize(self) -> None:
        self.sensor = serial.Serial(
            self.serial_port, baudrate=self.baud_rate, timeout=3
        )
        self.reader = UBXReader(self.sensor)
        self.logger.info("GPS sensor initialised.")

    async def read(self) -> Optional[List[float]]:
        try:
            raw_data, _ = await asyncio.to_thread(self.reader.read)
            gngll_data = next(
                (line for line in str(raw_data).split("$") if line.startswith("GNGLL")),
                "",
            )
            parts = gngll_data.replace(",,", ",").split(",")

            if len(parts) > 5:
                latitude = float(parts[1][:2]) + float(parts[1][2:]) / 60
                longitude = float(parts[3][:3]) + float(parts[3][3:]) / 60
                return [latitude, longitude]
        except Exception as e:
            self.logger.error(f"Error reading GPS sensor: {e}")
        return None


class EBIMU(Sensor):
    def __init__(self):
        super().__init__("EBIMU")
        self.serial_port = EBIMU_CONFIG["serial_port"]
        self.baud_rate = EBIMU_CONFIG["baud_rate"]
        self.sensor = None
        self.init_values = {"r": 0, "p": 0, "y": 0}

    async def initialize(self) -> None:
        self.sensor = serial.Serial(self.baud_rate, self.baud_rate, timeout=0.001)
        self.init_values = await self.calculate_init_values()

    async def calculate_init_values(self, init_times: int = 50) -> dict:
        self.logger.info("Calculating initial EBIMU values...")
        init_buffer = {"r": [], "p": [], "y": []}
        for i in range(init_times):
            data = await self.read_raw()
            if data:
                init_buffer["r"].append(data[0])
                init_buffer["p"].append(data[1])
                init_buffer["y"].append(data[2])
            if (i + 1) % 10 == 0:
                self.logger.info(f"Initialisation progress: {(i + 1) * 2}%")
            await asyncio.sleep(0.1)

        init_values = {k: sum(v) / len(v) for k, v in init_buffer.items()}
        self.logger.info(f"Initial EBIMU values calculated: {init_values}")
        return init_values

    async def read_raw(
        self,
    ) -> Optional[Tuple[float, float, float, float, float, float]]:
        if self.sensor.in_waiting:
            try:
                line = await asyncio.to_thread(self.sensor.readline)
                data = line.decode().strip().split(",")
                if len(data) == 6:
                    return tuple(map(float, data))
            except Exception as e:
                self.logger.error(f"Error reading raw EBIMU data: {e}")
        return None

    async def read(self) -> Optional[List[float]]:
        raw_data = await self.read_raw()
        if raw_data:
            roll, pitch, yaw, x, y, z = raw_data
            adjusted_data = [
                (roll - self.init_values["r"]) % 360,
                (pitch - self.init_values["p"]) % 180,
                (yaw - self.init_values["y"]) % 360,
                x,
                y,
                z,
            ]
            return adjusted_data
        return None


async def main():
    sensors = [BMP(), GPS(), EBIMU()]
    queues = {sensor.name: asyncio.Queue() for sensor in sensors}

    sensor_tasks = [
        asyncio.create_task(sensor.run(queues[sensor.name])) for sensor in sensors
    ]

    try:
        await asyncio.gather(*sensor_tasks)
    except asyncio.CancelledError:
        logging.info("Sensor tasks cancelled.")
    finally:
        for sensor in sensors:
            if hasattr(sensor, "sensor") and sensor.sensor:
                sensor.sensor.close()


if __name__ == "__main__":
    asyncio.run(main())
