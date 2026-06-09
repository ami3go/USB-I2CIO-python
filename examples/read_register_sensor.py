"""
Register-based sensor example using DevasysBlinkaI2C and Adafruit I2CDevice.

This example reads one byte from register 0x75 of a device at address 0x68.
For MPU6050-compatible devices, register 0x75 is WHO_AM_I.
"""

from devasys_usbi2cio import DevasysBlinkaI2C
from adafruit_bus_device.i2c_device import I2CDevice


def main() -> None:
    i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll", instance=0)

    try:
        device = I2CDevice(i2c, 0x68)
        result = bytearray(1)

        with device:
            device.write_then_readinto(bytes([0x75]), result)

        print(f"Register 0x75 = 0x{result[0]:02X}")

    finally:
        i2c.deinit()


if __name__ == "__main__":
    main()
