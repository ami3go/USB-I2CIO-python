"""DeVaSys USB-I2C/IO Python driver package."""

from .blinka_adapter import DevasysBlinkaI2C
from .driver import DevasysUsbI2cIo
from .errors import DevasysI2CError
from .types import (
    DEVINFO,
    I2C_TRANS,
    USBI2CIO_I2C_MAX_DATA,
    USBI2CIO_IO_MAX_DATA,
    USBI2CIO_MAX_DEVICES,
    IoMode,
    I2cTransType,
    PropertyCommand,
    PropertyOffset,
)

__all__ = [
    "DevasysUsbI2cIo",
    "DevasysBlinkaI2C",
    "DevasysI2CError",
    "I2C_TRANS",
    "DEVINFO",
    "USBI2CIO_MAX_DEVICES",
    "USBI2CIO_I2C_MAX_DATA",
    "USBI2CIO_IO_MAX_DATA",
    "I2cTransType",
    "IoMode",
    "PropertyOffset",
    "PropertyCommand",
]

__version__ = "0.2.0"
