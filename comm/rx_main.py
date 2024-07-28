import time

from rf_modules import Receiver


def main(pin, sleep_time=1):
    receiver = Receiver(rx_pin=pin)

    try:
        while True:
            print("Listening for message...")
            received = receiver.receive()
            if received:
                print(f"Received: {received}")
            else:
                print("No valid message received")
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("Stopping receiver...")
    finally:
        receiver.cleanup()


if __name__ == "__main__":
    pin = 27
    sleep_time = 1

    main(pin=pin, sleep_time=1)
