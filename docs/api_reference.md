# API Reference

## `DevasysUsbI2cIo`

Low-level class for `UsbI2cIo.dll`.

### Constructor

```python
DevasysUsbI2cIo(dll_path="UsbI2cIo.dll", instance=0)
```

### Methods

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

config_io_ports(config_mask)
read_io_ports()
write_io_ports(data, mask=0xFFFFFFFF)
```

## `DevasysBlinkaI2C`

Blinka-compatible adapter.

### Constructor

```python
DevasysBlinkaI2C(
    dll_path="UsbI2cIo.dll",
    instance=0,
    frequency=None,
    allow_stop_fallback=True,
)
```

### Methods

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

## `DevasysI2CError`

Driver-specific exception.

Stores:

- `message`
- `function`
- `result`
- `context`
