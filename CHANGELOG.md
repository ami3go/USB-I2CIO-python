# Changelog

## 0.2.0

- Fixed `I2C_TRANS.Data` size to 1088 bytes to match `Usbi2cio.h`.
- Changed `MAX_I2C_COUNT` to 1088 bytes.
- Added header-derived constants and enums:
  - `I2cTransType`
  - `IoMode`
  - `PropertyOffset`
  - `PropertyCommand`
- Corrected GPIO / I/O function signatures from `LONG` to `BOOL` where required.
- Added wrappers for all exported `DAPI_*` functions listed in `Usbi2cio.h`.
- Added wrappers for:
  - version functions
  - device count/info/serial functions
  - block I/O functions
  - debug buffer
  - fast transfer
  - generic USB transfer
  - vendor request
  - property access
  - firmware error
  - polling calls
- Kept and updated `DevasysBlinkaI2C`.
- Added `write_no_stop()` using `I2C_TRANS_NOADR_NS`.
- Added tests for full API wrapper presence and corrected structure size.

## 0.1.0

- Initial generated driver package.
