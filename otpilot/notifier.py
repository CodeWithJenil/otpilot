"""Desktop notifications for OTPilot.

Uses native OS notification mechanisms with graceful fallbacks:
- macOS: ``osascript`` (AppleScript)
- Windows / Linux: ``plyer``

Failures are silently ignored so the main application flow is never
interrupted.
"""

import subprocess
import sys


def _notify_macos(title: str, message: str) -> None:
    """Send a notification on macOS using osascript (AppleScript).

    Args:
        title: The notification title.
        message: The notification body text.
    """
    script = f'display notification "{message}" with title "{title}"'
    subprocess.Popen(
        ["osascript", "-e", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _notify_plyer(title: str, message: str) -> None:
    """Send a notification using plyer (Windows/Linux fallback).

    Args:
        title: The notification title.
        message: The notification body text.
    """
    from plyer import notification as plyer_notification

    plyer_notification.notify(
        title=title,
        message=message,
        app_name="OTPilot",
        timeout=4,
    )


def notify(title: str, message: str) -> None:
    """Show a desktop notification.

    Automatically selects the best notification backend for the
    current platform.

    Args:
        title: The notification title.
        message: The notification body text.
    """
    try:
        if sys.platform == "darwin":
            _notify_macos(title, message)
        else:
            _notify_plyer(title, message)
    except Exception:
        # Silent fail — notifications are best-effort
        pass
