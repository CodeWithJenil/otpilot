"""Clipboard operations for OTPilot.

Wraps ``pyperclip`` with error handling so clipboard failures never crash
the application.
"""

import pyperclip


class ClipboardError(Exception):
    """Raised when a clipboard operation fails."""

    def __init__(self, message: str = "Could not access the clipboard.") -> None:
        super().__init__(message)


def copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard.

    Args:
        text: The string to copy.

    Raises:
        ClipboardError: If the clipboard is unavailable (e.g. no display
            server on Linux, or missing clipboard utilities).
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
