"""Desktop notification delivery for OTPilot.

This module provides best-effort desktop notifications across macOS,
Windows, and Linux. In OTPilot, it surfaces user-visible runtime events such
as copied OTPs, auth issues, and update availability.

Key exports:
    notify: Cross-platform notification entry point.
"""

import subprocess
import sys


def _notify_macos(title: str, message: str) -> None:
    """Send a macOS notification using ``osascript``.

    Args:
        title (str): Notification title.
        message (str): Notification body text.

    Returns:
        None: This helper does not return a value.
    """
    script = f'display notification "{message}" with title "{title}"'
    # Run AppleScript in a detached process so notification calls are non-blocking.
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _notify_plyer(title: str, message: str) -> None:
    """Send a desktop notification via ``plyer``.

    Args:
        title (str): Notification title.
        message (str): Notification body text.

    Returns:
        None: This helper does not return a value.
    """
    from plyer import notification as plyer_notification

    plyer_notification.notify(
        title=title,
        message=message,
        app_name="OTPilot",
        timeout=4,
    )


def notify(title: str, message: str) -> None:
    """Display a desktop notification using platform-appropriate backend.

    Args:
        title (str): Notification title.
        message (str): Notification body text.

    Returns:
        None: This function does not return a value.

    Raises:
        None: Backend failures are intentionally swallowed as best-effort.
    """
    try:
        if sys.platform == "darwin":
            _notify_macos(title, message)
        else:
            _notify_plyer(title, message)
    except Exception:
        # Notifications are non-critical; never let failures break main flow.
        pass
