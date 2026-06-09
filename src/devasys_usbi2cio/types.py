"""ctypes aliases and structures for the DeVaSys UsbI2cIo.dll API."""

import ctypes
from ctypes import wintypes

BYTE = ctypes.c_ubyte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong
LONG = ctypes.c_long
HANDLE = wintypes.HANDLE
BOOL = wintypes.BOOL


class I2C_TRANS(ctypes.Structure):
    """
    DeVaSys I2C transaction structure.

    Layout from the DeVaSys API examples:

    BYTE byTransType;
    BYTE bySlvDevAddr;
    WORD wMemoryAddr;
    WORD wCount;
    BYTE Data[256];
    """

    _pack_ = 1
    _fields_ = [
        ("byTransType", BYTE),
        ("bySlvDevAddr", BYTE),
        ("wMemoryAddr", WORD),
        ("wCount", WORD),
        ("Data", BYTE * 256),
    ]
