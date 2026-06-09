import os
import sys
import ctypes
from ctypes import wintypes


class DevasysI2CError(Exception):
    pass


BYTE = ctypes.c_ubyte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong
LONG = ctypes.c_long
HANDLE = wintypes.HANDLE
BOOL = wintypes.BOOL


class I2C_TRANS(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("byTransType", BYTE),
        ("bySlvDevAddr", BYTE),
        ("wMemoryAddr", WORD),
        ("wCount", WORD),
        ("Data", BYTE * 256),
    ]


class DevasysUsbI2cIo:
    """
    Python driver for DeVaSys USB-I2C/IO board using UsbI2cIo.dll.

    Python address convention:
        Use normal 7-bit I2C addresses, for example:
            LCD PCF8574: 0x27
            MPU6050:     0x68

    The driver converts them to the 8-bit address format used by the DeVaSys API.
    """

    I2C_TRANS_NOADR = 0x00
    I2C_TRANS_8ADR = 0x01
    I2C_TRANS_16ADR = 0x02

    MAX_I2C_COUNT = 64

    DEVICE_NAME = b"UsbI2cIo"

    def __init__(self, dll_path="UsbI2cIo.dll", instance=0):
        if os.name != "nt":
            raise DevasysI2CError("This driver uses UsbI2cIo.dll and works on Windows only.")

        self.dll_path = dll_path
        self.instance = instance
        self.dll = self._load_dll(dll_path)
        self.handle = None

        self._setup_api()
        self.open(instance)

    def _load_dll(self, dll_path):
        dll_dir = os.path.dirname(os.path.abspath(dll_path))

        if dll_dir and os.path.exists(dll_dir) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dll_dir)

        try:
            return ctypes.WinDLL(dll_path)
        except OSError as exc:
            raise DevasysI2CError(
                f"Could not load {dll_path}. Put UsbI2cIo.dll beside this script "
                f"or pass full dll_path. Also check Python 32/64-bit matches the DLL."
            ) from exc

    def _setup_api(self):
        self.dll.DAPI_OpenDeviceInstance.argtypes = [ctypes.c_char_p, BYTE]
        self.dll.DAPI_OpenDeviceInstance.restype = HANDLE

        self.dll.DAPI_CloseDeviceInstance.argtypes = [HANDLE]
        self.dll.DAPI_CloseDeviceInstance.restype = BOOL

        self.dll.DAPI_ReadI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_ReadI2c.restype = LONG

        self.dll.DAPI_WriteI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_WriteI2c.restype = LONG

        # Optional digital IO functions
        self.dll.DAPI_ConfigIoPorts.argtypes = [HANDLE, DWORD]
        self.dll.DAPI_ConfigIoPorts.restype = LONG

        self.dll.DAPI_ReadIoPorts.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
        self.dll.DAPI_ReadIoPorts.restype = LONG

        self.dll.DAPI_WriteIoPorts.argtypes = [HANDLE, DWORD, DWORD]
        self.dll.DAPI_WriteIoPorts.restype = LONG

    def open(self, instance=0):
        handle = self.dll.DAPI_OpenDeviceInstance(self.DEVICE_NAME, BYTE(instance))

        invalid_handle = ctypes.c_void_p(-1).value
        if handle in (None, 0, invalid_handle):
            raise DevasysI2CError("DeVaSys USB-I2C/IO board not found or driver not installed.")

        self.handle = handle

    def close(self):
        if self.handle:
            self.dll.DAPI_CloseDeviceInstance(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @staticmethod
    def _check_addr7(addr7):
        if not 0x00 <= addr7 <= 0x7F:
            raise ValueError("I2C address must be 7-bit: 0x00 to 0x7F")

    @classmethod
    def _addr7_to_devasys(cls, addr7):
        cls._check_addr7(addr7)
        return (addr7 << 1) & 0xFE

    def _make_trans(self, trans_type, addr7, memory_addr=0, data=b"", count=None):
        data = bytes(data)

        if count is None:
            count = len(data)

        if count > self.MAX_I2C_COUNT:
            raise ValueError(f"Single DeVaSys I2C transaction max is {self.MAX_I2C_COUNT} bytes")

        if len(data) > 256:
            raise ValueError("I2C_TRANS data buffer max is 256 bytes")

        trans = I2C_TRANS()
        trans.byTransType = BYTE(trans_type)
        trans.bySlvDevAddr = BYTE(self._addr7_to_devasys(addr7))
        trans.wMemoryAddr = WORD(memory_addr)
        trans.wCount = WORD(count)

        for i, value in enumerate(data):
            trans.Data[i] = value

        return trans

    def write(self, addr7, data):
        """
        Raw I2C write without register address.

        Example:
            i2c.write(0x27, [0x00])
        """
        data = bytes(data)

        if len(data) == 0:
            raise ValueError("Use at least one byte for write(). Address-only scan is not reliable here.")

        trans = self._make_trans(
            trans_type=self.I2C_TRANS_NOADR,
            addr7=addr7,
            data=data,
            count=len(data),
        )

        result = self.dll.DAPI_WriteI2c(self.handle, ctypes.byref(trans))

        if result != len(data):
            raise DevasysI2CError(
                f"I2C write failed at 0x{addr7:02X}: wrote {result}, expected {len(data)}"
            )

        return result

    def read(self, addr7, count):
        """
        Raw I2C read without register address.
        """
        if count <= 0:
            return bytes()

        result_data = bytearray()
        remaining = count

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)

            trans = self._make_trans(
                trans_type=self.I2C_TRANS_NOADR,
                addr7=addr7,
                count=chunk,
            )

            result = self.dll.DAPI_ReadI2c(self.handle, ctypes.byref(trans))

            if result != chunk:
                raise DevasysI2CError(
                    f"I2C read failed at 0x{addr7:02X}: read {result}, expected {chunk}"
                )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk

        return bytes(result_data)

    def write_reg8(self, addr7, reg8, data):
        """
        Write to device using 8-bit register/memory address.

        Example:
            i2c.write_reg8(0x68, 0x6B, [0x00])
        """
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")

        data = bytes(data)

        trans = self._make_trans(
            trans_type=self.I2C_TRANS_8ADR,
            addr7=addr7,
            memory_addr=reg8,
            data=data,
            count=len(data),
        )

        result = self.dll.DAPI_WriteI2c(self.handle, ctypes.byref(trans))

        if result != len(data):
            raise DevasysI2CError(
                f"I2C write_reg8 failed at 0x{addr7:02X}, reg 0x{reg8:02X}: "
                f"wrote {result}, expected {len(data)}"
            )

        return result

    def read_reg8(self, addr7, reg8, count):
        """
        Read from device using 8-bit register/memory address.

        Example:
            who_am_i = i2c.read_reg8(0x68, 0x75, 1)
        """
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")

        result_data = bytearray()
        remaining = count
        current_reg = reg8

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)

            trans = self._make_trans(
                trans_type=self.I2C_TRANS_8ADR,
                addr7=addr7,
                memory_addr=current_reg,
                count=chunk,
            )

            result = self.dll.DAPI_ReadI2c(self.handle, ctypes.byref(trans))

            if result != chunk:
                raise DevasysI2CError(
                    f"I2C read_reg8 failed at 0x{addr7:02X}, reg 0x{current_reg:02X}: "
                    f"read {result}, expected {chunk}"
                )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFF

        return bytes(result_data)

    def write_reg16(self, addr7, reg16, data):
        """
        Write using 16-bit register/memory address, useful for EEPROM-like devices.
        """
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")

        data = bytes(data)

        trans = self._make_trans(
            trans_type=self.I2C_TRANS_16ADR,
            addr7=addr7,
            memory_addr=reg16,
            data=data,
            count=len(data),
        )

        result = self.dll.DAPI_WriteI2c(self.handle, ctypes.byref(trans))

        if result != len(data):
            raise DevasysI2CError(
                f"I2C write_reg16 failed at 0x{addr7:02X}, reg 0x{reg16:04X}: "
                f"wrote {result}, expected {len(data)}"
            )

        return result

    def read_reg16(self, addr7, reg16, count):
        """
        Read using 16-bit register/memory address, useful for EEPROM-like devices.
        """
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")

        result_data = bytearray()
        remaining = count
        current_reg = reg16

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)

            trans = self._make_trans(
                trans_type=self.I2C_TRANS_16ADR,
                addr7=addr7,
                memory_addr=current_reg,
                count=chunk,
            )

            result = self.dll.DAPI_ReadI2c(self.handle, ctypes.byref(trans))

            if result != chunk:
                raise DevasysI2CError(
                    f"I2C read_reg16 failed at 0x{addr7:02X}, reg 0x{current_reg:04X}: "
                    f"read {result}, expected {chunk}"
                )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFFFF

        return bytes(result_data)

    def scan(self, start=0x03, end=0x77):
        """
        Basic I2C scan.

        Note:
            This uses a 1-byte read test. It works for many devices,
            but it can miss write-only devices.
        """
        found = []

        for addr in range(start, end + 1):
            try:
                self.read(addr, 1)
                found.append(addr)
            except DevasysI2CError:
                pass

        return found

    # -------------------------
    # Optional digital IO access
    # -------------------------

    def config_io_ports(self, config_mask):
        """
        Configure DeVaSys digital IO direction mask.
        Meaning of bits depends on the DeVaSys board documentation.
        """
        return self.dll.DAPI_ConfigIoPorts(self.handle, DWORD(config_mask))

    def read_io_ports(self):
        value = DWORD(0)
        result = self.dll.DAPI_ReadIoPorts(self.handle, ctypes.byref(value))

        if result < 0:
            raise DevasysI2CError("DAPI_ReadIoPorts failed")

        return value.value

    def write_io_ports(self, data, mask=0xFFFFFFFF):
        result = self.dll.DAPI_WriteIoPorts(
            self.handle,
            DWORD(data),
            DWORD(mask),
        )

        if result < 0:
            raise DevasysI2CError("DAPI_WriteIoPorts failed")

        return result
class DevasysBlinkaI2C:
    """
    Blinka / CircuitPython-compatible I2C adapter for DevasysUsbI2cIo.

    This class provides a busio.I2C-like API:
        try_lock()
        unlock()
        scan()
        writeto()
        readfrom_into()
        writeto_then_readfrom()
        deinit()

    It allows many Adafruit CircuitPython drivers to use the DeVaSys USB-I2C/IO
    board as the I2C bus.
    """

    def __init__(
        self,
        dll_path="UsbI2cIo.dll",
        instance=0,
        frequency=None,
        allow_stop_fallback=True,
    ):
        """
        Parameters
        ----------
        dll_path:
            Path to UsbI2cIo.dll.

        instance:
            DeVaSys device instance number.

        frequency:
            Present only for Blinka compatibility.
            The DeVaSys DLL/board controls the actual bus speed.

        allow_stop_fallback:
            If True, unsupported generic write-then-read transactions are emulated
            as write-with-STOP followed by read. This is not a true repeated-start.
        """
        self._dev = DevasysUsbI2cIo(
            dll_path=dll_path,
            instance=instance,
        )
        self.frequency = frequency
        self._locked = False
        self._allow_stop_fallback = allow_stop_fallback

        # Used for old-style drivers that do:
        #   i2c.writeto(addr, data, stop=False)
        #   i2c.readfrom_into(addr, buf)
        self._pending_addr = None
        self._pending_write = None

    # ------------------------------------------------------------------
    # Context manager compatibility
    # ------------------------------------------------------------------

    def __enter__(self):
        while not self.try_lock():
            pass
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unlock()
        return False

    # ------------------------------------------------------------------
    # Blinka / CircuitPython-style lock API
    # ------------------------------------------------------------------

    def try_lock(self):
        """
        Try to lock the I2C bus.

        CircuitPython/Blinka drivers expect this method.
        """
        if self._locked:
            return False

        self._locked = True
        return True

    def unlock(self):
        """
        Unlock the I2C bus.
        """
        self._locked = False

    # ------------------------------------------------------------------
    # Blinka / CircuitPython-style bus API
    # ------------------------------------------------------------------

    def scan(self):
        """
        Return list of detected 7-bit I2C addresses.
        """
        try:
            return self._dev.scan()
        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def writeto(self, address, buffer, *, start=0, end=None, stop=True):
        """
        Write bytes to an I2C device.

        Blinka-compatible signature:
            writeto(address, buffer, *, start=0, end=None, stop=True)
        """
        if end is None:
            end = len(buffer)

        data = bytes(buffer[start:end])

        try:
            # Empty write is used by adafruit_bus_device.I2CDevice for probing.
            # DeVaSys raw write does not support zero-length write, so we probe
            # by trying to read one byte.
            if len(data) == 0:
                self._dev.read(address, 1)
                return None

            if stop:
                self._dev.write(address, data)
                return None

            # For stop=False, remember the write. The next readfrom_into()
            # will use writeto_then_readfrom().
            self._pending_addr = address
            self._pending_write = data
            return None

        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def readfrom_into(self, address, buffer, *, start=0, end=None):
        """
        Read bytes from an I2C device into an existing buffer.

        Blinka-compatible signature:
            readfrom_into(address, buffer, *, start=0, end=None)
        """
        if end is None:
            end = len(buffer)

        count = end - start

        if count < 0:
            raise ValueError("end must be greater than or equal to start")

        try:
            # Handle old-style repeated-start sequence:
            #   writeto(..., stop=False)
            #   readfrom_into(...)
            if self._pending_write is not None:
                if self._pending_addr != address:
                    raise OSError(
                        "Pending stop=False write address does not match read address"
                    )

                out_data = self._pending_write
                self._pending_write = None
                self._pending_addr = None

                data = self._write_then_read_compat(address, out_data, count)
            else:
                data = self._dev.read(address, count)

            for i, value in enumerate(data):
                buffer[start + i] = value

            return None

        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def writeto_then_readfrom(
        self,
        address,
        out_buffer,
        in_buffer,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
    ):
        """
        Write bytes, then immediately read bytes.

        Blinka-compatible signature:
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

        For most Adafruit sensors this is usually:
            write register address, then read register data.
        """
        if out_end is None:
            out_end = len(out_buffer)

        if in_end is None:
            in_end = len(in_buffer)

        out_data = bytes(out_buffer[out_start:out_end])
        read_count = in_end - in_start

        if read_count < 0:
            raise ValueError("in_end must be greater than or equal to in_start")

        try:
            data = self._write_then_read_compat(
                address,
                out_data,
                read_count,
            )

            for i, value in enumerate(data):
                in_buffer[in_start + i] = value

            return None

        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def deinit(self):
        """
        Close the DeVaSys device.
        """
        self._dev.close()

    # ------------------------------------------------------------------
    # Internal compatibility helper
    # ------------------------------------------------------------------

    def _write_then_read_compat(self, address, out_data, read_count):
        """
        Convert Blinka-style write-then-read into DeVaSys transactions.

        Supported directly:
            out_data length 0 -> raw read
            out_data length 1 -> 8-bit register read
            out_data length 2 -> 16-bit register read

        Fallback:
            out_data length > 2 -> write with STOP, then raw read
        """
        if read_count == 0:
            return bytes()

        if len(out_data) == 0:
            return self._dev.read(address, read_count)

        if len(out_data) == 1:
            reg8 = out_data[0]
            return self._dev.read_reg8(address, reg8, read_count)

        if len(out_data) == 2:
            reg16 = (out_data[0] << 8) | out_data[1]
            return self._dev.read_reg16(address, reg16, read_count)

        if self._allow_stop_fallback:
            self._dev.write(address, out_data)
            return self._dev.read(address, read_count)

        raise OSError(
            "Generic repeated-start transaction with more than 2 address bytes "
            "is not directly supported by this DeVaSys wrapper."
        )




if __name__ == "__main__":
    with DevasysUsbI2cIo() as i2c:
        print("Scanning I2C bus...")
        devices = i2c.scan()

        if devices:
            print("Found devices:")
            for addr in devices:
                print(f"  0x{addr:02X}")
        else:
            print("No I2C devices found.")