import time

import RPi.GPIO as GPIO


class Transmitter(object):
    def __init__(self, tx_pin, bit_time=0.001):
        self.TX_PIN = tx_pin
        self.BIT_TIME = bit_time

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TX_PIN, GPIO.OUT)

    def __manchester_encode(self, data):
        encoded = []
        for bit in data:
            if bit == "0":
                encoded.extend([0, 1])
            else:
                encoded.extend([1, 0])
        return encoded

    def transmit(self, message):
        binary_message = "".join(format(ord(c), "08b") for c in message)
        encoded = self.__manchester_encode(binary_message)
        for bit in encoded:
            GPIO.output(self.TX_PIN, bit)
            time.sleep(self.BIT_TIME / 2)

    def cleanup(self):
        GPIO.cleanup(self.TX_PIN)


class Receiver(object):
    def __init__(self, rx_pin, bit_time=0.001):
        self.RX_PIN = rx_pin
        self.BIT_TIME = bit_time

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RX_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def __manchester_decode(self, data):
        decoded = []
        for i in range(0, len(data), 2):
            if data[i] == 0 and data[i + 1] == 1:
                decoded.append("0")
            elif data[i] == 1 and data[i + 1] == 0:
                decoded.append("1")
            else:
                return None
        return "".join(decoded)

    def receive(self, timeout=1):
        data = []
        start_time = time.time()
        while time.time() - start_time < timeout:
            if GPIO.input(self.RX_PIN) == GPIO.HIGH:
                data.append(1)
            else:
                data.append(0)
            time.sleep(self.BIT_TIME / 2)

        if len(data) % 2 != 0:
            data = data[:-1]

        decoded = self.__manchester_decode(data)
        if decoded:
            return "".join(
                chr(int(decoded[i : i + 8], 2)) for i in range(0, len(decoded), 8)
            )
        return None

    def cleanup(self):
        GPIO.cleanup(self.RX_PIN)
