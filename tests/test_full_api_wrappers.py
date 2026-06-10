from devasys_usbi2cio.driver import DevasysUsbI2cIo


def test_all_header_wrapper_methods_exist():
    expected = [
        "dapi_get_dll_version",
        "dapi_get_driver_version",
        "dapi_get_firmware_version",
        "dapi_open_device_instance",
        "dapi_close_device_instance",
        "dapi_detect_device",
        "dapi_get_device_count",
        "dapi_get_device_info",
        "dapi_open_device_by_serial_id",
        "dapi_get_serial_id",
        "dapi_config_io_ports",
        "dapi_get_io_config",
        "dapi_read_io_ports",
        "dapi_write_io_ports",
        "dapi_block_write_io_ports",
        "dapi_block_read_io_ports",
        "dapi_read_i2c",
        "dapi_write_i2c",
        "dapi_read_debug_buffer",
        "dapi_write_fast_xfer_vr",
        "dapi_read_fast_xfer_vr",
        "dapi_transfer_data",
        "dapi_set_vendor_request",
        "dapi_get_vendor_request",
        "dapi_set_property",
        "dapi_get_property",
        "dapi_get_last_firmware_error",
        "dapi_enable_polling",
        "dapi_disable_polling",
        "dapi_get_polled_info",
    ]

    for name in expected:
        assert hasattr(DevasysUsbI2cIo, name), name


def test_all_header_transaction_constants_exist():
    assert DevasysUsbI2cIo.I2C_TRANS_NOADR == 0x00
    assert DevasysUsbI2cIo.I2C_TRANS_8ADR == 0x01
    assert DevasysUsbI2cIo.I2C_TRANS_16ADR == 0x02
    assert DevasysUsbI2cIo.I2C_TRANS_NOADR_NS == 0x03
    assert DevasysUsbI2cIo.I2C_TRANS_XICOR == 0x04
    assert DevasysUsbI2cIo.I2C_TRANS_8ADR_NONSEQ == 0x30
    assert DevasysUsbI2cIo.I2C_TRANS_16ADR_NONSEQ == 0x31
    assert DevasysUsbI2cIo.I2C_TRANS_24ADR_NONSEQ == 0x32
