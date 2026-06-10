"""ctypes aliases, constants, and structures for the DeVaSys UsbI2cIo.dll API."""

import ctypes
from ctypes import wintypes
from enum import IntEnum

BYTE = ctypes.c_ubyte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong
ULONG = ctypes.c_ulong
LONG = ctypes.c_long
HANDLE = wintypes.HANDLE
BOOL = wintypes.BOOL

LPBYTE = ctypes.POINTER(BYTE)
LPWORD = ctypes.POINTER(WORD)
LPDWORD = ctypes.POINTER(DWORD)
LPULONG = ctypes.POINTER(ULONG)
LPLONG = ctypes.POINTER(LONG)

USBI2CIO_MAX_DEVICES = 127
USBI2CIO_I2C_HEADER_SIZE = 6
USBI2CIO_I2C_MAX_DATA = 1088
USBI2CIO_IO_MAX_DATA = 1088


class I2cTransType(IntEnum):
    """I2C transaction types from Usbi2cio.h."""

    I2C_TRANS_NOADR = 0x00
    I2C_TRANS_8ADR = 0x01
    I2C_TRANS_16ADR = 0x02
    I2C_TRANS_NOADR_NS = 0x03
    I2C_TRANS_XICOR = 0x04
    I2C_TRANS_8ADR_NONSEQ = 0x30
    I2C_TRANS_16ADR_NONSEQ = 0x31
    I2C_TRANS_24ADR_NONSEQ = 0x32


class IoMode(IntEnum):
    """Block I/O modes from Usbi2cio.h."""

    IO_MODE_SINGLE = 0
    IO_MODE_BLOCK_ABC = 1
    IO_MODE_BLOCK_A = 2
    IO_MODE_BLOCK_B = 3
    IO_MODE_BLOCK_C = 4
    IO_MODE_BLOCK_AB = 5
    IO_MODE_BLOCK_BC = 6
    IO_MODE_BLOCK_AC = 7


class PropertyOffset(IntEnum):
    """Property byte offsets from Usbi2cio.h."""

    PROPERTY_WRCOMMAND_RDCOUNT = 0x00
    PROPERTY_I2C_CONFIG = 0x01
    PROPERTY_FAST_XFER_CONFIG = 0x02
    PROPERTY_IO_CONFIG_GLOBAL = 0x03
    PROPERTY_IO_CONFIG_PORTA = 0x04
    PROPERTY_IO_CONFIG_PORTB = 0x05
    PROPERTY_IO_CONFIG_PORTC = 0x06
    PROPERTY_IO_OUTPUT_PORTA = 0x07
    PROPERTY_IO_OUTPUT_PORTB = 0x08
    PROPERTY_IO_OUTPUT_PORTC = 0x09
    PROPERTY_DEBUG_CONFIG_GLOBAL = 0x0A
    PROPERTY_DEBUG_CONFIG_0 = 0x0B
    PROPERTY_DEBUG_CONFIG_1 = 0x0C
    PROPERTY_USER_0 = 0x0D
    PROPERTY_USER_1 = 0x0E
    PROPERTY_USER_2 = 0x0F
    PROPERTY_USER_3 = 0x10
    PROPERTY_IO_CONFIG_PORTD = 0x11
    PROPERTY_IO_OUTPUT_PORTD = 0x12
    PROPERTY_IO_OUTPUT_MODE_PORTA = 0x13
    PROPERTY_IO_OUTPUT_MODE_PORTB = 0x14
    PROPERTY_IO_OUTPUT_MODE_PORTC = 0x15
    PROPERTY_IO_OUTPUT_MODE_PORTD = 0x16
    PROPERTY_I2C_DEFAULT_CHANNEL = 0x17
    PROPERTY_I2C_CHAN0_CLK_LO = 0x18
    PROPERTY_I2C_CHAN0_CLK_HI = 0x19
    PROPERTY_I2C_CHAN1_CLK_LO = 0x1A
    PROPERTY_I2C_CHAN1_CLK_HI = 0x1B
    PROPERTY_I2C_CHAN2_CLK_LO = 0x1C
    PROPERTY_I2C_CHAN2_CLK_HI = 0x1D
    PROPERTY_MAX_PROPERTY_BYTES = 0x1E


class PropertyCommand(IntEnum):
    """Property command values from Usbi2cio.h."""

    PROPERTY_CMD_STORE_TABLE_TO_EEPROM = 0x00
    PROPERTY_CMD_LOAD_TABLE_FROM_EEPROM = 0x01
    PROPERTY_CMD_DISABLE_EEPROM_TABLE = 0x02
    PROPERTY_CMD_RESET_TO_DEFAULTS = 0x03


# Property bit masks from Usbi2cio.h
PROP_I2C_RETRIES_FIELD = 0x07
PROP_I2C_IGNORE_NAK = 0x08
PROP_I2C_POLL_EEPROM_ACK = 0x10
PROP_I2C_AUTO_REDIRECT_A2_REQS = 0x20
PROP_I2C_RESERVED_FIELD = 0xC0

PROP_FAST_XFER_RD_FIELD = 0x07
PROP_FAST_XFER_RD_ENABLE = 0x08
PROP_FAST_XFER_WR_FIELD = 0x70
PROP_FAST_XFER_WR_ENABLE = 0x80

PROP_IO_23BIT_MODE = 0x01

PROP_DBG_MAX_DISPLAY_FIELD = 0x7F
PROP_DBG_GLOBAL_ENABLE = 0x80


class DEVINFO(ctypes.Structure):
    """Device information structure from Usbi2cio.h."""

    _fields_ = [
        ("byInstance", BYTE),
        ("SerialId", BYTE * 9),
    ]


LPDEVINFO = ctypes.POINTER(DEVINFO)


class I2C_TRANS(ctypes.Structure):
    """
    DeVaSys I2C transaction structure.

    Header definition:

    BYTE byTransType;
    BYTE bySlvDevAddr;
    WORD wMemoryAddr;
    WORD wCount;
    BYTE Data[1088];
    """

    _pack_ = 1
    _fields_ = [
        ("byTransType", BYTE),
        ("bySlvDevAddr", BYTE),
        ("wMemoryAddr", WORD),
        ("wCount", WORD),
        ("Data", BYTE * USBI2CIO_I2C_MAX_DATA),
    ]
