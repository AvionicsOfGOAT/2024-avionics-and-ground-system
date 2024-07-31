import time

from rf_modules import Transmitter


def main(pin, sleep_time=1):
    transmitter = Transmitter(tx_pin=pin)

    try:
        while True:
            message = "TEST"
            print(f"Transmitting: {message}")
            transmitter.transmit(message)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Stopping transmitter...")
    finally:
        transmitter.cleanup()


if __name__ == "__main__":
    pin = 27
    sleep_time = 1

    main(pin=pin, sleep_time=sleep_time)
