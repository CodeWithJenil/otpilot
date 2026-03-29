"""System tray UI integration for OTPilot.

This module builds and runs the tray icon/menu using ``pystray`` and a
programmatically generated ``Pillow`` icon. Within OTPilot, it provides user
entry points for settings, re-authentication, and graceful shutdown.

Key exports:
    TrayApp: System tray controller for icon lifecycle and menu actions.
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
    """Raise when tray support is unavailable in the current environment."""
    if not _PYSTRAY_AVAILABLE:
        raise RuntimeError(
            "System tray unavailable on this platform"
        ) from _PYSTRAY_IMPORT_ERROR


def _create_icon_image() -> Image.Image:
    """Generate a tray icon image for OTPilot.

    Returns:
        Image.Image: RGBA icon image used by ``pystray``.
    """
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a vertical gradient by varying line color per y-coordinate.
    for i in range(size):
        ratio = i / size
        r = int(67 + ratio * 30)
        g = int(56 + ratio * 20)
        b = int(202 - ratio * 30)
        draw.line([(0, i), (size - 1, i)], fill=(r, g, b, 230))

    # Mask to rounded rectangle for a softer tray icon silhouette.
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=14, fill=255)
    img.putalpha(mask)

    # Render OTP glyphs using the first available font.
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
    """Open a terminal and launch ``otpilot setup`` for settings updates."""
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
            # Linux: try common terminal emulators until one succeeds.
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
        pass  # Best-effort only.


def _reauth() -> None:
    """Run re-authentication in a background thread and notify the result."""

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
    """Manage the OTPilot system tray icon and menu lifecycle.

    Responsibilities:
    - Build tray menu actions.
    - Start and stop the tray icon runtime.
    - Delegate settings and re-auth actions.

    Key attributes:
        _on_quit: Optional callback invoked when the user selects Quit.
        _icon: Active ``pystray.Icon`` instance when running.
    """

    def __init__(self, on_quit: Optional[Callable[[], None]] = None) -> None:
        """Initialize a tray application controller.

        Args:
            on_quit (Optional[Callable[[], None]]): Optional callback invoked
                after the tray icon stops via the Quit menu action.

        Returns:
            None: This constructor does not return a value.

        Raises:
            RuntimeError: If ``pystray`` is unavailable on this platform.
        """
        _ensure_pystray_available()
        self._on_quit = on_quit
        self._icon: Optional[Any] = None

    def _quit_action(self, icon: Any, item: Any) -> None:
        """Handle the Quit tray menu action.

        Args:
            icon (Any): ``pystray`` icon instance from callback.
            item (Any): Selected menu item metadata.

        Returns:
            None: This callback does not return a value.
        """
        if self._icon is not None:
            self._icon.stop()
        if self._on_quit is not None:
            self._on_quit()

    def _settings_action(self, icon: Any, item: Any) -> None:
        """Handle the Settings tray menu action.

        Args:
            icon (Any): ``pystray`` icon instance from callback.
            item (Any): Selected menu item metadata.

        Returns:
            None: This callback does not return a value.
        """
        _open_settings_terminal()

    def _reauth_action(self, icon: Any, item: Any) -> None:
        """Handle the Re-authenticate tray menu action.

        Args:
            icon (Any): ``pystray`` icon instance from callback.
            item (Any): Selected menu item metadata.

        Returns:
            None: This callback does not return a value.
        """
        _reauth()

    def run(self) -> None:
        """Start the tray icon event loop.

        Returns:
            None: This method blocks until the tray icon exits.

        Raises:
            RuntimeError: If ``pystray`` is unavailable on this platform.
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
        """Stop the tray icon if running.

        Returns:
            None: This method does not return a value.

        Raises:
            None: Missing icon state is handled gracefully.
        """
        if self._icon is not None:
            self._icon.stop()
