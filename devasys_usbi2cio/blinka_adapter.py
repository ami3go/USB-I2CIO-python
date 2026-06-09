"""Blinka / CircuitPython-compatible I2C adapter for DeVaSys USB-I2C/IO."""

import time
from typing import Optional

from .driver import DevasysUsbI2cIo
from .errors import DevasysI2CError


class DevasysBlinkaI2C:
    """
    Blinka / CircuitPython-compatible adapter around :class:`DevasysUsbI2cIo`.

    This class is not a full Blinka backend. Code using ``board`` and
    ``busio.I2C(board.SCL, board.SDA)`` will not automatically use the DeVaSys
    board. Instead, instantiate this class and pass it directly to drivers.

    Provided methods:

    - try_lock()
    - unlock()
    - scan()
    - writeto()
    - readfrom_into()
    - writeto_then_readfrom()
    - deinit()
    """

    def __init__(
        self,
        dll_path: str = "UsbI2cIo.dll",
        instance: int = 0,
        frequency: Optional[int] = None,
        allow_stop_fallback: bool = True,
    ) -> None:
        self._dev = DevasysUsbI2cIo(dll_path=dll_path, instance=instance)
        self.frequency = frequency
        self._locked = False
        self._allow_stop_fallback = allow_stop_fallback
        self._pending_addr = None
        self._pending_write = None

    # ------------------------------------------------------------------
    # Context manager compatibility
    # ------------------------------------------------------------------

    def __enter__(self):
        while not self.try_lock():
            time.sleep(0.001)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.unlock()
        return False

    # ------------------------------------------------------------------
    # Blinka / CircuitPython-style locking
    # ------------------------------------------------------------------

    def try_lock(self) -> bool:
        """Try to lock the I2C bus."""
        if self._locked:
            return False
        self._locked = True
        return True

    def unlock(self) -> None:
        """Unlock the I2C bus."""
        self._locked = False

    # ------------------------------------------------------------------
    # Blinka / CircuitPython-style I2C methods
    # ------------------------------------------------------------------

    def scan(self) -> list:
        """Return detected 7-bit I2C addresses."""
        try:
            return self._dev.scan()
        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def writeto(self, address: int, buffer, *, start: int = 0, end: Optional[int] = None, stop: bool = True) -> None:
        """
        Write bytes to an I2C device.

        Signature follows the CircuitPython ``busio.I2C.writeto`` style.
        """
        if end is None:
            end = len(buffer)

        if start < 0 or end < start:
            raise ValueError("Invalid start/end slice")

        data = bytes(buffer[start:end])

        try:
            if stop:
                self._pending_addr = None
                self._pending_write = None

                # Some Adafruit probing code uses zero-length writes. DeVaSys
                # raw write does not support zero-length write, so use a
                # one-byte read probe instead.
                if not data:
                    self._dev.read(address, 1)
                    return None

                self._dev.write(address, data)
                return None

            # stop=False means: remember data, and complete transaction during
            # the next readfrom_into() call.
            self._pending_addr = address
            self._pending_write = data
            return None

        except DevasysI2CError as exc:
            self._pending_addr = None
            self._pending_write = None
            raise OSError(str(exc)) from exc

    def readfrom_into(self, address: int, buffer, *, start: int = 0, end: Optional[int] = None) -> None:
        """
        Read bytes from an I2C device into a mutable buffer.

        Signature follows the CircuitPython ``busio.I2C.readfrom_into`` style.
        """
        if end is None:
            end = len(buffer)

        if start < 0 or end < start:
            raise ValueError("Invalid start/end slice")

        read_count = end - start

        try:
            if self._pending_write is not None:
                pending_addr = self._pending_addr
                pending_write = self._pending_write

                # Clear pending state before executing the transfer. This avoids
                # leaving stale stop=False state after an exception.
                self._pending_addr = None
                self._pending_write = None

                if pending_addr != address:
                    raise OSError("Pending stop=False write address does not match read address")

                data = self._write_then_read_compat(address, pending_write, read_count)
            else:
                data = self._dev.read(address, read_count)

            for index, value in enumerate(data):
                buffer[start + index] = value

            return None

        except DevasysI2CError as exc:
            self._pending_addr = None
            self._pending_write = None
            raise OSError(str(exc)) from exc

    def writeto_then_readfrom(
        self,
        address: int,
        out_buffer,
        in_buffer,
        *,
        out_start: int = 0,
        out_end: Optional[int] = None,
        in_start: int = 0,
        in_end: Optional[int] = None,
    ) -> None:
        """
        Write bytes, then immediately read bytes.

        This method supports common register-based reads. If ``out_buffer`` has
        one byte, it is treated as an 8-bit register address. If it has two
        bytes, it is treated as a 16-bit register address.
        """
        if out_end is None:
            out_end = len(out_buffer)
        if in_end is None:
            in_end = len(in_buffer)

        if out_start < 0 or out_end < out_start:
            raise ValueError("Invalid output start/end slice")
        if in_start < 0 or in_end < in_start:
            raise ValueError("Invalid input start/end slice")

        out_data = bytes(out_buffer[out_start:out_end])
        read_count = in_end - in_start

        try:
            self._pending_addr = None
            self._pending_write = None

            data = self._write_then_read_compat(address, out_data, read_count)

            for index, value in enumerate(data):
                in_buffer[in_start + index] = value

            return None

        except DevasysI2CError as exc:
            raise OSError(str(exc)) from exc

    def deinit(self) -> None:
        """Close the underlying DeVaSys device."""
        self._pending_addr = None
        self._pending_write = None
        self._dev.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_then_read_compat(self, address: int, out_data: bytes, read_count: int) -> bytes:
        """
        Convert a Blinka-style write-then-read into DeVaSys transactions.

        Supported directly:

        - 0 output bytes: raw read
        - 1 output byte: 8-bit register read
        - 2 output bytes: 16-bit register read

        Longer output writes are handled using STOP fallback only when
        ``allow_stop_fallback`` is True.
        """
        if read_count <= 0:
            return bytes()

        if len(out_data) == 0:
            return self._dev.read(address, read_count)

        if len(out_data) == 1:
            return self._dev.read_reg8(address, out_data[0], read_count)

        if len(out_data) == 2:
            reg16 = (out_data[0] << 8) | out_data[1]
            return self._dev.read_reg16(address, reg16, read_count)

        if self._allow_stop_fallback:
            self._dev.write(address, out_data)
            return self._dev.read(address, read_count)

        raise OSError(
            "Generic repeated-start transaction with more than two address bytes "
            "is not directly supported by this DeVaSys wrapper."
        )
