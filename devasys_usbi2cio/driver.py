"""Low-level Python driver for DeVaSys USB-I2C/IO using UsbI2cIo.dll."""

from __future__ import annotations

import ctypes
import os
from typing import Any, Dict, List, Optional, Sequence, Union

from .errors import DevasysI2CError
from .types import (
    BOOL,
    BYTE,
    DEVINFO,
    DWORD,
    HANDLE,
    I2C_TRANS,
    LONG,
    LPDEVINFO,
    ULONG,
    USBI2CIO_I2C_MAX_DATA,
    USBI2CIO_IO_MAX_DATA,
    USBI2CIO_MAX_DEVICES,
    WORD,
    I2cTransType,
)

ByteSequence = Union[bytes, bytearray, memoryview, Sequence[int]]


class DevasysUsbI2cIo:
    """
    Low-level wrapper for the DeVaSys USB-I2C/IO Windows DLL.

    Public methods use normal 7-bit I2C addresses. The driver converts them
    internally to the 8-bit address format used by the DeVaSys API.
    """

    DEVICE_NAME = b"UsbI2cIo"

    # I2C transaction types
    I2C_TRANS_NOADR = int(I2cTransType.I2C_TRANS_NOADR)
    I2C_TRANS_8ADR = int(I2cTransType.I2C_TRANS_8ADR)
    I2C_TRANS_16ADR = int(I2cTransType.I2C_TRANS_16ADR)
    I2C_TRANS_NOADR_NS = int(I2cTransType.I2C_TRANS_NOADR_NS)
    I2C_TRANS_XICOR = int(I2cTransType.I2C_TRANS_XICOR)
    I2C_TRANS_8ADR_NONSEQ = int(I2cTransType.I2C_TRANS_8ADR_NONSEQ)
    I2C_TRANS_16ADR_NONSEQ = int(I2cTransType.I2C_TRANS_16ADR_NONSEQ)
    I2C_TRANS_24ADR_NONSEQ = int(I2cTransType.I2C_TRANS_24ADR_NONSEQ)

    # Header value: USBI2CIO_I2C_MAX_DATA = 1088
    MAX_I2C_COUNT = USBI2CIO_I2C_MAX_DATA
    MAX_IO_COUNT = USBI2CIO_IO_MAX_DATA

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

    def _set_signature(self, name: str, argtypes: list, restype) -> None:
        """Set a DLL function signature when the function exists."""
        if hasattr(self.dll, name):
            func = getattr(self.dll, name)
            func.argtypes = argtypes
            func.restype = restype

    def _setup_api(self) -> None:
        """Define ctypes signatures for all exported functions listed in Usbi2cio.h."""

        # Version calls
        self._set_signature("DAPI_GetDllVersion", [], WORD)
        self._set_signature("DAPI_GetDriverVersion", [], WORD)
        self._set_signature("DAPI_GetFirmwareVersion", [HANDLE, ctypes.POINTER(WORD)], BOOL)

        # Open / close / info calls
        self._set_signature("DAPI_OpenDeviceInstance", [ctypes.c_char_p, BYTE], HANDLE)
        self._set_signature("DAPI_CloseDeviceInstance", [HANDLE], BOOL)
        self._set_signature("DAPI_DetectDevice", [HANDLE], BOOL)
        self._set_signature("DAPI_GetDeviceCount", [ctypes.c_char_p], BYTE)
        self._set_signature("DAPI_GetDeviceInfo", [ctypes.c_char_p, LPDEVINFO], BYTE)
        self._set_signature("DAPI_OpenDeviceBySerialId", [ctypes.c_char_p, ctypes.c_char_p], HANDLE)
        self._set_signature("DAPI_GetSerialId", [HANDLE, ctypes.c_char_p], BOOL)

        # I/O calls
        self._set_signature("DAPI_ConfigIoPorts", [HANDLE, ULONG], BOOL)
        self._set_signature("DAPI_GetIoConfig", [HANDLE, ctypes.POINTER(LONG)], BOOL)
        self._set_signature("DAPI_ReadIoPorts", [HANDLE, ctypes.POINTER(LONG)], BOOL)
        self._set_signature("DAPI_WriteIoPorts", [HANDLE, ULONG, ULONG], BOOL)
        self._set_signature(
            "DAPI_BlockWriteIoPorts",
            [HANDLE, WORD, WORD, ctypes.POINTER(BYTE), WORD],
            LONG,
        )
        self._set_signature(
            "DAPI_BlockReadIoPorts",
            [HANDLE, ctypes.POINTER(BYTE), WORD, WORD, WORD],
            LONG,
        )

        # I2C calls
        self._set_signature("DAPI_ReadI2c", [HANDLE, ctypes.POINTER(I2C_TRANS)], LONG)
        self._set_signature("DAPI_WriteI2c", [HANDLE, ctypes.POINTER(I2C_TRANS)], LONG)

        # Debugging calls
        self._set_signature("DAPI_ReadDebugBuffer", [ctypes.c_char_p, HANDLE, LONG], LONG)

        # Fast transfer calls
        self._set_signature("DAPI_WriteFastXferVr", [HANDLE, WORD, ctypes.POINTER(BYTE)], LONG)
        self._set_signature("DAPI_ReadFastXferVr", [HANDLE, ctypes.POINTER(BYTE), WORD], LONG)

        # Generic USB transfer calls
        self._set_signature(
            "DAPI_TransferData",
            [HANDLE, BYTE, ctypes.POINTER(BYTE), ctypes.POINTER(ULONG)],
            BOOL,
        )
        self._set_signature(
            "DAPI_SetVendorRequest",
            [HANDLE, BYTE, WORD, WORD, WORD, ctypes.POINTER(BYTE)],
            LONG,
        )
        self._set_signature(
            "DAPI_GetVendorRequest",
            [HANDLE, ctypes.POINTER(BYTE), BYTE, WORD, WORD, WORD],
            LONG,
        )

        # Property calls
        self._set_signature("DAPI_SetProperty", [HANDLE, BYTE, BYTE], BOOL)
        self._set_signature("DAPI_GetProperty", [HANDLE, ctypes.POINTER(BYTE), BYTE], BOOL)
        self._set_signature("DAPI_GetLastFirmwareError", [HANDLE, ctypes.POINTER(LONG)], BOOL)

        # Polling calls listed as unimplemented in the vendor header
        self._set_signature("DAPI_EnablePolling", [], None)
        self._set_signature("DAPI_DisablePolling", [], None)
        self._set_signature("DAPI_GetPolledInfo", [], None)

    # ------------------------------------------------------------------
    # Generic DLL-call wrappers and validators
    # ------------------------------------------------------------------

    def _require_open(self) -> None:
        if not self.handle:
            raise DevasysI2CError("Device is not open.")

    def _call_dapi(self, function_name: str, *args, context: Optional[dict] = None):
        """Call a DLL function and convert failures to DevasysI2CError."""
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

    def _check_bool(self, function_name: str, result: Any, context: Optional[dict] = None) -> bool:
        if not bool(result):
            raise DevasysI2CError(
                "DAPI function returned FALSE.",
                function=function_name,
                result=int(result) if result is not None else None,
                context=context,
            )
        return bool(result)

    def _check_result_non_negative(
        self,
        function_name: str,
        result: int,
        context: Optional[dict] = None,
    ) -> int:
        if result < 0:
            raise DevasysI2CError(
                "DAPI function returned error.",
                function=function_name,
                result=result,
                context=context,
            )
        return int(result)

    def _check_result_exact(
        self,
        function_name: str,
        result: int,
        expected: int,
        context: Optional[dict] = None,
    ) -> int:
        if result != expected:
            merged_context = dict(context or {})
            merged_context["expected"] = expected
            raise DevasysI2CError(
                "DAPI function returned unexpected byte count.",
                function=function_name,
                result=result,
                context=merged_context,
            )
        return int(result)

    @staticmethod
    def _invalid_handle_values() -> set:
        return {None, 0, ctypes.c_void_p(-1).value}

    @staticmethod
    def _coerce_bytes(data: ByteSequence) -> bytes:
        if isinstance(data, memoryview):
            return data.tobytes()
        try:
            return bytes(data)
        except ValueError as exc:
            raise ValueError("Data must contain only byte values 0x00 to 0xFF") from exc

    @staticmethod
    def _decode_c_serial(raw: bytes) -> str:
        return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")

    # ------------------------------------------------------------------
    # Version calls
    # ------------------------------------------------------------------

    def dapi_get_dll_version(self) -> int:
        return int(self._call_dapi("DAPI_GetDllVersion"))

    def dapi_get_driver_version(self) -> int:
        return int(self._call_dapi("DAPI_GetDriverVersion"))

    def dapi_get_firmware_version(self) -> int:
        self._require_open()
        version = WORD(0)
        result = self._call_dapi(
            "DAPI_GetFirmwareVersion",
            self.handle,
            ctypes.byref(version),
        )
        self._check_bool("DAPI_GetFirmwareVersion", result)
        return int(version.value)

    # User-friendly aliases
    get_dll_version = dapi_get_dll_version
    get_driver_version = dapi_get_driver_version
    get_firmware_version = dapi_get_firmware_version

    # ------------------------------------------------------------------
    # Open / close / device info calls
    # ------------------------------------------------------------------

    def dapi_open_device_instance(self, device_name: bytes, instance: int):
        result = self._call_dapi(
            "DAPI_OpenDeviceInstance",
            device_name,
            BYTE(instance),
            context={"device_name": device_name, "instance": instance},
        )

        if result in self._invalid_handle_values():
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
        return self._check_bool(
            "DAPI_CloseDeviceInstance",
            result,
            context={"handle": self.handle},
        )

    def dapi_detect_device(self) -> bool:
        self._require_open()
        result = self._call_dapi("DAPI_DetectDevice", self.handle)
        return self._check_bool("DAPI_DetectDevice", result)

    def dapi_get_device_count(self, device_name: bytes = DEVICE_NAME) -> int:
        return int(self._call_dapi("DAPI_GetDeviceCount", device_name))

    def dapi_get_device_info(self, device_name: bytes = DEVICE_NAME) -> List[Dict[str, Any]]:
        info_array_type = DEVINFO * USBI2CIO_MAX_DEVICES
        info_array = info_array_type()
        count = int(self._call_dapi("DAPI_GetDeviceInfo", device_name, info_array))
        count = max(0, min(count, USBI2CIO_MAX_DEVICES))

        devices = []
        for index in range(count):
            item = info_array[index]
            serial = self._decode_c_serial(bytes(item.SerialId))
            devices.append({"instance": int(item.byInstance), "serial_id": serial})
        return devices

    def dapi_open_device_by_serial_id(self, device_name: bytes, serial_id: Union[str, bytes]):
        serial_bytes = serial_id.encode("ascii") if isinstance(serial_id, str) else serial_id
        result = self._call_dapi(
            "DAPI_OpenDeviceBySerialId",
            device_name,
            serial_bytes,
            context={"device_name": device_name, "serial_id": serial_id},
        )
        if result in self._invalid_handle_values():
            raise DevasysI2CError(
                "Could not open DeVaSys USB-I2C/IO device by serial ID.",
                function="DAPI_OpenDeviceBySerialId",
                result=result,
                context={"device_name": device_name, "serial_id": serial_id},
            )
        return result

    def dapi_get_serial_id(self) -> str:
        self._require_open()
        buffer = ctypes.create_string_buffer(10)
        result = self._call_dapi("DAPI_GetSerialId", self.handle, buffer)
        self._check_bool("DAPI_GetSerialId", result)
        return self._decode_c_serial(buffer.raw)

    def open(self, instance: int = 0):
        self.handle = self.dapi_open_device_instance(self.DEVICE_NAME, instance)
        return self.handle

    def open_by_serial_id(self, serial_id: Union[str, bytes]):
        if self.handle:
            self.close()
        self.handle = self.dapi_open_device_by_serial_id(self.DEVICE_NAME, serial_id)
        return self.handle

    def close(self):
        if self.handle:
            result = self.dapi_close_device_instance()
            self.handle = None
            return result
        return None

    def detect_device(self) -> bool:
        return self.dapi_detect_device()

    def get_serial_id(self) -> str:
        return self.dapi_get_serial_id()

    @classmethod
    def get_device_count(cls, dll_path: str = "UsbI2cIo.dll", device_name: bytes = DEVICE_NAME) -> int:
        temp = cls.__new__(cls)
        temp.dll_path = dll_path
        temp.dll = temp._load_dll(dll_path)
        temp._setup_api()
        temp.handle = None
        return temp.dapi_get_device_count(device_name)

    @classmethod
    def get_device_info(cls, dll_path: str = "UsbI2cIo.dll", device_name: bytes = DEVICE_NAME) -> List[Dict[str, Any]]:
        temp = cls.__new__(cls)
        temp.dll_path = dll_path
        temp.dll = temp._load_dll(dll_path)
        temp._setup_api()
        temp.handle = None
        return temp.dapi_get_device_info(device_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    # ------------------------------------------------------------------
    # I/O calls
    # ------------------------------------------------------------------

    def dapi_config_io_ports(self, config_mask: int) -> bool:
        self._require_open()
        context = {"config_mask": hex(config_mask)}
        result = self._call_dapi(
            "DAPI_ConfigIoPorts",
            self.handle,
            ULONG(config_mask),
            context=context,
        )
        return self._check_bool("DAPI_ConfigIoPorts", result, context=context)

    def dapi_get_io_config(self) -> int:
        self._require_open()
        value = LONG(0)
        result = self._call_dapi("DAPI_GetIoConfig", self.handle, ctypes.byref(value))
        self._check_bool("DAPI_GetIoConfig", result)
        return int(value.value)

    def dapi_read_io_ports(self) -> int:
        self._require_open()
        value = LONG(0)
        result = self._call_dapi("DAPI_ReadIoPorts", self.handle, ctypes.byref(value))
        self._check_bool("DAPI_ReadIoPorts", result)
        return int(value.value)

    def dapi_write_io_ports(self, data: int, mask: int = 0xFFFFFFFF) -> bool:
        self._require_open()
        context = {"data": hex(data), "mask": hex(mask)}
        result = self._call_dapi(
            "DAPI_WriteIoPorts",
            self.handle,
            ULONG(data),
            ULONG(mask),
            context=context,
        )
        return self._check_bool("DAPI_WriteIoPorts", result, context=context)

    def dapi_block_write_io_ports(self, io_mode: int, io_index: int, data: ByteSequence) -> int:
        self._require_open()
        data_bytes = self._coerce_bytes(data)
        if len(data_bytes) > self.MAX_IO_COUNT:
            raise ValueError(f"Block I/O write max is {self.MAX_IO_COUNT} bytes")

        array_type = BYTE * len(data_bytes)
        buffer = array_type(*data_bytes)
        context = {"io_mode": io_mode, "io_index": io_index, "count": len(data_bytes)}
        result = self._call_dapi(
            "DAPI_BlockWriteIoPorts",
            self.handle,
            WORD(io_mode),
            WORD(io_index),
            buffer,
            WORD(len(data_bytes)),
            context=context,
        )
        return self._check_result_exact(
            "DAPI_BlockWriteIoPorts",
            result,
            len(data_bytes),
            context=context,
        )

    def dapi_block_read_io_ports(self, io_mode: int, io_index: int, count: int) -> bytes:
        self._require_open()
        if count < 0:
            raise ValueError("count must be >= 0")
        if count > self.MAX_IO_COUNT:
            raise ValueError(f"Block I/O read max is {self.MAX_IO_COUNT} bytes")

        array_type = BYTE * count
        buffer = array_type()
        context = {"io_mode": io_mode, "io_index": io_index, "count": count}
        result = self._call_dapi(
            "DAPI_BlockReadIoPorts",
            self.handle,
            buffer,
            WORD(io_mode),
            WORD(io_index),
            WORD(count),
            context=context,
        )
        self._check_result_exact("DAPI_BlockReadIoPorts", result, count, context=context)
        return bytes(buffer[:count])

    # Friendly aliases
    config_io_ports = dapi_config_io_ports
    get_io_config = dapi_get_io_config
    read_io_ports = dapi_read_io_ports
    write_io_ports = dapi_write_io_ports
    block_write_io_ports = dapi_block_write_io_ports
    block_read_io_ports = dapi_block_read_io_ports

    # ------------------------------------------------------------------
    # I2C helpers and calls
    # ------------------------------------------------------------------

    @staticmethod
    def _check_addr7(addr7: int) -> None:
        if not 0x00 <= addr7 <= 0x7F:
            raise ValueError("I2C address must be 7-bit: 0x00 to 0x7F")

    @classmethod
    def _addr7_to_devasys(cls, addr7: int) -> int:
        cls._check_addr7(addr7)
        return (addr7 << 1) & 0xFE

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
        if len(data_bytes) > self.MAX_I2C_COUNT:
            raise ValueError(f"I2C_TRANS data buffer max is {self.MAX_I2C_COUNT} bytes")
        if not 0 <= memory_addr <= 0xFFFF:
            raise ValueError("memory_addr must fit in WORD: 0x0000 to 0xFFFF")

        trans = I2C_TRANS()
        trans.byTransType = BYTE(trans_type)
        trans.bySlvDevAddr = BYTE(self._addr7_to_devasys(addr7))
        trans.wMemoryAddr = WORD(memory_addr)
        trans.wCount = WORD(count)

        for index, value in enumerate(data_bytes):
            trans.Data[index] = value

        return trans

    def dapi_read_i2c(
        self,
        trans: I2C_TRANS,
        expected_count: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> int:
        self._require_open()
        result = self._call_dapi("DAPI_ReadI2c", self.handle, ctypes.byref(trans), context=context)
        self._check_result_non_negative("DAPI_ReadI2c", result, context=context)
        if expected_count is not None:
            self._check_result_exact("DAPI_ReadI2c", result, expected_count, context=context)
        return int(result)

    def dapi_write_i2c(
        self,
        trans: I2C_TRANS,
        expected_count: Optional[int] = None,
        context: Optional[dict] = None,
    ) -> int:
        self._require_open()
        result = self._call_dapi("DAPI_WriteI2c", self.handle, ctypes.byref(trans), context=context)
        self._check_result_non_negative("DAPI_WriteI2c", result, context=context)
        if expected_count is not None:
            self._check_result_exact("DAPI_WriteI2c", result, expected_count, context=context)
        return int(result)

    def i2c_transfer(
        self,
        *,
        addr7: int,
        trans_type: int,
        memory_addr: int = 0,
        data: ByteSequence = b"",
        count: Optional[int] = None,
        read: bool = False,
    ) -> bytes | int:
        """
        Generic I2C transfer helper for all transaction types supported by I2C_TRANS.

        For read=True, returns bytes. For read=False, returns written byte count.
        """
        if read:
            if count is None:
                raise ValueError("count is required for read transfers")
            trans = self._make_trans(trans_type, addr7, memory_addr=memory_addr, count=count)
            self.dapi_read_i2c(
                trans,
                expected_count=count,
                context={
                    "addr7": f"0x{addr7:02X}",
                    "trans_type": f"0x{trans_type:02X}",
                    "memory_addr": f"0x{memory_addr:04X}",
                    "count": count,
                    "mode": "generic_i2c_read",
                },
            )
            return bytes(trans.Data[:count])

        data_bytes = self._coerce_bytes(data)
        trans = self._make_trans(
            trans_type,
            addr7,
            memory_addr=memory_addr,
            data=data_bytes,
            count=len(data_bytes),
        )
        return self.dapi_write_i2c(
            trans,
            expected_count=len(data_bytes),
            context={
                "addr7": f"0x{addr7:02X}",
                "trans_type": f"0x{trans_type:02X}",
                "memory_addr": f"0x{memory_addr:04X}",
                "count": len(data_bytes),
                "mode": "generic_i2c_write",
            },
        )

    def write(self, addr7: int, data: ByteSequence) -> int:
        data_bytes = self._coerce_bytes(data)
        if not data_bytes:
            raise ValueError("write() requires at least one byte")
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_NOADR,
            data=data_bytes,
            read=False,
        ))

    def write_no_stop(self, addr7: int, data: ByteSequence) -> int:
        """Raw I2C write with stop signaling inhibited, using I2C_TRANS_NOADR_NS."""
        data_bytes = self._coerce_bytes(data)
        if not data_bytes:
            raise ValueError("write_no_stop() requires at least one byte")
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_NOADR_NS,
            data=data_bytes,
            read=False,
        ))

    def read(self, addr7: int, count: int) -> bytes:
        if count <= 0:
            return bytes()

        result_data = bytearray()
        remaining = count

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)
            data = self.i2c_transfer(
                addr7=addr7,
                trans_type=self.I2C_TRANS_NOADR,
                count=chunk,
                read=True,
            )
            result_data.extend(data)
            remaining -= chunk

        return bytes(result_data)

    def write_reg8(self, addr7: int, reg8: int, data: ByteSequence) -> int:
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")
        data_bytes = self._coerce_bytes(data)
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_8ADR,
            memory_addr=reg8,
            data=data_bytes,
            read=False,
        ))

    def read_reg8(self, addr7: int, reg8: int, count: int) -> bytes:
        if not 0 <= reg8 <= 0xFF:
            raise ValueError("reg8 must be 0x00 to 0xFF")
        if count <= 0:
            return bytes()

        result_data = bytearray()
        remaining = count
        current_reg = reg8

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)
            data = self.i2c_transfer(
                addr7=addr7,
                trans_type=self.I2C_TRANS_8ADR,
                memory_addr=current_reg,
                count=chunk,
                read=True,
            )
            result_data.extend(data)
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFF

        return bytes(result_data)

    def write_reg16(self, addr7: int, reg16: int, data: ByteSequence) -> int:
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")
        data_bytes = self._coerce_bytes(data)
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_16ADR,
            memory_addr=reg16,
            data=data_bytes,
            read=False,
        ))

    def read_reg16(self, addr7: int, reg16: int, count: int) -> bytes:
        if not 0 <= reg16 <= 0xFFFF:
            raise ValueError("reg16 must be 0x0000 to 0xFFFF")
        if count <= 0:
            return bytes()

        result_data = bytearray()
        remaining = count
        current_reg = reg16

        while remaining:
            chunk = min(remaining, self.MAX_I2C_COUNT)
            data = self.i2c_transfer(
                addr7=addr7,
                trans_type=self.I2C_TRANS_16ADR,
                memory_addr=current_reg,
                count=chunk,
                read=True,
            )
            result_data.extend(data)
            remaining -= chunk
            current_reg = (current_reg + chunk) & 0xFFFF

        return bytes(result_data)

    def write_reg8_nonseq(self, addr7: int, reg8: int, data: ByteSequence) -> int:
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_8ADR_NONSEQ,
            memory_addr=reg8,
            data=data,
            read=False,
        ))

    def write_reg16_nonseq(self, addr7: int, reg16: int, data: ByteSequence) -> int:
        return int(self.i2c_transfer(
            addr7=addr7,
            trans_type=self.I2C_TRANS_16ADR_NONSEQ,
            memory_addr=reg16,
            data=data,
            read=False,
        ))

    def scan(self, start: int = 0x03, end: int = 0x77) -> list:
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
    # Debugging calls
    # ------------------------------------------------------------------

    def dapi_read_debug_buffer(self, max_bytes: int = 1024) -> str:
        self._require_open()
        if max_bytes <= 0:
            return ""

        buffer = ctypes.create_string_buffer(max_bytes)
        result = self._call_dapi(
            "DAPI_ReadDebugBuffer",
            buffer,
            self.handle,
            LONG(max_bytes),
            context={"max_bytes": max_bytes},
        )
        n = self._check_result_non_negative(
            "DAPI_ReadDebugBuffer",
            result,
            context={"max_bytes": max_bytes},
        )
        return buffer.raw[:n].split(b"\x00", 1)[0].decode("ascii", errors="replace")

    read_debug_buffer = dapi_read_debug_buffer

    # ------------------------------------------------------------------
    # Fast transfer calls
    # ------------------------------------------------------------------

    def dapi_write_fast_xfer_vr(self, data: ByteSequence) -> int:
        self._require_open()
        data_bytes = self._coerce_bytes(data)
        if len(data_bytes) > 0xFFFF:
            raise ValueError("Fast transfer write max is 65535 bytes")

        array_type = BYTE * len(data_bytes)
        buffer = array_type(*data_bytes)
        context = {"count": len(data_bytes)}
        result = self._call_dapi(
            "DAPI_WriteFastXferVr",
            self.handle,
            WORD(len(data_bytes)),
            buffer,
            context=context,
        )
        return self._check_result_exact("DAPI_WriteFastXferVr", result, len(data_bytes), context=context)

    def dapi_read_fast_xfer_vr(self, count: int) -> bytes:
        self._require_open()
        if count < 0:
            raise ValueError("count must be >= 0")
        if count > 0xFFFF:
            raise ValueError("Fast transfer read max is 65535 bytes")

        array_type = BYTE * count
        buffer = array_type()
        context = {"count": count}
        result = self._call_dapi(
            "DAPI_ReadFastXferVr",
            self.handle,
            buffer,
            WORD(count),
            context=context,
        )
        self._check_result_exact("DAPI_ReadFastXferVr", result, count, context=context)
        return bytes(buffer[:count])

    write_fast_xfer_vr = dapi_write_fast_xfer_vr
    read_fast_xfer_vr = dapi_read_fast_xfer_vr

    # ------------------------------------------------------------------
    # Generic USB transfer and vendor request calls
    # ------------------------------------------------------------------

    def dapi_transfer_data(self, endpoint: int, buffer: ByteSequence, length: Optional[int] = None) -> bytes:
        self._require_open()
        data_bytes = self._coerce_bytes(buffer)
        if length is None:
            length = len(data_bytes)
        if length < 0:
            raise ValueError("length must be >= 0")

        array_type = BYTE * max(length, len(data_bytes), 1)
        raw = list(data_bytes[:length])
        raw.extend([0] * (max(length, len(data_bytes), 1) - len(raw)))
        c_buffer = array_type(*raw)
        c_length = ULONG(length)

        result = self._call_dapi(
            "DAPI_TransferData",
            self.handle,
            BYTE(endpoint),
            c_buffer,
            ctypes.byref(c_length),
            context={"endpoint": endpoint, "length": length},
        )
        self._check_bool(
            "DAPI_TransferData",
            result,
            context={"endpoint": endpoint, "length": length},
        )
        return bytes(c_buffer[: int(c_length.value)])

    def dapi_set_vendor_request(
        self,
        request: int,
        value: int,
        index: int,
        data: ByteSequence = b"",
        length: Optional[int] = None,
    ) -> int:
        self._require_open()
        data_bytes = self._coerce_bytes(data)
        if length is None:
            length = len(data_bytes)
        if length < 0 or length > 0xFFFF:
            raise ValueError("length must be 0 to 65535")

        array_type = BYTE * max(length, len(data_bytes), 1)
        raw = list(data_bytes[:length])
        raw.extend([0] * (max(length, len(data_bytes), 1) - len(raw)))
        buffer = array_type(*raw)

        context = {
            "request": request,
            "value": value,
            "index": index,
            "length": length,
        }
        result = self._call_dapi(
            "DAPI_SetVendorRequest",
            self.handle,
            BYTE(request),
            WORD(value),
            WORD(index),
            WORD(length),
            buffer,
            context=context,
        )
        return self._check_result_non_negative("DAPI_SetVendorRequest", result, context=context)

    def dapi_get_vendor_request(
        self,
        request: int,
        value: int,
        index: int,
        length: int,
    ) -> bytes:
        self._require_open()
        if length < 0 or length > 0xFFFF:
            raise ValueError("length must be 0 to 65535")

        array_type = BYTE * max(length, 1)
        buffer = array_type()
        context = {
            "request": request,
            "value": value,
            "index": index,
            "length": length,
        }
        result = self._call_dapi(
            "DAPI_GetVendorRequest",
            self.handle,
            buffer,
            BYTE(request),
            WORD(value),
            WORD(index),
            WORD(length),
            context=context,
        )
        n = self._check_result_non_negative("DAPI_GetVendorRequest", result, context=context)
        return bytes(buffer[: min(n, length)])

    transfer_data = dapi_transfer_data
    set_vendor_request = dapi_set_vendor_request
    get_vendor_request = dapi_get_vendor_request

    # ------------------------------------------------------------------
    # Property and firmware error calls
    # ------------------------------------------------------------------

    def dapi_set_property(self, prop_index: int, prop_value: int) -> bool:
        self._require_open()
        context = {"prop_index": prop_index, "prop_value": prop_value}
        result = self._call_dapi(
            "DAPI_SetProperty",
            self.handle,
            BYTE(prop_index),
            BYTE(prop_value),
            context=context,
        )
        return self._check_bool("DAPI_SetProperty", result, context=context)

    def dapi_get_property(self, prop_index: int) -> int:
        self._require_open()
        value = BYTE(0)
        result = self._call_dapi(
            "DAPI_GetProperty",
            self.handle,
            ctypes.byref(value),
            BYTE(prop_index),
            context={"prop_index": prop_index},
        )
        self._check_bool("DAPI_GetProperty", result, context={"prop_index": prop_index})
        return int(value.value)

    def dapi_get_last_firmware_error(self) -> int:
        self._require_open()
        value = LONG(0)
        result = self._call_dapi("DAPI_GetLastFirmwareError", self.handle, ctypes.byref(value))
        self._check_bool("DAPI_GetLastFirmwareError", result)
        return int(value.value)

    set_property = dapi_set_property
    get_property = dapi_get_property
    get_last_firmware_error = dapi_get_last_firmware_error

    # ------------------------------------------------------------------
    # Polling calls listed as unimplemented in the vendor header
    # ------------------------------------------------------------------

    def dapi_enable_polling(self) -> None:
        self._call_dapi("DAPI_EnablePolling")
        return None

    def dapi_disable_polling(self) -> None:
        self._call_dapi("DAPI_DisablePolling")
        return None

    def dapi_get_polled_info(self) -> None:
        self._call_dapi("DAPI_GetPolledInfo")
        return None

    enable_polling = dapi_enable_polling
    disable_polling = dapi_disable_polling
    get_polled_info = dapi_get_polled_info
