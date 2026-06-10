# Installation

## Editable install for development

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Install with Blinka / Adafruit support

```bat
python -m pip install -e .[blinka]
```

## Test import

```bat
python -c "from devasys_usbi2cio import DevasysUsbI2cIo, DevasysBlinkaI2C; print('Import OK')"
```

## Run installed command

```bat
devasys-i2c-scan --dll UsbI2cIo.dll
```

## Normal local install

```bat
python -m pip install .
```

## Build wheel

```bat
python -m pip install build
python -m build
```

Then install from `dist`:

```bat
python -m pip install dist\devasys_usbi2cio-0.1.0-py3-none-any.whl
```

## Important

`UsbI2cIo.dll` is not included. Put it beside your script, in the current working directory, or pass the full path.
