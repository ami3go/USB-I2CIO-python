import pytest

from devasys_usbi2cio.blinka_adapter import DevasysBlinkaI2C


class FakeDevice:
    def __init__(self):
        self.calls = []
        self.closed = False

    def scan(self):
        self.calls.append(("scan",))
        return [0x27, 0x68]

    def write(self, address, data):
        self.calls.append(("write", address, bytes(data)))
        return len(data)

    def read(self, address, count):
        self.calls.append(("read", address, count))
        return bytes(range(count))

    def read_reg8(self, address, reg8, count):
        self.calls.append(("read_reg8", address, reg8, count))
        return bytes([reg8] * count)

    def read_reg16(self, address, reg16, count):
        self.calls.append(("read_reg16", address, reg16, count))
        return bytes([(reg16 >> 8) & 0xFF] * count)

    def close(self):
        self.closed = True


def make_adapter(allow_stop_fallback=True):
    i2c = DevasysBlinkaI2C.__new__(DevasysBlinkaI2C)
    i2c._dev = FakeDevice()
    i2c.frequency = None
    i2c._locked = False
    i2c._allow_stop_fallback = allow_stop_fallback
    i2c._pending_addr = None
    i2c._pending_write = None
    return i2c


def test_lock_unlock():
    i2c = make_adapter()

    assert i2c.try_lock() is True
    assert i2c.try_lock() is False

    i2c.unlock()
    assert i2c.try_lock() is True


def test_scan():
    i2c = make_adapter()

    assert i2c.scan() == [0x27, 0x68]


def test_writeto_slicing():
    i2c = make_adapter()

    i2c.writeto(0x27, bytes([1, 2, 3, 4]), start=1, end=3)

    assert i2c._dev.calls[-1] == ("write", 0x27, bytes([2, 3]))


def test_readfrom_into_slicing():
    i2c = make_adapter()
    buf = bytearray([99, 99, 99, 99, 99])

    i2c.readfrom_into(0x27, buf, start=1, end=4)

    assert buf == bytearray([99, 0, 1, 2, 99])


def test_writeto_then_readfrom_reg8():
    i2c = make_adapter()
    buf = bytearray(3)

    i2c.writeto_then_readfrom(0x68, bytes([0x75]), buf)

    assert buf == bytearray([0x75, 0x75, 0x75])
    assert i2c._dev.calls[-1] == ("read_reg8", 0x68, 0x75, 3)


def test_writeto_then_readfrom_reg16():
    i2c = make_adapter()
    buf = bytearray(2)

    i2c.writeto_then_readfrom(0x50, bytes([0x12, 0x34]), buf)

    assert buf == bytearray([0x12, 0x12])
    assert i2c._dev.calls[-1] == ("read_reg16", 0x50, 0x1234, 2)


def test_stop_false_then_read():
    i2c = make_adapter()
    buf = bytearray(1)

    i2c.writeto(0x68, bytes([0x75]), stop=False)
    i2c.readfrom_into(0x68, buf)

    assert buf == bytearray([0x75])
    assert i2c._pending_write is None
    assert i2c._pending_addr is None


def test_long_write_then_read_fallback():
    i2c = make_adapter(allow_stop_fallback=True)
    buf = bytearray(2)

    i2c.writeto_then_readfrom(0x20, bytes([1, 2, 3]), buf)

    assert ("write", 0x20, bytes([1, 2, 3])) in i2c._dev.calls
    assert i2c._dev.calls[-1] == ("read", 0x20, 2)


def test_long_write_then_read_no_fallback():
    i2c = make_adapter(allow_stop_fallback=False)
    buf = bytearray(2)

    with pytest.raises(OSError):
        i2c.writeto_then_readfrom(0x20, bytes([1, 2, 3]), buf)


def test_deinit_closes_device():
    i2c = make_adapter()

    i2c.deinit()

    assert i2c._dev.closed is True
