import pytest

from devasys_usbi2cio import DevasysI2CError
from devasys_usbi2cio.driver import DevasysUsbI2cIo


def make_driver_no_init():
    dev = DevasysUsbI2cIo.__new__(DevasysUsbI2cIo)
    dev.handle = 1
    return dev


def test_error_string_contains_context():
    err = DevasysI2CError(
        "Failure",
        function="DAPI_WriteI2c",
        result=-1,
        context={"addr7": "0x27", "count": 1},
    )

    text = str(err)
    assert "Failure" in text
    assert "DAPI_WriteI2c" in text
    assert "result=-1" in text
    assert "addr7=0x27" in text


def test_check_result_non_negative_raises():
    dev = make_driver_no_init()

    with pytest.raises(DevasysI2CError):
        dev._check_result_non_negative("DAPI_ReadI2c", -1, context={"addr7": "0x27"})


def test_check_result_exact_raises():
    dev = make_driver_no_init()

    with pytest.raises(DevasysI2CError) as exc_info:
        dev._check_result_exact("DAPI_WriteI2c", result=0, expected=1, context={"addr7": "0x27"})

    assert "expected=1" in str(exc_info.value)


def test_require_open_raises():
    dev = make_driver_no_init()
    dev.handle = None

    with pytest.raises(DevasysI2CError):
        dev._require_open()
