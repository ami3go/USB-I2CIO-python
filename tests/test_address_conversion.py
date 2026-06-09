import pytest

from devasys_usbi2cio.driver import DevasysUsbI2cIo


def test_addr7_to_devasys():
    assert DevasysUsbI2cIo._addr7_to_devasys(0x27) == 0x4E
    assert DevasysUsbI2cIo._addr7_to_devasys(0x68) == 0xD0
    assert DevasysUsbI2cIo._addr7_to_devasys(0x00) == 0x00
    assert DevasysUsbI2cIo._addr7_to_devasys(0x7F) == 0xFE


@pytest.mark.parametrize("addr", [-1, 0x80, 0x100])
def test_invalid_addr7(addr):
    with pytest.raises(ValueError):
        DevasysUsbI2cIo._addr7_to_devasys(addr)
