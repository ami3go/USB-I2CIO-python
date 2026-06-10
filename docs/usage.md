# Usage Guide

## Low-Level Driver

```python
from devasys_usbi2cio import DevasysUsbI2cIo

with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    print([f"0x{x:02X}" for x in i2c.scan()])
```

## Raw Write

```python
i2c.write(0x27, [0x00])
```

## Raw Read

```python
data = i2c.read(0x50, 16)
```

## 8-bit Register Read

```python
who_am_i = i2c.read_reg8(0x68, 0x75, 1)
```

## 16-bit Register Read

```python
data = i2c.read_reg16(0x50, 0x0100, 16)
```

## Blinka-Compatible Adapter

```python
from devasys_usbi2cio import DevasysBlinkaI2C

i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")
try:
    print([f"0x{x:02X}" for x in i2c.scan()])
finally:
    i2c.deinit()
```
