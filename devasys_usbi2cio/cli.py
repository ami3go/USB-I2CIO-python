"""Command line tools for the DeVaSys USB-I2C/IO driver."""

import argparse
import sys

from driver import DevasysUsbI2cIo
from errors import DevasysI2CError


def scan_main(argv=None) -> int:
    """Run an I2C scan using the DeVaSys USB-I2C/IO board."""
    parser = argparse.ArgumentParser(
        description="Scan I2C bus using DeVaSys USB-I2C/IO board."
    )
    parser.add_argument("--dll", default="UsbI2cIo.dll", help="Path to UsbI2cIo.dll")
    parser.add_argument("--instance", type=int, default=0, help="DeVaSys device instance")
    parser.add_argument(
        "--start",
        type=lambda value: int(value, 0),
        default=0x03,
        help="Start 7-bit I2C address, decimal or hex. Default: 0x03",
    )
    parser.add_argument(
        "--end",
        type=lambda value: int(value, 0),
        default=0x77,
        help="End 7-bit I2C address, decimal or hex. Default: 0x77",
    )
    args = parser.parse_args(argv)

    try:
        with DevasysUsbI2cIo(dll_path=args.dll, instance=args.instance) as i2c:
            print("Scanning I2C bus...")
            devices = i2c.scan(start=args.start, end=args.end)

            if devices:
                print("Found I2C devices:")
                for addr in devices:
                    print(f"  0x{addr:02X}")
            else:
                print("No I2C devices found.")
        return 0

    except (DevasysI2CError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    """Default console entry point."""
    return scan_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
