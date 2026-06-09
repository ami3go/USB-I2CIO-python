"""Exception types for the DeVaSys USB-I2C/IO package."""

from typing import Any, Dict, Optional


class DevasysI2CError(Exception):
    """
    Common exception for all DeVaSys USB-I2C/IO driver errors.

    Parameters
    ----------
    message:
        Human-readable error message.

    function:
        DLL function name or internal function name related to the failure.

    result:
        Result code returned by the DLL, if available.

    context:
        Additional debug context, such as address, register, byte count,
        transaction mode, DLL path, or device instance.
    """

    def __init__(
        self,
        message: str,
        function: Optional[str] = None,
        result: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.function = function
        self.result = result
        self.context = context or {}

        parts = [message]

        if function:
            parts.append(f"function={function}")

        if result is not None:
            parts.append(f"result={result}")

        if self.context:
            ctx = ", ".join(f"{key}={value}" for key, value in self.context.items())
            parts.append(f"context: {ctx}")

        super().__init__(" | ".join(parts))
