import time

import adafruit_bmp280
import board
import serial
from pyubx2 import UBXReader

from data_file import DataFile
from database import Database


class Sensor:
    def __init__(self):
        self.name = ""

    def init(self):
        self.data_file = DataFile(self.name)
        print(self.name + " connected.")

    def reader(self, queue):
        print(self.name + " process started.")
        while True:
            data = self.read()
            if data != None:
                queue.put(data)

    def save(self, data):
        self.data_file.save(data)

    def read(self):
        return

    def consol_print(self, data):
        # print(self.name,":",data)
        pass


class Bmp(Sensor):
    def __init__(self):
        self.name = "BMP"
        self.INIT_TIMES = 50
        self.init_altitude = 0
        self.sensor = self.init()

    def init(self):
        i2c = board.I2C()
        sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        sensor.sea_level_pressure = 1013.25
        init_buffer = []
        self.INIT_TIMES = 50
        print("Wait BMP Initialing...")
        for i in range(self.INIT_TIMES):
            init_buffer.append(sensor.altitude)
            if (i + 1) % 10 == 0:
                print(f"{(i + 1) * 2} %")
        self.init_altitude = sum(init_buffer) / self.INIT_TIMES
        print("Done OK")
        super().init()
        return sensor

    def read(self):
        try:
            data = self.sensor.altitude - self.init_altitude
            super().save(data)
            return data
        except:
            print(self.name, "is unavailable")


class Gps(Sensor):
    def __init__(self):
        self.name = "GPS"
        self.sensor = self.init()

    def init(self):
        stream = serial.Serial("/dev/ttyAMA2", baudrate=9600, timeout=50)
        sensor = UBXReader(stream)
        super().init()
        return sensor

    def read(self):
        data = 0
        (raw_data, parsed_data) = self.sensor.read()
        # print(raw_data)
        lines = str(raw_data).split("$")
        gngll_data = ""
        for line in lines:
            if line.startswith("GNGLL"):
                gngll_data = line
                break
        gngll_data = gngll_data.replace(",,", ",")
        parts = gngll_data.split(",")

        if len(parts) > 5:
            try:
                latitude = float(parts[1][:2]) + float(parts[1][2:]) / 60
                longitude = float(parts[3][:3]) + float(parts[3][3:]) / 60
                data = [latitude, latitude]
            except ValueError:
                pass
        if data != 0:
            super().save(data)
            self.consol_print(data)
            return data
        return None


class Ebimu(Sensor):
    def __init__(self):
        self.buf = ""
        self.name = "EBIMU"
        self.sensor = None
        self.init_r = 0
        self.init_p = 0
        self.init_y = 0

        self.init()

    def init(self):
        self.sensor = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.001)
        # sensor = self.sensor
        super().init()
        init_buffer_r = []
        init_buffer_p = []
        init_buffer_y = []
        self.INIT_TIMES = 50
        print("Wait EBIMU Initialing...")
        for i in range(self.INIT_TIMES):
            while True:
                data = self.read()
                if data != None:
                    init_buffer_r.append(data[0])
                    init_buffer_p.append(data[1])
                    init_buffer_y.append(data[2])
                    break

            if (i + 1) % 10 == 0:
                print(f"{(i + 1) * 2} %")
        self.init_r = sum(init_buffer_r) / self.INIT_TIMES
        self.init_p = sum(init_buffer_p) / self.INIT_TIMES
        self.init_y = sum(init_buffer_y) / self.INIT_TIMES
        print(self.init_r, self.init_p, self.init_y)
        print("Done OK")
        # return sensor

    def read(self):
        data = 0
        roll = 0
        pitch = 0
        yaw = 0
        x = 0
        y = 0
        z = 0
        try:
            if self.sensor.inWaiting():
                read_data = str(self.sensor.read()).strip()
                self.buf += read_data
                if read_data[3] == "n":
                    self.buf = self.buf.replace("'", "")
                    self.buf = self.buf.replace("b", "")

                    try:
                        roll, pitch, yaw, x, y, z = map(
                            float, self.buf[1:-4].split(",")
                        )
                    except Exception as e:
                        self.buf = ""

                    data = [roll, pitch, yaw, x, y, z]
                    # data = [((roll+360)-self.init_r)%180,((pitch+180)-self.init_p)%90,((yaw+360)-self.init_y)%180,x,y,z]
                    self.buf = ""
        except Exception as e:
            print(self.name, "is unavailable:", e)

        if data != 0:
            self.consol_print(data)
            super().save(data)
            return data
        return None
