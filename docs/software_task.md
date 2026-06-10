# Software Task Specification: DeVaSys USB-I2C/IO Python Driver with Blinka-Compatible Adapter

**Project name:** `devasys-usbi2cio`  
**Target hardware:** DeVaSys USB-I2C/IO / USB-I2CCIO board  
**Target OS:** Windows  
**Main language:** Python 3.x  
**Driver interface:** Vendor DLL `UsbI2cIo.dll` through `ctypes`  
**Document version:** 1.0  
**Date:** 2026-06-09  

---

## 1. Goal

Create a production-quality Python package for controlling the DeVaSys USB-I2C/IO board from Python.

The package shall provide two main classes:

1. `DevasysUsbI2cIo`  
   Low-level Python driver that wraps the DeVaSys `UsbI2cIo.dll` API.

2. `DevasysBlinkaI2C`  
   Blinka / CircuitPython-compatible I2C adapter that exposes a `busio.I2C`-like API and allows many Adafruit CircuitPython I2C drivers to work with the DeVaSys USB-I2C/IO board.

The package shall also include examples, tests, error handling, and documentation.

---

## 2. Scope

### 2.1 In Scope

The software shall support:

- Opening and closing the DeVaSys USB-I2C/IO board.
- Selecting DeVaSys device instance number.
- Raw I2C write transactions.
- Raw I2C read transactions.
- 8-bit register write.
- 8-bit register read.
- 16-bit register write.
- 16-bit register read.
- I2C bus scan.
- Optional digital IO wrappers, if supported by the DLL:
  - Configure IO ports.
  - Read IO ports.
  - Write IO ports.
- Blinka-compatible methods:
  - `try_lock()`
  - `unlock()`
  - `scan()`
  - `writeto()`
  - `readfrom_into()`
  - `writeto_then_readfrom()`
  - `deinit()`
- Example for I2C scan.
- Example for LCD 2004 / 20x4 HD44780 over PCF8574 I2C backpack.
- Example for register-based sensor access.
- Clear errors using custom exception `DevasysI2CError`.

### 2.2 Out of Scope

The first implementation does not need to provide:

- A full official Blinka backend integrated into `board` and `busio`.
- Linux support, unless DeVaSys provides a compatible shared library.
- Advanced I2C speed configuration, unless supported and documented by the DLL.
- SPI, UART, or other non-I2C protocols.
- Async API.
- GUI.
- Packaging for PyPI, unless requested later.

---

## 3. Target Users

The target users are:

- Test engineers.
- Electronics developers.
- Python automation users.
- Users who want to control I2C devices from a PC.
- Users who want to reuse Adafruit CircuitPython I2C drivers without using Raspberry Pi, FT232H, MCP2221A, or RP2040 U2IF.

---

## 4. Hardware Assumptions

The driver assumes:

- DeVaSys USB-I2C/IO or USB-I2CCIO board is connected through USB.
- DeVaSys Windows driver is installed.
- `UsbI2cIo.dll` is available.
- DLL architecture matches Python architecture:
  - 32-bit DLL requires 32-bit Python.
  - 64-bit DLL requires 64-bit Python.
- I2C pull-up resistors are available on the target bus.
- I2C voltage level is compatible with the connected devices.

---

## 5. Repository Structure

Recommended repository structure:

```text
devasys-usbi2cio/
│
├── README.md
├── requirements.txt
├── pyproject.toml                 # optional
├── LICENSE
│
├── src/
│   └── devasys_usbi2cio/
│       ├── __init__.py
│       ├── driver.py              # DevasysUsbI2cIo low-level class
│       ├── blinka_adapter.py      # DevasysBlinkaI2C class
│       ├── errors.py              # DevasysI2CError
│       └── types.py               # ctypes structures and aliases
│
├── examples/
│   ├── scan_i2c.py
│   ├── scan_blinka_i2c.py
│   ├── lcd2004_pcf8574.py
│   └── read_register_sensor.py
│
├── tests/
│   ├── test_address_conversion.py
│   ├── test_transaction_struct.py
│   ├── test_blinka_adapter.py
│   └── test_error_handling.py
│
└── docs/
    ├── usage.md
    ├── troubleshooting.md
    └── api_reference.md
```

For a simple single-file prototype, it is acceptable to keep everything in:

```text
devasys_usbi2cio.py
```

However, the production version should use the structured layout above.

---

## 6. Public API Requirements

## 6.1 `DevasysI2CError`

Create a custom exception class for all DeVaSys-related driver errors.

### Required behavior

The exception shall store:

- Human-readable message.
- DLL function name, if applicable.
- DLL result code, if applicable.
- Context dictionary with useful debug information.

### Required constructor

```python
class DevasysI2CError(Exception):
    def __init__(
        self,
        message: str,
        function: str | None = None,
        result: int | None = None,
        context: dict | None = None,
    ):
        ...
```

### Example error message

```text
DAPI function returned unexpected byte count. |
function=DAPI_WriteI2c |
result=0 |
context: addr7=0x27, count=1, mode=raw_write, expected=1
```

---

## 6.2 `DevasysUsbI2cIo`

Low-level driver class.

### Constructor

```python
class DevasysUsbI2cIo:
    def __init__(
        self,
        dll_path: str = "UsbI2cIo.dll",
        instance: int = 0,
    ):
        ...
```

### Constructor requirements

The constructor shall:

- Validate that the operating system is Windows.
- Load `UsbI2cIo.dll` using `ctypes.WinDLL`.
- Configure DLL function signatures.
- Open the selected DeVaSys device instance.
- Store the device handle.

### Context manager support

The class shall support:

```python
with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    devices = i2c.scan()
```

Required methods:

```python
def __enter__(self): ...
def __exit__(self, exc_type, exc_value, traceback): ...
```

---

## 7. Low-Level DLL Wrapper Requirements

All direct DLL calls shall be hidden behind wrapper methods.

### Required wrapper methods

```python
def dapi_open_device_instance(self, device_name: bytes, instance: int): ...
def dapi_close_device_instance(self): ...
def dapi_read_i2c(self, trans, expected_count: int | None = None, context: dict | None = None): ...
def dapi_write_i2c(self, trans, expected_count: int | None = None, context: dict | None = None): ...
def dapi_config_io_ports(self, config_mask: int): ...
def dapi_read_io_ports(self) -> int: ...
def dapi_write_io_ports(self, data: int, mask: int = 0xFFFFFFFF): ...
```

### Internal helper methods

```python
def _load_dll(self, dll_path: str): ...
def _setup_api(self): ...
def _require_open(self): ...
def _call_dapi(self, function_name: str, *args, context: dict | None = None): ...
def _check_result_non_negative(self, function_name: str, result: int, context: dict | None = None): ...
def _check_result_exact(self, function_name: str, result: int, expected: int, context: dict | None = None): ...
```

### Error handling rules

- Missing DLL shall raise `DevasysI2CError`.
- Missing DLL function shall raise `DevasysI2CError`.
- Invalid handle shall raise `DevasysI2CError`.
- Negative DLL result shall raise `DevasysI2CError`.
- Unexpected I2C byte count shall raise `DevasysI2CError`.
- The error context shall include address, register, byte count, and transaction mode where applicable.

---

## 8. I2C Addressing Requirements

The public Python API shall use normal 7-bit I2C addresses.

Example:

```python
i2c.write(0x27, [0x00])
i2c.read_reg8(0x68, 0x75, 1)
```

Internally, the driver shall convert to DeVaSys 8-bit address format:

```python
devasys_address = (addr7 << 1) & 0xFE
```

### Required validation

```python
0x00 <= addr7 <= 0x7F
```

Invalid addresses shall raise `ValueError`.

---

## 9. I2C Transaction Structure

Implement the DeVaSys I2C transaction structure using `ctypes`.

```python
class I2C_TRANS(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("byTransType", BYTE),
        ("bySlvDevAddr", BYTE),
        ("wMemoryAddr", WORD),
        ("wCount", WORD),
        ("Data", BYTE * 256),
    ]
```

### Transaction types

The driver shall define:

```python
I2C_TRANS_NOADR = 0x00
I2C_TRANS_8ADR  = 0x01
I2C_TRANS_16ADR = 0x02
```

### Transfer size

The driver shall define:

```python
MAX_I2C_COUNT = 64
```

If the user requests a read longer than `MAX_I2C_COUNT`, the driver shall split it into multiple transactions.

---

## 10. `DevasysUsbI2cIo` Public I2C Methods

## 10.1 `write`

```python
def write(self, addr7: int, data: bytes | bytearray | list[int]) -> int:
    ...
```

### Behavior

- Sends raw I2C write without register address.
- Requires at least one byte.
- Uses transaction type `I2C_TRANS_NOADR`.
- Returns number of bytes written.
- Raises `DevasysI2CError` on failure.

### Example

```python
i2c.write(0x27, [0x00])
```

---

## 10.2 `read`

```python
def read(self, addr7: int, count: int) -> bytes:
    ...
```

### Behavior

- Performs raw I2C read without register address.
- Returns `bytes`.
- If `count <= 0`, returns empty `bytes`.
- Splits long reads into chunks of `MAX_I2C_COUNT`.

### Example

```python
data = i2c.read(0x50, 16)
```

---

## 10.3 `write_reg8`

```python
def write_reg8(self, addr7: int, reg8: int, data: bytes | bytearray | list[int]) -> int:
    ...
```

### Behavior

- Writes data to an 8-bit register address.
- Register shall be in range `0x00` to `0xFF`.
- Uses transaction type `I2C_TRANS_8ADR`.

### Example

```python
i2c.write_reg8(0x68, 0x6B, [0x00])
```

---

## 10.4 `read_reg8`

```python
def read_reg8(self, addr7: int, reg8: int, count: int) -> bytes:
    ...
```

### Behavior

- Reads data from an 8-bit register address.
- Register shall be in range `0x00` to `0xFF`.
- Uses transaction type `I2C_TRANS_8ADR`.
- Splits long reads into chunks.
- Register address shall auto-increment between chunks.

### Example

```python
who_am_i = i2c.read_reg8(0x68, 0x75, 1)
```

---

## 10.5 `write_reg16`

```python
def write_reg16(self, addr7: int, reg16: int, data: bytes | bytearray | list[int]) -> int:
    ...
```

### Behavior

- Writes data to a 16-bit register or memory address.
- Register shall be in range `0x0000` to `0xFFFF`.
- Uses transaction type `I2C_TRANS_16ADR`.

### Example

```python
i2c.write_reg16(0x50, 0x0100, [0x12, 0x34])
```

---

## 10.6 `read_reg16`

```python
def read_reg16(self, addr7: int, reg16: int, count: int) -> bytes:
    ...
```

### Behavior

- Reads data from a 16-bit register or memory address.
- Register shall be in range `0x0000` to `0xFFFF`.
- Uses transaction type `I2C_TRANS_16ADR`.
- Splits long reads into chunks.
- Register address shall auto-increment between chunks.

### Example

```python
data = i2c.read_reg16(0x50, 0x0100, 16)
```

---

## 10.7 `scan`

```python
def scan(self, start: int = 0x03, end: int = 0x77) -> list[int]:
    ...
```

### Behavior

- Scans I2C address range.
- Returns list of 7-bit addresses.
- Default scan range shall be `0x03` to `0x77`.
- Scan can use 1-byte read probing.
- Failed addresses shall be ignored.
- The scan method shall not stop the full scan if one address fails.

### Note

Some write-only devices may not respond correctly to read-based probing. This limitation shall be documented.

---

## 11. Optional Digital IO API

If the DLL exposes digital IO functions, provide these public methods:

```python
def config_io_ports(self, config_mask: int): ...
def read_io_ports(self) -> int: ...
def write_io_ports(self, data: int, mask: int = 0xFFFFFFFF): ...
```

The exact meaning of IO port bits depends on the DeVaSys board documentation and shall be documented separately if available.

---

## 12. Blinka-Compatible Adapter: `DevasysBlinkaI2C`

## 12.1 Goal

Create an adapter class that allows DeVaSys USB-I2C/IO to be passed directly to many Adafruit CircuitPython drivers.

The adapter shall mimic the important parts of the `busio.I2C` API.

### Constructor

```python
class DevasysBlinkaI2C:
    def __init__(
        self,
        dll_path: str = "UsbI2cIo.dll",
        instance: int = 0,
        frequency: int | None = None,
        allow_stop_fallback: bool = True,
    ):
        ...
```

### Constructor behavior

- Create an internal `DevasysUsbI2cIo` instance.
- Store `frequency` for compatibility only.
- Implement software lock state.
- Store `allow_stop_fallback`.

---

## 12.2 Locking API

### `try_lock`

```python
def try_lock(self) -> bool:
    ...
```

Behavior:

- If bus is unlocked, lock it and return `True`.
- If already locked, return `False`.

### `unlock`

```python
def unlock(self) -> None:
    ...
```

Behavior:

- Unlock the bus.
- Should not raise if already unlocked.

---

## 12.3 Blinka I2C Methods

### `scan`

```python
def scan(self) -> list[int]:
    ...
```

Behavior:

- Call internal `DevasysUsbI2cIo.scan()`.
- Convert `DevasysI2CError` to `OSError` for Blinka compatibility.

---

### `writeto`

```python
def writeto(
    self,
    address: int,
    buffer,
    *,
    start: int = 0,
    end: int | None = None,
    stop: bool = True,
) -> None:
    ...
```

Behavior:

- Slice input buffer using `start` and `end`.
- If buffer length is zero, perform a safe probe operation.
- If `stop=True`, perform normal raw write.
- If `stop=False`, store the write data internally as a pending transaction.
- Convert `DevasysI2CError` to `OSError`.

---

### `readfrom_into`

```python
def readfrom_into(
    self,
    address: int,
    buffer,
    *,
    start: int = 0,
    end: int | None = None,
) -> None:
    ...
```

Behavior:

- Read bytes into existing mutable buffer.
- Slice output using `start` and `end`.
- If a previous `writeto(..., stop=False)` exists, complete it using write-then-read compatibility logic.
- Convert `DevasysI2CError` to `OSError`.

---

### `writeto_then_readfrom`

```python
def writeto_then_readfrom(
    self,
    address: int,
    out_buffer,
    in_buffer,
    *,
    out_start: int = 0,
    out_end: int | None = None,
    in_start: int = 0,
    in_end: int | None = None,
) -> None:
    ...
```

Behavior:

- Slice output and input buffers.
- Use internal compatibility helper to implement write-then-read.
- Fill `in_buffer`.
- Convert `DevasysI2CError` to `OSError`.

---

### `deinit`

```python
def deinit(self) -> None:
    ...
```

Behavior:

- Close the underlying DeVaSys device.
- Safe to call during cleanup.

---

## 13. Blinka Write-Then-Read Compatibility Logic

Implement internal helper:

```python
def _write_then_read_compat(
    self,
    address: int,
    out_data: bytes,
    read_count: int,
) -> bytes:
    ...
```

### Required behavior

| `out_data` length | Behavior |
|---:|---|
| 0 | Raw read using `DevasysUsbI2cIo.read()` |
| 1 | 8-bit register read using `DevasysUsbI2cIo.read_reg8()` |
| 2 | 16-bit register read using `DevasysUsbI2cIo.read_reg16()` |
| >2 | If `allow_stop_fallback=True`, do raw write with STOP, then raw read |
| >2 | If `allow_stop_fallback=False`, raise `OSError` |

### Important limitation

Generic repeated-start transactions with more than two address bytes are not guaranteed to be true repeated-start transactions. This limitation shall be clearly documented.

---

## 14. Examples Required

## 14.1 Basic DeVaSys I2C Scan

File:

```text
examples/scan_i2c.py
```

Expected example:

```python
from devasys_usbi2cio import DevasysUsbI2cIo

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    devices = i2c.scan()
    print([f"0x{x:02X}" for x in devices])
```

---

## 14.2 Blinka-Compatible I2C Scan

File:

```text
examples/scan_blinka_i2c.py
```

Expected example:

```python
import time
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")

try:
    while not i2c.try_lock():
        time.sleep(0.01)

    try:
        devices = i2c.scan()
        print([f"0x{x:02X}" for x in devices])
    finally:
        i2c.unlock()
finally:
    i2c.deinit()
```

---

## 14.3 LCD 2004 / PCF8574 Example

File:

```text
examples/lcd2004_pcf8574.py
```

Required features:

- Initialize HD44780 LCD in 4-bit mode.
- Support common PCF8574 mapping:
  - P0 = RS
  - P1 = RW
  - P2 = EN
  - P3 = Backlight
  - P4 = D4
  - P5 = D5
  - P6 = D6
  - P7 = D7
- Support 20 columns and 4 rows.
- Support:
  - Clear display.
  - Home.
  - Set cursor.
  - Write text.
  - Write full line.
  - Backlight on/off.
- Use common addresses:
  - `0x27`
  - `0x3F`

---

## 14.4 Register-Based Sensor Example

File:

```text
examples/read_register_sensor.py
```

Required behavior:

- Use `DevasysBlinkaI2C`.
- Use `adafruit_bus_device.i2c_device.I2CDevice`.
- Demonstrate read of a register such as `0x75` from a device at `0x68`.

---

## 15. Tests Required

## 15.1 Unit Tests Without Hardware

Tests shall not require physical DeVaSys hardware.

Use mocks or fake DLL objects.

### Required test areas

- 7-bit to DeVaSys address conversion.
- Invalid I2C address handling.
- `I2C_TRANS` field layout.
- Raw write transaction creation.
- Raw read chunking.
- 8-bit register read transaction.
- 16-bit register read transaction.
- Error when DLL function returns negative value.
- Error when I2C byte count is unexpected.
- `DevasysBlinkaI2C.try_lock()` behavior.
- `DevasysBlinkaI2C.unlock()` behavior.
- `writeto()` buffer slicing.
- `readfrom_into()` buffer slicing.
- `writeto_then_readfrom()` behavior for:
  - 0-byte out buffer.
  - 1-byte out buffer.
  - 2-byte out buffer.
  - More than 2-byte out buffer with fallback enabled.
  - More than 2-byte out buffer with fallback disabled.

---

## 16. Documentation Requirements

## 16.1 README

The README shall include:

- What the package does.
- Supported hardware.
- Windows-only limitation.
- DLL requirement.
- 32-bit / 64-bit Python note.
- Basic installation.
- Basic I2C scan example.
- Blinka adapter example.
- LCD 2004 example.
- Troubleshooting section.

---

## 16.2 Troubleshooting

Include common issues:

### DLL not found

Possible causes:

- `UsbI2cIo.dll` is not in the script folder.
- Full path not provided.
- DLL dependency missing.

### Wrong Python architecture

Possible causes:

- 32-bit DLL used with 64-bit Python.
- 64-bit DLL used with 32-bit Python.

### Device not found

Possible causes:

- DeVaSys board not connected.
- Driver not installed.
- Wrong instance number.
- Device already open by another application.

### No I2C devices found

Possible causes:

- Missing pull-up resistors.
- Wrong voltage level.
- Device not powered.
- SDA/SCL reversed.
- Address is different.
- Read-based scan does not detect write-only devices.

### LCD lights but no text

Possible causes:

- Contrast potentiometer not adjusted.
- Wrong I2C address.
- Different PCF8574 pin mapping.
- LCD not initialized correctly.
- 5 V LCD used with incompatible I2C voltage.

---

## 17. Coding Style Requirements

The code shall:

- Use clear class and method names.
- Include docstrings for all public classes and methods.
- Use type hints where practical.
- Avoid global mutable state.
- Avoid hard-coded absolute paths.
- Keep hardware-specific constants in one place.
- Convert low-level driver errors to useful high-level errors.
- Keep Blinka adapter separate from low-level DLL wrapper.
- Be compatible with Python 3.9 or newer.

---

## 18. Safety and Reliability Requirements

The software shall:

- Always close the USB device when `deinit()` or `close()` is called.
- Support context manager cleanup.
- Avoid leaving pending `stop=False` state after a failed read.
- Raise clear exceptions instead of silent failure.
- Never crash Python due to unhandled DLL access if recoverable.
- Validate input ranges before calling the DLL.
- Avoid sending unexpected empty writes unless intentionally used as a probe.
- Clearly document limitations of scan and repeated-start emulation.

---

## 19. Acceptance Criteria

The task is complete when:

1. `DevasysUsbI2cIo` can open and close the board.
2. `DevasysUsbI2cIo.scan()` returns detected 7-bit I2C addresses.
3. `DevasysUsbI2cIo.write()` can write one or more bytes to an I2C device.
4. `DevasysUsbI2cIo.read()` can read one or more bytes from an I2C device.
5. `read_reg8()` and `write_reg8()` work with register-based devices.
6. `read_reg16()` and `write_reg16()` work with EEPROM-style devices.
7. All DLL functions are wrapped with error handling.
8. `DevasysI2CError` reports useful function, result, and context information.
9. `DevasysBlinkaI2C` provides:
   - `try_lock`
   - `unlock`
   - `scan`
   - `writeto`
   - `readfrom_into`
   - `writeto_then_readfrom`
   - `deinit`
10. Basic Adafruit `I2CDevice` usage works with `DevasysBlinkaI2C`.
11. LCD 2004 PCF8574 example can write text to all four rows.
12. Unit tests for non-hardware logic pass.
13. README and troubleshooting documentation are complete.

---

## 20. Recommended Implementation Order

1. Create project structure.
2. Implement `DevasysI2CError`.
3. Implement `I2C_TRANS` ctypes structure.
4. Implement DLL loading.
5. Implement DLL function signature setup.
6. Implement direct DAPI wrappers.
7. Implement open/close/context manager.
8. Implement raw I2C write/read.
9. Implement 8-bit register read/write.
10. Implement 16-bit register read/write.
11. Implement scan.
12. Implement optional digital IO wrappers.
13. Implement `DevasysBlinkaI2C`.
14. Implement examples.
15. Implement unit tests with mocked DLL.
16. Write README and troubleshooting docs.
17. Run hardware verification on real DeVaSys board.
18. Fix compatibility issues discovered during hardware testing.

---

## 21. Hardware Verification Checklist

Use this checklist during real hardware testing.

### Setup

- [ ] DeVaSys board connected to PC.
- [ ] Windows driver installed.
- [ ] `UsbI2cIo.dll` available.
- [ ] Python architecture matches DLL.
- [ ] I2C target device powered.
- [ ] SDA/SCL correctly connected.
- [ ] Pull-up resistors present.
- [ ] Common ground connected.

### Tests

- [ ] Driver opens board.
- [ ] Driver closes board.
- [ ] Scan finds known device.
- [ ] LCD backpack found at `0x27` or `0x3F`.
- [ ] LCD clear command works.
- [ ] LCD text write works.
- [ ] Register read works on known sensor.
- [ ] Invalid address raises `ValueError`.
- [ ] Disconnected device raises clear `DevasysI2CError`.
- [ ] Blinka scan example works.
- [ ] Adafruit `I2CDevice` example works.

---

## 22. Known Limitations to Document

- This is not a full native Blinka backend.
- User must instantiate `DevasysBlinkaI2C` manually.
- Code like this will not automatically use the DeVaSys board:

```python
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA)
```

Instead, users shall use:

```python
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")
```

- Generic repeated-start behavior depends on what the DLL supports.
- Register-style reads are supported directly for 1-byte and 2-byte register address writes.
- More complex transactions may use STOP fallback and may not work with every device.
- I2C scan may miss write-only devices.
- Digital IO bit behavior depends on DeVaSys documentation.

---

## 23. Future Enhancements

Possible future improvements:

- Full Blinka backend integration.
- Configurable I2C speed, if supported by DLL.
- More accurate scan mode using address-only probe, if supported.
- Logging support.
- Type-stub file `py.typed`.
- PyPI package.
- CI unit tests.
- Hardware-in-the-loop test mode.
- Support for multiple DeVaSys boards.
- Device discovery helper.
- LCD support as reusable driver class.
- Optional GUI diagnostic tool.

---

## 24. Minimal Usage Example

```python
from devasys_usbi2cio import DevasysUsbI2cIo

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    print("Scanning...")
    devices = i2c.scan()
    print([f"0x{x:02X}" for x in devices])
```

---

## 25. Minimal Blinka-Compatible Usage Example

```python
import time
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")

try:
    while not i2c.try_lock():
        time.sleep(0.01)

    try:
        devices = i2c.scan()
        print([f"0x{x:02X}" for x in devices])
    finally:
        i2c.unlock()
finally:
    i2c.deinit()
```

---

## 26. Definition of Done

The software task is done when the package is cleanly structured, documented, tested without hardware where possible, and verified on real DeVaSys USB-I2C/IO hardware with at least:

- One I2C scan.
- One raw I2C write.
- One raw I2C read.
- One 8-bit register read.
- One LCD 2004 text output test.
- One Blinka-compatible `I2CDevice` example.
