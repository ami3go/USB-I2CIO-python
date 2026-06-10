import ctypes

from devasys_usbi2cio.driver import DevasysUsbI2cIo
from devasys_usbi2cio.types import I2C_TRANS, USBI2CIO_I2C_MAX_DATA


def make_driver_no_init():
    dev = DevasysUsbI2cIo.__new__(DevasysUsbI2cIo)
    return dev


def test_i2c_trans_size_matches_header():
    assert USBI2CIO_I2C_MAX_DATA == 1088
    assert ctypes.sizeof(I2C_TRANS) == 1094


def test_make_raw_write_transaction():
    dev = make_driver_no_init()
    trans = dev._make_trans(
        trans_type=DevasysUsbI2cIo.I2C_TRANS_NOADR,
        addr7=0x27,
        data=[0x12, 0x34],
    )

    assert trans.byTransType == DevasysUsbI2cIo.I2C_TRANS_NOADR
    assert trans.bySlvDevAddr == 0x4E
    assert trans.wMemoryAddr == 0
    assert trans.wCount == 2
    assert list(trans.Data[:2]) == [0x12, 0x34]


def test_make_reg8_transaction():
    dev = make_driver_no_init()
    trans = dev._make_trans(
        trans_type=DevasysUsbI2cIo.I2C_TRANS_8ADR,
        addr7=0x68,
        memory_addr=0x75,
        count=1,
    )

    assert trans.byTransType == DevasysUsbI2cIo.I2C_TRANS_8ADR
    assert trans.bySlvDevAddr == 0xD0
    assert trans.wMemoryAddr == 0x75
    assert trans.wCount == 1


def test_make_reg16_transaction():
    dev = make_driver_no_init()
    trans = dev._make_trans(
        trans_type=DevasysUsbI2cIo.I2C_TRANS_16ADR,
        addr7=0x50,
        memory_addr=0x1234,
        count=4,
    )

    assert trans.byTransType == DevasysUsbI2cIo.I2C_TRANS_16ADR
    assert trans.bySlvDevAddr == 0xA0
    assert trans.wMemoryAddr == 0x1234
    assert trans.wCount == 4
