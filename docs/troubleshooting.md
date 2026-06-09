# Troubleshooting

## DLL not found

Check that `UsbI2cIo.dll` is in the working directory, beside your script, or passed by full path:

```python
DevasysUsbI2cIo(dll_path=r"C:\Path\To\UsbI2cIo.dll")
```

## Wrong Python architecture

A 32-bit DLL requires 32-bit Python. A 64-bit DLL requires 64-bit Python.

Check Python architecture:

```bash
python -c "import platform; print(platform.architecture())"
```

## Device not found

Possible causes:

- DeVaSys board is not connected.
- DeVaSys Windows driver is not installed.
- Another program already opened the board.
- Wrong instance number.
- Bad USB cable.

## No I2C devices found

Possible causes:

- I2C target is not powered.
- SDA and SCL are swapped.
- Missing pull-up resistors.
- Wrong I2C voltage level.
- Device address is different.
- Target does not respond to a read-based scan.

## LCD backlight works but no text

Possible causes:

- Contrast potentiometer not adjusted.
- Wrong I2C address.
- Different PCF8574 backpack pin mapping.
- LCD not initialized correctly.
- 5 V LCD backpack used without proper level shifting.

## Blinka driver does not work

This package is not a full Blinka backend. Do not use:

```python
import board
import busio
i2c = busio.I2C(board.SCL, board.SDA)
```

Use:

```python
from devasys_usbi2cio import DevasysBlinkaI2C
i2c = DevasysBlinkaI2C(dll_path="UsbI2cIo.dll")
```

Then pass `i2c` directly to the driver.
