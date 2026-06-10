"""Blinka-compatible DeVaSys USB-I2C/IO scan example."""

import time

from devasys_usbi2cio import DevasysBlinkaI2C


def main() -> None:
    i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll", instance=0)

    try:
        while not i2c.try_lock():
            time.sleep(0.01)

        try:
            print("Scanning I2C bus...")
            devices = i2c.scan()

            if devices:
                print("Found I2C devices:")
                for addr in devices:
                    print(f"  0x{addr:02X}")
            else:
                print("No I2C devices found.")
        finally:
            i2c.unlock()

    finally:
        i2c.deinit()


if __name__ == "__main__":
    main()
