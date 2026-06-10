from devasys_usbi2cio.driver import DevasysUsbI2cIo


class FakeChunkDriver(DevasysUsbI2cIo):
    def __init__(self):
        self.handle = 1
        self.calls = []

    def dapi_read_i2c(self, trans, expected_count=None, context=None):
        self.calls.append((trans.byTransType, trans.wMemoryAddr, trans.wCount, context))
        for index in range(trans.wCount):
            trans.Data[index] = index & 0xFF
        return trans.wCount


def test_raw_read_chunking_uses_1088_byte_header_limit():
    dev = FakeChunkDriver()
    data = dev.read(0x27, 2200)

    assert len(data) == 2200
    assert [call[2] for call in dev.calls] == [1088, 1088, 24]


def test_reg8_read_chunking_and_increment():
    dev = FakeChunkDriver()
    data = dev.read_reg8(0x68, 0x10, 2200)

    assert len(data) == 2200
    assert [call[1] for call in dev.calls] == [0x10, 0x50, 0x90]
    assert [call[2] for call in dev.calls] == [1088, 1088, 24]


def test_reg16_read_chunking_and_increment():
    dev = FakeChunkDriver()
    data = dev.read_reg16(0x50, 0x0100, 2200)

    assert len(data) == 2200
    assert [call[1] for call in dev.calls] == [0x0100, 0x0540, 0x0980]
    assert [call[2] for call in dev.calls] == [1088, 1088, 24]
