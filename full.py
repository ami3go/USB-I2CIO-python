import os
import ctypes
from ctypes import wintypes


BYTE = ctypes.c_ubyte
WORD = ctypes.c_ushort
DWORD = ctypes.c_ulong
LONG = ctypes.c_long
HANDLE = wintypes.HANDLE
BOOL = wintypes.BOOL


class DevasysI2CError(Exception):
    """
    Common exception for all DeVaSys USB-I2C/IO driver errors.
    """

    def __init__(self, message, function=None, result=None, context=None):
        self.message = message
        self.function = function
        self.result = result
        self.context = context or {}

        parts = [message]

        if function:
            parts.append(f"function={function}")

        if result is not None:
            parts.append(f"result={result}")

        if context:
            ctx = ", ".join(f"{k}={v}" for k, v in context.items())
            parts.append(f"context: {ctx}")

        super().__init__(" | ".join(parts))


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
    Python wrapper for DeVaSys USB-I2C/IO using UsbI2cIo.dll.

    Public functions use normal 7-bit I2C addresses:
        0x27 for LCD backpack
        0x68 for MPU6050
        0x50 for EEPROM
    """

    DEVICE_NAME = b"UsbI2cIo"

    I2C_TRANS_NOADR = 0x00
    I2C_TRANS_8ADR = 0x01
    I2C_TRANS_16ADR = 0x02

    MAX_I2C_COUNT = 64

    def __init__(self, dll_path="UsbI2cIo.dll", instance=0):
        if os.name != "nt":
            raise DevasysI2CError(
                "UsbI2cIo.dll driver works on Windows only."
            )

        self.dll_path = dll_path
        self.instance = instance
        self.handle = None

        self.dll = self._load_dll(dll_path)
        self._setup_api()
        self.open(instance)

    # ------------------------------------------------------------------
    # DLL loading and API setup
    # ------------------------------------------------------------------

    def _load_dll(self, dll_path):
        dll_dir = os.path.dirname(os.path.abspath(dll_path))

        if dll_dir and os.path.exists(dll_dir) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dll_dir)

        try:
            return ctypes.WinDLL(dll_path)
        except OSError as exc:
            raise DevasysI2CError(
                "Could not load UsbI2cIo.dll. Put the DLL beside this script "
                "or pass the full dll_path. Also check 32-bit/64-bit Python "
                "matches the DLL.",
                function="WinDLL",
                context={"dll_path": dll_path},
            ) from exc

    def _setup_api(self):
        """
        Define argument and return types for all DAPI functions used by this driver.
        """

        self.dll.DAPI_OpenDeviceInstance.argtypes = [ctypes.c_char_p, BYTE]
        self.dll.DAPI_OpenDeviceInstance.restype = HANDLE

        self.dll.DAPI_CloseDeviceInstance.argtypes = [HANDLE]
        self.dll.DAPI_CloseDeviceInstance.restype = BOOL

        self.dll.DAPI_ReadI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_ReadI2c.restype = LONG

        self.dll.DAPI_WriteI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_WriteI2c.restype = LONG

        self.dll.DAPI_ConfigIoPorts.argtypes = [HANDLE, DWORD]
        self.dll.DAPI_ConfigIoPorts.restype = LONG

        self.dll.DAPI_ReadIoPorts.argtypes = [HANDLE, ctypes.POINTER(DWORD)]
        self.dll.DAPI_ReadIoPorts.restype = LONG

        self.dll.DAPI_WriteIoPorts.argtypes = [HANDLE, DWORD, DWORD]
        self.dll.DAPI_WriteIoPorts.restype = LONG

    # ------------------------------------------------------------------
    # Generic DLL-call wrappers
    # ------------------------------------------------------------------

    def _require_open(self):
        if not self.handle:
            raise DevasysI2CError("Device is not open.")

    def _call_dapi(self, function_name, *args, context=None):
        """
        Generic wrapper for all DAPI DLL function calls.

        It converts ctypes/OSError/WinError into DevasysI2CError.
        """
        try:
            func = getattr(self.dll, function_name)
        except AttributeError as exc:
            raise DevasysI2CError(
                "DLL function not found.",
                function=function_name,
                context=context,
            ) from exc

        try:
            return func(*args)
        except Exception as exc:
            raise DevasysI2CError(
                "DLL function call failed.",
                function=function_name,
                context=context,
            ) from exc

    def _check_result_non_negative(self, function_name, result, context=None):
        """
        Many DAPI functions return negative value on error.
        """
        if result < 0:
            raise DevasysI2CError(
                "DAPI function returned error.",
                function=function_name,
                result=result,
                context=context,
            )

        return result

    def _check_result_exact(self, function_name, result, expected, context=None):
        """
        Used for I2C read/write where result should equal expected byte count.
        """
        if result != expected:
            raise DevasysI2CError(
                "DAPI function returned unexpected byte count.",
                function=function_name,
                result=result,
                context={
                    **(context or {}),
                    "expected": expected,
                },
            )

        return result

    # ------------------------------------------------------------------
    # Direct wrappers around all DLL driver functions
    # ------------------------------------------------------------------

    def dapi_open_device_instance(self, device_name, instance):
        result = self._call_dapi(
            "DAPI_OpenDeviceInstance",
            device_name,
            BYTE(instance),
            context={"device_name": device_name, "instance": instance},
        )

        invalid_handle = ctypes.c_void_p(-1).value

        if result in (None, 0, invalid_handle):
            raise DevasysI2CError(
                "Could not open DeVaSys USB-I2C/IO device.",
                function="DAPI_OpenDeviceInstance",
                result=result,
                context={"device_name": device_name, "instance": instance},
            )

        return result

    def dapi_close_device_instance(self):
        self._require_open()

        result = self._call_dapi(
            "DAPI_CloseDeviceInstance",
            self.handle,
            context={"handle": self.handle},
        )

        if not result:
            raise DevasysI2CError(
                "Could not close DeVaSys USB-I2C/IO device.",
                function="DAPI_CloseDeviceInstance",
                result=result,
            )

        return result

    def dapi_read_i2c(self, trans, expected_count=None, context=None):
        self._require_open()

        result = self._call_dapi(
            "DAPI_ReadI2c",
            self.handle,
            ctypes.byref(trans),
            context=context,
        )

        self._check_result_non_negative(
            "DAPI_ReadI2c",
            result,
            context=context,
        )

        if expected_count is not None:
            self._check_result_exact(
                "DAPI_ReadI2c",
                result,
                expected_count,
                context=context,
            )

        return result

    def dapi_write_i2c(self, trans, expected_count=None, context=None):
        self._require_open()

        result = self._call_dapi(
            "DAPI_WriteI2c",
            self.handle,
            ctypes.byref(trans),
            context=context,
        )

        self._check_result_non_negative(
            "DAPI_WriteI2c",
            result,
            context=context,
        )

        if expected_count is not None:
            self._check_result_exact(
                "DAPI_WriteI2c",
                result,
                expected_count,
                context=context,
            )

        return result

    def dapi_config_io_ports(self, config_mask):
        self._require_open()

        result = self._call_dapi(
            "DAPI_ConfigIoPorts",
            self.handle,
            DWORD(config_mask),
            context={"config_mask": hex(config_mask)},
        )

        return self._check_result_non_negative(
            "DAPI_ConfigIoPorts",
            result,
            context={"config_mask": hex(config_mask)},
        )

    def dapi_read_io_ports(self):
        self._require_open()

        value = DWORD(0)

        result = self._call_dapi(
            "DAPI_ReadIoPorts",
            self.handle,
            ctypes.byref(value),
        )

        self._check_result_non_negative(
            "DAPI_ReadIoPorts",
            result,
        )

        return value.value

    def dapi_write_io_ports(self, data, mask=0xFFFFFFFF):
        self._require_open()

        result = self._call_dapi(
            "DAPI_WriteIoPorts",
            self.handle,
            DWORD(data),
            DWORD(mask),
            context={
                "data": hex(data),
                "mask": hex(mask),
            },
        )

        return self._check_result_non_negative(
            "DAPI_WriteIoPorts",
            result,
            context={
                "data": hex(data),
                "mask": hex(mask),
            },
        )

    # ------------------------------------------------------------------
    # Device open / close
    # ------------------------------------------------------------------

    def open(self, instance=0):
        self.handle = self.dapi_open_device_instance(
            self.DEVICE_NAME,
            instance,
        )
        return self.handle

    def close(self):
        if self.handle:
            result = self.dapi_close_device_instance()
            self.handle = None
            return result

        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    # ------------------------------------------------------------------
    # I2C helper functions
    # ------------------------------------------------------------------

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
            raise ValueError(
                f"Single transaction max is {self.MAX_I2C_COUNT} bytes."
            )

        if len(data) > 256:
            raise ValueError("I2C_TRANS data buffer max is 256 bytes.")

        trans = I2C_TRANS()
        trans.byTransType = BYTE(trans_type)
        trans.bySlvDevAddr = BYTE(self._addr7_to_devasys(addr7))
        trans.wMemoryAddr = WORD(memory_addr)
        trans.wCount = WORD(count)

        for i, value in enumerate(data):
            trans.Data[i] = value

        return trans

    # ------------------------------------------------------------------
    # Public I2C API
    # ------------------------------------------------------------------

    def write(self, addr7, data):
        """
        Raw I2C write without register address.
        """
        data = bytes(data)

        if not data:
            raise ValueError("write() requires at least one byte.")

        trans = self._make_trans(
            trans_type=self.I2C_TRANS_NOADR,
            addr7=addr7,
            data=data,
            count=len(data),
        )

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data),
            context={
                "addr7": f"0x{addr7:02X}",
                "count": len(data),
                "mode": "raw_write",
            },
        )

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

            self.dapi_read_i2c(
                trans,
                expected_count=chunk,
                context={
                    "addr7": f"0x{addr7:02X}",
                    "count": chunk,
                    "mode": "raw_read",
                },
            )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk

        return bytes(result_data)

    def write_reg8(self, addr7, reg8, data):
        """
        Write to 8-bit register address.
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

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data),
            context={
                "addr7": f"0x{addr7:02X}",
                "reg8": f"0x{reg8:02X}",
                "count": len(data),
                "mode": "write_reg8",
            },
        )

    def read_reg8(self, addr7, reg8, count):
        """
        Read from 8-bit register address.
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

            self.dapi_read_i2c(
                trans,
                expected_count=chunk,
                context={
                    "addr7": f"0x{addr7:02X}",
                    "reg8": f"0x{current_reg:02X}",
                    "count": chunk,
                    "mode": "read_reg8",
                },
            )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFF

        return bytes(result_data)

    def write_reg16(self, addr7, reg16, data):
        """
        Write to 16-bit register address.
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

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data),
            context={
                "addr7": f"0x{addr7:02X}",
                "reg16": f"0x{reg16:04X}",
                "count": len(data),
                "mode": "write_reg16",
            },
        )

    def read_reg16(self, addr7, reg16, count):
        """
        Read from 16-bit register address.
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

            self.dapi_read_i2c(
                trans,
                expected_count=chunk,
                context={
                    "addr7": f"0x{addr7:02X}",
                    "reg16": f"0x{current_reg:04X}",
                    "count": chunk,
                    "mode": "read_reg16",
                },
            )

            result_data.extend(bytes(trans.Data[:chunk]))
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFFFF

        return bytes(result_data)

    def scan(self, start=0x03, end=0x77):
        """
        Simple I2C scan.

        This uses 1-byte read test.
        It can miss write-only devices, but works for many common sensors.
        """
        found = []

        for addr in range(start, end + 1):
            try:
                self.read(addr, 1)
                found.append(addr)
            except DevasysI2CError:
                pass

        return found

    # ------------------------------------------------------------------
    # Public digital IO API
    # ------------------------------------------------------------------

    def config_io_ports(self, config_mask):
        return self.dapi_config_io_ports(config_mask)

    def read_io_ports(self):
        return self.dapi_read_io_ports()

    def write_io_ports(self, data, mask=0xFFFFFFFF):
        return self.dapi_write_io_ports(data, mask)


if __name__ == "__main__":
    try:
        with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
            print("Scanning I2C bus...")
            devices = i2c.scan()

            if devices:
                print("Found I2C devices:")
                for addr in devices:
                    print(f"  0x{addr:02X}")
            else:
                print("No I2C devices found.")

    except DevasysI2CError as exc:
        print("DeVaSys error:")
        print(exc)