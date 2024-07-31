import RPi.GPIO as GPIO
from rpi_rf import RFDevice

GPIO.setmode(GPIO.BCM)


def receive_code():
    if rx_device.rx_code:
        code = rx_device.rx_code
        print(f"Received: {code}")
        return code
    return None


if __name__ == "__main__":
    RX_PIN = 27
    rx_device = RFDevice(RX_PIN)
    rx_device.enable_rx()

    try:
        while True:
            received = receive_code()
            if received:
                print(f"Processing received code: {received}")

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        rx_device.cleanup()
        GPIO.cleanup()
