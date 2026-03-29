"""Clipboard utilities for OTPilot.

This module wraps ``pyperclip`` to provide a stable copy API with
application-specific error handling. Within OTPilot, it is the final step in
OTP delivery before optional auto-paste and notifications.

Key exports:
    copy_to_clipboard: Copy extracted OTP text to the system clipboard.
    ClipboardError: Domain-specific clipboard failure exception.
"""

import pyperclip


class ClipboardError(Exception):
    """Error raised when clipboard operations fail in OTPilot.

    Attributes:
        args: Exception message tuple inherited from ``Exception``.
    """

    def __init__(self, message: str = "Could not access the clipboard.") -> None:
        """Initialize a clipboard error.

        Args:
            message (str): Human-readable clipboard failure description.

        Returns:
            None: This constructor does not return a value.

        Raises:
            None: The constructor itself does not raise additional exceptions.
        """
        super().__init__(message)


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Args:
        text (str): String content to copy.

    Returns:
        None: This function does not return a value.

    Raises:
        ClipboardError: If clipboard backends are unavailable or copy fails.
    """
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        raise ClipboardError(
            "Could not copy to clipboard. "
            "On Linux, make sure xclip or xsel is installed. "
            f"Details: {exc}"
        ) from exc
    except Exception as exc:
        raise ClipboardError(
            f"Unexpected clipboard error: {exc}"
        ) from exc
