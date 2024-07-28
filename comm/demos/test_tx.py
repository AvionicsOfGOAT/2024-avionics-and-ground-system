import time

import RPi.GPIO as GPIO
from rpi_rf import RFDevice

GPIO.setmode(GPIO.BCM)


def transmit_code(code):
    tx_device.tx_code(code)
    print(f"Transmitted: {code}")


if __name__ == "__main__":
    TX_PIN = 17
    tx_device = RFDevice(TX_PIN)

    try:
        while True:
            transmit_code("test_transmission")
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        tx_device.cleanup()
        GPIO.cleanup()
