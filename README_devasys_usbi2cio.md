# DeVaSys USB-I2C/IO Python Driver

Python driver and Blinka-compatible I2C adapter for the **DeVaSys USB-I2C/IO / USB-I2CCIO** board.

This project allows a Windows PC to control I2C devices using the DeVaSys USB-I2C/IO board and the vendor `UsbI2cIo.dll`.

It provides two main interfaces:

- `DevasysUsbI2cIo` — low-level Python wrapper around the DeVaSys DLL.
- `DevasysBlinkaI2C` — Blinka / CircuitPython-style adapter compatible with many Adafruit I2C drivers.

---

## Features

- Windows support through `UsbI2cIo.dll`
- Normal 7-bit I2C address API
- Raw I2C write
- Raw I2C read
- 8-bit register read/write
- 16-bit register read/write
- I2C bus scan
- Optional DeVaSys digital IO wrappers
- Blinka-compatible methods:
  - `try_lock()`
  - `unlock()`
  - `scan()`
  - `writeto()`
  - `readfrom_into()`
  - `writeto_then_readfrom()`
  - `deinit()`
- Custom error class with detailed DLL function context
- Example for LCD 2004 / HD44780 over PCF8574 I2C backpack

---

## Target Hardware

Tested / intended for:

- DeVaSys USB-I2C/IO
- DeVaSys USB-I2CCIO

Typical I2C devices:

- LCD 1602 / 2004 with PCF8574 backpack
- EEPROM devices
- Temperature sensors
- ADCs / DACs
- GPIO expanders
- Register-based I2C sensors

---

## Important Notes

This driver uses the vendor DLL:

```text
UsbI2cIo.dll
```

Make sure:

- The DLL is available in the project folder or passed by full path.
- The DeVaSys Windows driver is installed.
- Python architecture matches the DLL architecture:
  - 32-bit DLL → 32-bit Python
  - 64-bit DLL → 64-bit Python
- Your I2C bus has pull-up resistors.
- I2C voltage levels are compatible with your target device.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/devasys-usbi2cio.git
cd devasys-usbi2cio
```

Optional: create a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install package in editable mode:

```bash
pip install -e .
```

For Adafruit / Blinka-style examples:

```bash
pip install adafruit-blinka adafruit-circuitpython-busdevice
```

---

## Recommended Project Structure

```text
devasys-usbi2cio/
│
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
│
├── src/
│   └── devasys_usbi2cio/
│       ├── __init__.py
│       ├── driver.py
│       ├── blinka_adapter.py
│       ├── errors.py
│       └── types.py
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
    └── software_task.md
```

For a simple first version, a single-file driver is also acceptable:

```text
devasys_usbi2cio.py
```

---

## Quick Start: Low-Level I2C Scan

```python
from devasys_usbi2cio import DevasysUsbI2cIo

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    print("Scanning I2C bus...")
    devices = i2c.scan()

    if devices:
        print("Found devices:")
        for addr in devices:
            print(f"  0x{addr:02X}")
    else:
        print("No I2C devices found.")
```

Example output:

```text
Scanning I2C bus...
Found devices:
  0x27
```

---

## Quick Start: Blinka-Compatible I2C Scan

```python
import time
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")

try:
    while not i2c.try_lock():
        time.sleep(0.01)

    try:
        print("Scanning I2C bus...")
        devices = i2c.scan()
        print([f"0x{x:02X}" for x in devices])
    finally:
        i2c.unlock()

finally:
    i2c.deinit()
```

---

## Using with Adafruit `I2CDevice`

`DevasysBlinkaI2C` can be passed to many Adafruit CircuitPython drivers that accept an I2C bus object.

```python
from devasys_usbi2cio import DevasysBlinkaI2C
from adafruit_bus_device.i2c_device import I2CDevice

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")

device = I2CDevice(i2c, 0x68)

result = bytearray(1)

with device:
    device.write_then_readinto(
        bytes([0x75]),
        result,
    )

print(f"Register 0x75 = 0x{result[0]:02X}")

i2c.deinit()
```

---

## LCD 2004 / PCF8574 Example

Common I2C addresses for LCD backpacks:

```text
0x27
0x3F
```

Typical PCF8574 mapping:

| PCF8574 Pin | LCD Function |
|---|---|
| P0 | RS |
| P1 | RW |
| P2 | EN |
| P3 | Backlight |
| P4 | D4 |
| P5 | D5 |
| P6 | D6 |
| P7 | D7 |

Example usage:

```python
from devasys_usbi2cio import DevasysUsbI2cIo
from examples.lcd2004_pcf8574 import LCD2004_PCF8574

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    lcd = LCD2004_PCF8574(i2c, address=0x27)

    lcd.clear()
    lcd.write_line(0, "DeVaSys USB-I2C")
    lcd.write_line(1, "LCD 2004 test")
    lcd.write_line(2, "Address: 0x27")
    lcd.write_line(3, "Hello!")
```

---

## API Overview

## `DevasysUsbI2cIo`

Low-level class for direct access to the DeVaSys DLL.

```python
i2c = DevasysUsbI2cIo(
    dll_path="UsbI2cIo.dll",
    instance=0,
)
```

### Main methods

```python
open(instance=0)
close()

write(addr7, data)
read(addr7, count)

write_reg8(addr7, reg8, data)
read_reg8(addr7, reg8, count)

write_reg16(addr7, reg16, data)
read_reg16(addr7, reg16, count)

scan(start=0x03, end=0x77)
```

### Optional digital IO methods

```python
config_io_ports(config_mask)
read_io_ports()
write_io_ports(data, mask=0xFFFFFFFF)
```

---

## `DevasysBlinkaI2C`

Blinka / CircuitPython-compatible I2C adapter.

```python
i2c = DevasysBlinkaI2C(
    dll_path="UsbI2cIo.dll",
    instance=0,
    frequency=None,
    allow_stop_fallback=True,
)
```

### Main methods

```python
try_lock()
unlock()
scan()
writeto(address, buffer, *, start=0, end=None, stop=True)
readfrom_into(address, buffer, *, start=0, end=None)
writeto_then_readfrom(
    address,
    out_buffer,
    in_buffer,
    *,
    out_start=0,
    out_end=None,
    in_start=0,
    in_end=None,
)
deinit()
```

---

## Addressing Convention

This project uses normal **7-bit I2C addresses** in the public Python API.

Example:

```python
i2c.write(0x27, [0x00])
i2c.read_reg8(0x68, 0x75, 1)
```

Internally, the driver converts 7-bit addresses to the DeVaSys DLL address format:

```python
devasys_address = (addr7 << 1) & 0xFE
```

---

## Error Handling

All driver-specific errors are raised as:

```python
DevasysI2CError
```

Example:

```text
DAPI function returned unexpected byte count. |
function=DAPI_WriteI2c |
result=0 |
context: addr7=0x27, count=1, mode=raw_write, expected=1
```

The exception includes:

- Human-readable message
- DLL function name
- DLL result code
- Context dictionary

---

## Limitations

This project is a Python wrapper around the DeVaSys DLL. It is not a full native Blinka backend.

This will not automatically use the DeVaSys board:

```python
import board
import busio

i2c = busio.I2C(board.SCL, board.SDA)
```

Use this instead:

```python
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")
```

Other known limitations:

- Windows-only unless a compatible library is available for other operating systems.
- Generic repeated-start support depends on DLL behavior.
- Register-style reads with 1-byte and 2-byte register addresses are supported directly.
- More complex write-then-read transactions may use STOP fallback.
- I2C scan may miss write-only devices.
- Digital IO bit meaning depends on DeVaSys board documentation.

---

## Troubleshooting

## DLL not found

Check that:

- `UsbI2cIo.dll` is in the same folder as your script, or
- you passed the full DLL path:

```python
DevasysUsbI2cIo(dll_path=r"C:\Path\To\UsbI2cIo.dll")
```

---

## Wrong Python architecture

If the DLL fails to load, check Python architecture:

```bash
python -c "import platform; print(platform.architecture())"
```

Use 32-bit Python for a 32-bit DLL, or 64-bit Python for a 64-bit DLL.

---

## Device not found

Possible causes:

- DeVaSys board is not connected.
- Windows driver is not installed.
- Another program already opened the board.
- Wrong device instance number.
- USB cable problem.

---

## No I2C devices found

Possible causes:

- I2C target is not powered.
- SDA and SCL are swapped.
- Missing pull-up resistors.
- Wrong voltage level.
- Device address is different.
- Target device does not respond to read-based scan.

---

## LCD backlight works but no text

Possible causes:

- LCD contrast potentiometer is not adjusted.
- Wrong LCD I2C address.
- Different PCF8574 backpack pin mapping.
- LCD uses 5 V logic but I2C bus is not level-shifted correctly.

---

## Development

Run unit tests:

```bash
pytest
```

Run formatting:

```bash
black src tests examples
```

Run linting:

```bash
ruff check src tests examples
```

---

## Suggested `requirements.txt`

```text
adafruit-blinka
adafruit-circuitpython-busdevice
pytest
black
ruff
```

For minimal low-level usage, the Python standard library is enough because `ctypes` is built in.

---

## Roadmap

Planned / possible future improvements:

- Full package structure under `src/`
- Unit tests using a fake DLL object
- Hardware-in-the-loop test mode
- Better I2C scan probing
- Logging support
- PyPI package
- Full Blinka backend support
- Configurable I2C speed if supported by the DLL
- Diagnostic GUI tool
- More example drivers

---

## License

Choose a license before publishing the project.

Recommended options:

- MIT License for simple open-source reuse.
- Apache-2.0 if patent protection language is desired.
- Private/proprietary license if this is for internal company use.

---

## Status

Initial development / prototype stage.

Hardware verification is required before using this package in production test systems.
