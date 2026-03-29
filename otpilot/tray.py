"""System tray icon and menu for OTPilot.

Uses ``pystray`` with a ``Pillow``-generated icon. Provides menu items
for settings, re-authentication, and quitting.
"""

import subprocess
import sys
import threading
from typing import Any, Callable, Optional

from PIL import Image, ImageDraw, ImageFont

try:
    from pystray import Icon, Menu, MenuItem

    _PYSTRAY_AVAILABLE = True
    _PYSTRAY_IMPORT_ERROR: Optional[Exception] = None
except ImportError as exc:
    Icon = Menu = MenuItem = None  # type: ignore[assignment]
    _PYSTRAY_AVAILABLE = False
    _PYSTRAY_IMPORT_ERROR = exc
except Exception as exc:
    Icon = Menu = MenuItem = None  # type: ignore[assignment]
    _PYSTRAY_AVAILABLE = False
    _PYSTRAY_IMPORT_ERROR = exc


def _ensure_pystray_available() -> None:
    if not _PYSTRAY_AVAILABLE:
        raise RuntimeError(
            "System tray unavailable on this platform"
        ) from _PYSTRAY_IMPORT_ERROR


def _create_icon_image() -> Image.Image:
    """Generate a simple tray icon programmatically with Pillow.

    Creates a 64×64 icon with a gradient background and "OTP" text.

    Returns:
        A Pillow ``Image`` object.
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a rounded rectangle background with a gradient-like effect
    # Base color: vibrant blue-purple
    for i in range(size):
        ratio = i / size
        r = int(67 + ratio * 30)
        g = int(56 + ratio * 20)
        b = int(202 - ratio * 30)
        draw.line([(0, i), (size - 1, i)], fill=(r, g, b, 230))

    # Apply circular mask for rounded look
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=14, fill=255)
    img.putalpha(mask)

    # Draw "OTP" text
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            font = ImageFont.load_default()

    text = "OTP"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - 2
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


def _open_settings_terminal() -> None:
    """Open a terminal window to change OTPilot settings interactively."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                ["osascript", "-e", 'tell app "Terminal" to do script "otpilot setup"'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k", "otpilot setup"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # Linux — try common terminal emulators
            for term in ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]:
                try:
                    subprocess.Popen(
                        [term, "-e", "otpilot setup"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    break
                except FileNotFoundError:
                    continue
    except Exception:
        pass  # Best-effort


def _reauth() -> None:
    """Re-run the OAuth authentication flow in a background thread."""
    def _do_reauth() -> None:
        try:
            from otpilot.gmail_client import run_oauth_flow
            from otpilot.notifier import notify

            run_oauth_flow()
            notify("OTPilot", "Re-authentication successful!")
        except Exception as exc:
            from otpilot.notifier import notify
            notify("OTPilot Error", f"Re-authentication failed: {exc}")

    thread = threading.Thread(target=_do_reauth, daemon=True)
    thread.start()


class TrayApp:
    """Manages the system tray icon and its menu.

    Args:
        on_quit: Callback invoked when the user selects "Quit" from the
            tray menu.
    """

    def __init__(self, on_quit: Optional[Callable[[], None]] = None) -> None:
        _ensure_pystray_available()
        self._on_quit = on_quit
        self._icon: Optional[Any] = None

    def _quit_action(self, icon: Any, item: Any) -> None:
        """Handle the Quit menu action."""
        if self._icon is not None:
            self._icon.stop()
        if self._on_quit is not None:
            self._on_quit()

    def _settings_action(self, icon: Any, item: Any) -> None:
        """Handle the Settings menu action."""
        _open_settings_terminal()

    def _reauth_action(self, icon: Any, item: Any) -> None:
        """Handle the Re-authenticate menu action."""
        _reauth()

    def run(self) -> None:
        """Start the system tray icon. Blocks the calling thread.

        This should be called from the main thread, as ``pystray``
        requires it on macOS.
        """
        _ensure_pystray_available()
        menu = Menu(
            MenuItem("OTPilot", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Settings", self._settings_action),
            MenuItem("Re-authenticate", self._reauth_action),
            Menu.SEPARATOR,
            MenuItem("Quit", self._quit_action),
        )

        self._icon = Icon(
            name="OTPilot",
            icon=_create_icon_image(),
            title="OTPilot — Press hotkey to fetch OTP",
            menu=menu,
        )

        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon programmatically."""
        if self._icon is not None:
            self._icon.stop()
