# DeVaSys USB-I2C/IO Python Driver

Python driver and Blinka-compatible I2C adapter for the **DeVaSys USB-I2C/IO / USB-I2CCIO** board.

This package controls I2C devices from Windows using the DeVaSys vendor DLL:

```text
UsbI2cIo.dll
```

It provides two main classes:

- `DevasysUsbI2cIo` — low-level Python wrapper around `UsbI2cIo.dll`.
- `DevasysBlinkaI2C` — Blinka / CircuitPython-style I2C adapter compatible with many Adafruit I2C drivers.

---

## Features

- Windows support through `UsbI2cIo.dll`
- Normal 7-bit I2C address API
- Raw I2C write/read
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
- Clear exception class: `DevasysI2CError`
- Examples for scan, LCD 2004, and register-based sensors
- Unit tests for non-hardware logic

---

## Important Notes

Make sure:

- The DeVaSys Windows driver is installed.
- `UsbI2cIo.dll` is available in your script folder or passed by full path.
- Python architecture matches the DLL:
  - 32-bit DLL requires 32-bit Python.
  - 64-bit DLL requires 64-bit Python.
- I2C pull-up resistors are present.
- I2C voltage levels are safe for your device.

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/devasys-usbi2cio.git
cd devasys-usbi2cio
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Optional dependencies for Adafruit-style examples:

```bash
pip install adafruit-blinka adafruit-circuitpython-busdevice
```

---

## Basic I2C Scan

```python
from devasys_usbi2cio import DevasysUsbI2cIo

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    devices = i2c.scan()
    print([f"0x{x:02X}" for x in devices])
```

---

## Blinka-Compatible I2C Scan

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

## Adafruit `I2CDevice` Example

```python
from devasys_usbi2cio import DevasysBlinkaI2C
from adafruit_bus_device.i2c_device import I2CDevice

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")

try:
    device = I2CDevice(i2c, 0x68)
    result = bytearray(1)

    with device:
        device.write_then_readinto(bytes([0x75]), result)

    print(f"Register 0x75 = 0x{result[0]:02X}")
finally:
    i2c.deinit()
```

---

## LCD 2004 Example

Run:

```bash
python examples/lcd2004_pcf8574.py
```

Common LCD backpack addresses:

```text
0x27
0x3F
```

Common PCF8574 mapping:

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

---

## API Overview

### `DevasysUsbI2cIo`

```python
write(addr7, data)
read(addr7, count)

write_reg8(addr7, reg8, data)
read_reg8(addr7, reg8, count)

write_reg16(addr7, reg16, data)
read_reg16(addr7, reg16, count)

scan(start=0x03, end=0x77)

config_io_ports(config_mask)
read_io_ports()
write_io_ports(data, mask=0xFFFFFFFF)
```

### `DevasysBlinkaI2C`

```python
try_lock()
unlock()
scan()
writeto(address, buffer, *, start=0, end=None, stop=True)
readfrom_into(address, buffer, *, start=0, end=None)
writeto_then_readfrom(address, out_buffer, in_buffer, *, out_start=0, out_end=None, in_start=0, in_end=None)
deinit()
```

---

## Addressing

Use normal 7-bit I2C addresses:

```python
i2c.write(0x27, [0x00])
i2c.read_reg8(0x68, 0x75, 1)
```

The driver converts internally to the DeVaSys DLL format:

```python
devasys_address = (addr7 << 1) & 0xFE
```

---

## Limitations

This is not a full native Blinka backend.

This does **not** automatically use the DeVaSys board:

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

Other limitations:

- Windows-only because it uses `UsbI2cIo.dll`.
- I2C scan uses a one-byte read probe and may miss write-only devices.
- Generic repeated-start transactions longer than two address bytes may use STOP fallback.
- Digital IO bit meaning depends on DeVaSys board documentation.

---

## Tests

The included tests do not require hardware.

```bash
pip install -e . pytest
pytest
```

---

## Troubleshooting

See:

```text
docs/troubleshooting.md
```

---

## Status

Initial generated implementation. Hardware verification with a real DeVaSys board is still required before production use.
