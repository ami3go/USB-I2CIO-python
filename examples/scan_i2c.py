"""Basic DeVaSys USB-I2C/IO scan example."""

from devasys_usbi2cio import DevasysI2CError, DevasysUsbI2cIo


def main() -> None:
    try:
        with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll", instance=0) as i2c:
            print("Scanning I2C bus...")
            devices = i2c.scan()

            if devices:
                print("Found I2C devices:")
                for addr in devices:
                    print(f"  0x{addr:02X}")
            else:
                print("No I2C devices found.")

    except DevasysI2CError as exc:
        print("DeVaSys error:")
        print(exc)


if __name__ == "__main__":
    main()
