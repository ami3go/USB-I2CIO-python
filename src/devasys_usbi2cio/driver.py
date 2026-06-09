"""Low-level Python driver for DeVaSys USB-I2C/IO using UsbI2cIo.dll."""

import ctypes
import os
from typing import Optional, Sequence, Union

from .errors import DevasysI2CError
from .types import BOOL, BYTE, DWORD, HANDLE, LONG, I2C_TRANS

ByteSequence = Union[bytes, bytearray, Sequence[int]]


class DevasysUsbI2cIo:
    """
    Low-level wrapper for the DeVaSys USB-I2C/IO Windows DLL.

    Public methods use normal 7-bit I2C addresses. The driver converts them
    internally to the 8-bit address format used by the DeVaSys API.

    Examples
    --------
    >>> with DevasysUsbI2cIo(dll_path="UsbI2cIo.dll") as i2c:
    ...     print([hex(addr) for addr in i2c.scan()])
    """

    DEVICE_NAME = b"UsbI2cIo"

    I2C_TRANS_NOADR = 0x00
    I2C_TRANS_8ADR = 0x01
    I2C_TRANS_16ADR = 0x02

    MAX_I2C_COUNT = 64

    def __init__(self, dll_path: str = "UsbI2cIo.dll", instance: int = 0) -> None:
        if os.name != "nt":
            raise DevasysI2CError(
                "UsbI2cIo.dll driver works on Windows only.",
                context={"os.name": os.name},
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

    def _load_dll(self, dll_path: str):
        """Load the DeVaSys vendor DLL."""
        dll_dir = os.path.dirname(os.path.abspath(dll_path))

        if dll_dir and os.path.exists(dll_dir) and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dll_dir)

        try:
            return ctypes.WinDLL(dll_path)
        except OSError as exc:
            raise DevasysI2CError(
                "Could not load UsbI2cIo.dll. Put the DLL beside this script "
                "or pass the full dll_path. Also check that Python 32/64-bit "
                "matches the DLL architecture.",
                function="WinDLL",
                context={"dll_path": dll_path},
            ) from exc

    def _setup_api(self) -> None:
        """
        Define argument and return types for all DAPI functions used by this driver.

        Required I2C functions are configured unconditionally. Optional digital
        IO functions are configured only if present in the DLL.
        """
        self.dll.DAPI_OpenDeviceInstance.argtypes = [ctypes.c_char_p, BYTE]
        self.dll.DAPI_OpenDeviceInstance.restype = HANDLE

        self.dll.DAPI_CloseDeviceInstance.argtypes = [HANDLE]
        self.dll.DAPI_CloseDeviceInstance.restype = BOOL

        self.dll.DAPI_ReadI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_ReadI2c.restype = LONG

        self.dll.DAPI_WriteI2c.argtypes = [HANDLE, ctypes.POINTER(I2C_TRANS)]
        self.dll.DAPI_WriteI2c.restype = LONG

        optional_signatures = {
            "DAPI_ConfigIoPorts": ([HANDLE, DWORD], LONG),
            "DAPI_ReadIoPorts": ([HANDLE, ctypes.POINTER(DWORD)], LONG),
            "DAPI_WriteIoPorts": ([HANDLE, DWORD, DWORD], LONG),
        }

        for name, (argtypes, restype) in optional_signatures.items():
            if hasattr(self.dll, name):
                func = getattr(self.dll, name)
                func.argtypes = argtypes
                func.restype = restype

    # ------------------------------------------------------------------
    # Generic DLL-call wrappers
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        if not self.handle:
            raise DevasysI2CError("Device is not open.")

    def _call_dapi(self, function_name: str, *args, context: Optional[dict] = None):
        """
        Generic wrapper around all DAPI DLL calls.

        This method converts DLL call failures and missing DLL functions into
        DevasysI2CError with context.
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

    def _check_result_non_negative(
        self,
        function_name: str,
        result: int,
        context: Optional[dict] = None,
    ) -> int:
        """Check functions where a negative return value means failure."""
        if result < 0:
            raise DevasysI2CError(
                "DAPI function returned error.",
                function=function_name,
                result=result,
                context=context,
            )
        return result

    def _check_result_exact(
        self,
        function_name: str,
        result: int,
        expected: int,
        context: Optional[dict] = None,
    ) -> int:
        """Check I2C transfers where return value must equal byte count."""
        if result != expected:
            merged_context = dict(context or {})
            merged_context["expected"] = expected
            raise DevasysI2CError(
                "DAPI function returned unexpected byte count.",
                function=function_name,
                result=result,
                context=merged_context,
            )
        return result

    # ------------------------------------------------------------------
    # Direct wrappers around DLL functions
    # ------------------------------------------------------------------

    def dapi_open_device_instance(self, device_name: bytes, instance: int):
        """Open a DeVaSys device instance through the DLL."""
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
        """Close the currently opened DeVaSys device instance."""
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
                context={"handle": self.handle},
            )

        return result

    def dapi_read_i2c(
        self,
        trans: I2C_TRANS,
        expected_count: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> int:
        """Read I2C data using DAPI_ReadI2c."""
        self._require_open()

        result = self._call_dapi(
            "DAPI_ReadI2c",
            self.handle,
            ctypes.byref(trans),
            context=context,
        )

        self._check_result_non_negative("DAPI_ReadI2c", result, context=context)

        if expected_count is not None:
            self._check_result_exact(
                "DAPI_ReadI2c",
                result,
                expected_count,
                context=context,
            )

        return result

    def dapi_write_i2c(
        self,
        trans: I2C_TRANS,
        expected_count: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> int:
        """Write I2C data using DAPI_WriteI2c."""
        self._require_open()

        result = self._call_dapi(
            "DAPI_WriteI2c",
            self.handle,
            ctypes.byref(trans),
            context=context,
        )

        self._check_result_non_negative("DAPI_WriteI2c", result, context=context)

        if expected_count is not None:
            self._check_result_exact(
                "DAPI_WriteI2c",
                result,
                expected_count,
                context=context,
            )

        return result

    def dapi_config_io_ports(self, config_mask: int) -> int:
        """Configure optional digital IO ports."""
        self._require_open()
        context = {"config_mask": hex(config_mask)}

        result = self._call_dapi(
            "DAPI_ConfigIoPorts",
            self.handle,
            DWORD(config_mask),
            context=context,
        )

        return self._check_result_non_negative(
            "DAPI_ConfigIoPorts",
            result,
            context=context,
        )

    def dapi_read_io_ports(self) -> int:
        """Read optional digital IO port state."""
        self._require_open()

        value = DWORD(0)

        result = self._call_dapi(
            "DAPI_ReadIoPorts",
            self.handle,
            ctypes.byref(value),
        )

        self._check_result_non_negative("DAPI_ReadIoPorts", result)
        return int(value.value)

    def dapi_write_io_ports(self, data: int, mask: int = 0xFFFFFFFF) -> int:
        """Write optional digital IO port state."""
        self._require_open()
        context = {"data": hex(data), "mask": hex(mask)}

        result = self._call_dapi(
            "DAPI_WriteIoPorts",
            self.handle,
            DWORD(data),
            DWORD(mask),
            context=context,
        )

        return self._check_result_non_negative(
            "DAPI_WriteIoPorts",
            result,
            context=context,
        )

    # ------------------------------------------------------------------
    # Device lifetime
    # ------------------------------------------------------------------

    def open(self, instance: int = 0):
        """Open a DeVaSys device instance."""
        self.handle = self.dapi_open_device_instance(self.DEVICE_NAME, instance)
        return self.handle

    def close(self):
        """Close the DeVaSys device if it is open."""
        if self.handle:
            result = self.dapi_close_device_instance()
            self.handle = None
            return result
        return None

    def __enter__(self):
        """Return self for context-manager usage."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Close the device when leaving a context manager."""
        self.close()

    # ------------------------------------------------------------------
    # I2C helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_addr7(addr7: int) -> None:
        if not 0x00 <= addr7 <= 0x7F:
            raise ValueError("I2C address must be 7-bit: 0x00 to 0x7F")

    @classmethod
    def _addr7_to_devasys(cls, addr7: int) -> int:
        cls._check_addr7(addr7)
        return (addr7 << 1) & 0xFE

    @staticmethod
    def _coerce_bytes(data: ByteSequence) -> bytes:
        try:
            return bytes(data)
        except ValueError as exc:
            raise ValueError("Data must contain only byte values 0x00 to 0xFF") from exc

    def _make_trans(
        self,
        trans_type: int,
        addr7: int,
        memory_addr: int = 0,
        data: ByteSequence = b"",
        count: Optional[int] = None,
    ) -> I2C_TRANS:
        data_bytes = self._coerce_bytes(data)

        if count is None:
            count = len(data_bytes)

        if count < 0:
            raise ValueError("count must be >= 0")

        if count > self.MAX_I2C_COUNT:
            raise ValueError(
                f"Single DeVaSys I2C transaction max is {self.MAX_I2C_COUNT} bytes"
            )

        if len(data_bytes) > 256:
            raise ValueError("I2C_TRANS data buffer max is 256 bytes")

        trans = I2C_TRANS()
        trans.byTransType = BYTE(trans_type)
        trans.bySlvDevAddr = BYTE(self._addr7_to_devasys(addr7))
        trans.wMemoryAddr = memory_addr
        trans.wCount = count

        for index, value in enumerate(data_bytes):
            trans.Data[index] = value

        return trans

    # ------------------------------------------------------------------
    # Public I2C API
    # ------------------------------------------------------------------

    def write(self, addr7: int, data: ByteSequence) -> int:
        """
        Raw I2C write without register address.

        Parameters
        ----------
        addr7:
            Normal 7-bit I2C address.

        data:
            One or more bytes to write.

        Returns
        -------
        int
            Number of bytes written.
        """
        data_bytes = self._coerce_bytes(data)

        if not data_bytes:
            raise ValueError("write() requires at least one byte")

        trans = self._make_trans(
            trans_type=self.I2C_TRANS_NOADR,
            addr7=addr7,
            data=data_bytes,
            count=len(data_bytes),
        )

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data_bytes),
            context={
                "addr7": f"0x{addr7:02X}",
                "count": len(data_bytes),
                "mode": "raw_write",
            },
        )

    def read(self, addr7: int, count: int) -> bytes:
        """
        Raw I2C read without register address.

        Long reads are split into MAX_I2C_COUNT chunks.
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

    def write_reg8(self, addr7: int, reg8: int, data: ByteSequence) -> int:
        """Write data to an 8-bit register address."""
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")

        data_bytes = self._coerce_bytes(data)
        trans = self._make_trans(
            trans_type=self.I2C_TRANS_8ADR,
            addr7=addr7,
            memory_addr=reg8,
            data=data_bytes,
            count=len(data_bytes),
        )

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data_bytes),
            context={
                "addr7": f"0x{addr7:02X}",
                "reg8": f"0x{reg8:02X}",
                "count": len(data_bytes),
                "mode": "write_reg8",
            },
        )

    def read_reg8(self, addr7: int, reg8: int, count: int) -> bytes:
        """Read data from an 8-bit register address."""
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")

        if count <= 0:
            return bytes()

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

    def write_reg16(self, addr7: int, reg16: int, data: ByteSequence) -> int:
        """Write data to a 16-bit register or memory address."""
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")

        data_bytes = self._coerce_bytes(data)
        trans = self._make_trans(
            trans_type=self.I2C_TRANS_16ADR,
            addr7=addr7,
            memory_addr=reg16,
            data=data_bytes,
            count=len(data_bytes),
        )

        return self.dapi_write_i2c(
            trans,
            expected_count=len(data_bytes),
            context={
                "addr7": f"0x{addr7:02X}",
                "reg16": f"0x{reg16:04X}",
                "count": len(data_bytes),
                "mode": "write_reg16",
            },
        )

    def read_reg16(self, addr7: int, reg16: int, count: int) -> bytes:
        """Read data from a 16-bit register or memory address."""
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")

        if count <= 0:
            return bytes()

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

    def scan(self, start: int = 0x03, end: int = 0x77) -> list:
        """
        Scan the I2C bus and return detected 7-bit addresses.

        This uses a one-byte read probe. It works for many devices but may
        miss write-only devices.
        """
        if not 0 <= start <= 0x7F:
            raise ValueError("start must be a 7-bit address")
        if not 0 <= end <= 0x7F:
            raise ValueError("end must be a 7-bit address")
        if start > end:
            raise ValueError("start must be <= end")

        found = []

        for addr in range(start, end + 1):
            try:
                self.read(addr, 1)
                found.append(addr)
            except DevasysI2CError:
                pass

        return found

    # ------------------------------------------------------------------
    # Optional digital IO public API
    # ------------------------------------------------------------------

    def config_io_ports(self, config_mask: int) -> int:
        """Configure optional digital IO ports."""
        return self.dapi_config_io_ports(config_mask)

    def read_io_ports(self) -> int:
        """Read optional digital IO ports."""
        return self.dapi_read_io_ports()

    def write_io_ports(self, data: int, mask: int = 0xFFFFFFFF) -> int:
        """Write optional digital IO ports."""
        return self.dapi_write_io_ports(data, mask)
