"""Entry point for OTPilot.

Starts the system tray icon and global hotkey listener. On hotkey
trigger, fetches recent emails, extracts the OTP, copies it to the
clipboard, and shows a desktop notification.
"""

import signal
import subprocess
import sys
import threading
import time
from typing import Optional

import click
import requests
from rich.console import Console

from otpilot import __version__
from otpilot.clipboard import ClipboardError, copy_to_clipboard
from otpilot.config import config_exists, get_config, token_exists
from otpilot.gmail_client import GmailAuthError, NotAuthenticatedError, fetch_recent_emails
try:
    from otpilot.hotkey_listener import HotkeyListener
    _HOTKEY_LISTENER_AVAILABLE = True
except Exception:
    HotkeyListener = None  # type: ignore[assignment]
    _HOTKEY_LISTENER_AVAILABLE = False
from otpilot.notifier import notify
from otpilot.otp_extractor import extract_otp
try:
    from otpilot.tray import TrayApp

    _TRAY_AVAILABLE = True
except Exception:
    TrayApp = None  # type: ignore[assignment]
    _TRAY_AVAILABLE = False


console = Console()

# Global references for cleanup
_listener: Optional[object] = None
_tray: Optional[object] = None


def _fetch_latest_version() -> Optional[str]:
    """Fetch the latest OTPilot version from PyPI."""
    try:
        response = requests.get("https://pypi.org/pypi/otpilot/json", timeout=5)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None

    return payload.get("info", {}).get("version")


def _is_update_available(current: str, latest: str) -> bool:
    """Compare current vs latest version strings."""
    try:
        from packaging.version import Version

        return Version(latest) > Version(current)
    except Exception:
        def _version_tuple(value: str) -> tuple:
            parts = []
            for piece in value.replace("-", ".").split("."):
                if piece.isdigit():
                    parts.append(int(piece))
                else:
                    digits = "".join(ch for ch in piece if ch.isdigit())
                    if digits:
                        parts.append(int(digits))
            return tuple(parts)

        return _version_tuple(latest) > _version_tuple(current)


def _check_for_update() -> Optional[str]:
    """Return latest version string if an update is available."""
    latest = _fetch_latest_version()
    if not latest:
        return None
    if _is_update_available(__version__, latest):
        return latest
    return None


def _on_hotkey_triggered() -> None:
    """Callback invoked when the user presses the configured hotkey.

    Fetches recent emails, extracts the OTP, copies it to clipboard,
    and shows a notification. All errors are caught and surfaced as
    notifications — the service never crashes silently.
    """
    try:
        emails = fetch_recent_emails()
    except NotAuthenticatedError:
        notify("OTPilot", "Please re-authenticate. Run: otpilot setup")
        return
    except GmailAuthError:
        notify("OTPilot", "Authentication error. Run: otpilot setup")
        return
    except Exception as exc:
        notify("OTPilot Error", f"Could not fetch emails: {exc}")
        return

    otp = extract_otp(emails)

    if otp is None:
        notify("OTPilot", "No OTP found in recent emails.")
        return

    try:
        copy_to_clipboard(otp)
    except ClipboardError as exc:
        notify("OTPilot Error", str(exc))
        return

    config = get_config()
    if config.get("auto_paste", False):
        try:
            from pynput import keyboard

            time.sleep(0.1)
            controller = keyboard.Controller()
            modifier = keyboard.Key.cmd if sys.platform == "darwin" else keyboard.Key.ctrl
            with controller.pressed(modifier):
                controller.press("v")
                controller.release("v")
        except Exception:
            # Fall back silently to clipboard copy
            pass

    if config.get("notify_on_copy", True):
        # Mask middle digits for privacy in notification
        masked = otp
        if config.get("mask_otp_in_notification", True) and len(otp) > 4:
            masked = otp[:2] + "•" * (len(otp) - 4) + otp[-2:]
        notify("OTPilot", f"OTP copied: {masked}")


def _cleanup() -> None:
    """Clean up listener and tray on exit."""
    global _listener, _tray
    if _listener is not None:
        _listener.stop()
        _listener = None
    if _tray is not None:
        _tray.stop()
        _tray = None


def _block_forever_until_signal() -> None:
    """Keep the service alive when tray UI is unavailable."""
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _cleanup()


def run() -> None:
    """Start the OTPilot background service.

    Initializes the hotkey listener in a background thread and starts
    the system tray icon in the main thread (required by pystray on
    macOS).
    """
    global _listener, _tray

    # First-run check
    if not config_exists() or not token_exists():
        from otpilot.setup_wizard import run_setup
        run_setup()
        return

    config = get_config()
    hotkey_str = config.get("hotkey", "ctrl+shift+o")

    if config.get("check_updates_on_start", True):
        def _background_update_check() -> None:
            latest = _check_for_update()
            if latest:
                notify("OTPilot", f"OTPilot update available: v{latest}. Run: otpilot update")

        threading.Thread(target=_background_update_check, daemon=True).start()

    # Set up signal handlers for clean exit
    def _signal_handler(sig: int, frame: object) -> None:
        _cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Start hotkey listener in background thread (if available)
    if _HOTKEY_LISTENER_AVAILABLE and HotkeyListener is not None:
        try:
            _listener = HotkeyListener(hotkey_str, _on_hotkey_triggered)
            _listener.start()
            notify("OTPilot", f"Running! Press {hotkey_str} to fetch OTP.")
        except Exception:
            console.print("[yellow]Hotkey listener unavailable on this platform[/yellow]")
            notify("OTPilot", "Running without hotkey support.")
    else:
        console.print("[yellow]Hotkey listener unavailable on this platform[/yellow]")
        notify("OTPilot", "Running without hotkey support.")

    # Start tray in main thread (blocks until quit). If unavailable,
    # continue running without tray support.
    if _TRAY_AVAILABLE and TrayApp is not None:
        try:
            _tray = TrayApp(on_quit=_cleanup)
            _tray.run()
            return
        except Exception:
            print("System tray unavailable on this platform")
            _tray = None
            _block_forever_until_signal()
            return

    print("System tray unavailable on this platform")
    _block_forever_until_signal()


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """OTPilot — Background OTP copier for Gmail."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def setup() -> None:
    """Run or re-run the interactive setup wizard."""
    from otpilot.setup_wizard import run_setup
    run_setup()


@cli.command()
def start() -> None:
    """Start the OTPilot background service."""
    run()


@cli.command()
def status() -> None:
    """Show the current OTPilot status."""
    from otpilot.config import CONFIG_FILE

    authenticated = token_exists()
    has_config = config_exists()

    console.print()
    console.print("[bold]OTPilot Status[/bold]")
    console.print(f"  Version:        {__version__}")
    console.print(
        f"  Authenticated:  {'[green]Yes[/green]' if authenticated else '[red]No[/red]'}"
    )


    if has_config:
        config = get_config()
        console.print(f"  Hotkey:         {config.get('hotkey', 'not set')}")
        console.print(
            f"  Notifications:  {'On' if config.get('notify_on_copy', True) else 'Off'}"
        )
        console.print(f"  Max OTP age:    {config.get('otp_max_age_minutes', 10)} min")
        console.print(f"  Fetch count:    {config.get('email_fetch_count', 10)} emails")
    else:
        console.print("  Config:         [yellow]Not configured[/yellow]")

    console.print(f"  Config path:    {CONFIG_FILE}")
    console.print()

    if not authenticated or not has_config:
        console.print("  [dim]Run [bold]otpilot setup[/bold] to get started.[/dim]\n")


@cli.command()
@click.option("--set", "hotkey_value", default=None, help='Set hotkey directly, e.g. --set "ctrl+shift+o"')
def hotkey(hotkey_value: str) -> None:
    """View or change the global hotkey."""
    from otpilot.config import set_value, get_value
    from otpilot.hotkey_listener import capture_hotkey

    current = get_value("hotkey", "not set")

    if hotkey_value is not None:
        # Direct set via --set flag
        set_value("hotkey", hotkey_value)
        console.print(f"\n  [green]✓[/green] Hotkey changed: [dim]{current}[/dim] → [bold]{hotkey_value}[/bold]")
        console.print("  [dim]Restart OTPilot for changes to take effect.[/dim]\n")
        return

    console.print(f"\n  Current hotkey: [bold]{current}[/bold]\n")

    if not click.confirm("  Change it?", default=True):
        console.print()
        return

    console.print(
        "\n  Press your desired hotkey combination now...\n"
        "  [dim](Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)[/dim]\n"
    )
    new_hotkey = capture_hotkey()
    set_value("hotkey", new_hotkey)
    console.print(f"  [green]✓[/green] Hotkey changed: [dim]{current}[/dim] → [bold]{new_hotkey}[/bold]")
    console.print("  [dim]Restart OTPilot for changes to take effect.[/dim]\n")


@cli.command()
def version() -> None:
    """Print the OTPilot version."""
    click.echo(f"OTPilot v{__version__}")


@cli.command()
def update() -> None:
    """Check for and install OTPilot updates."""
    latest = _fetch_latest_version()
    if latest is None:
        click.echo("Could not check for updates. Please try again later.")
        return

    if not _is_update_available(__version__, latest):
        click.echo(f"OTPilot is up to date (v{__version__})")
        return

    click.echo(f"Update available: v{__version__} → v{latest}")
    click.echo("Run: pip install --upgrade otpilot")

    if not click.confirm("Update now?", default=True):
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "otpilot"]
    )
    if result.returncode == 0:
        click.echo("Updated successfully. Restart OTPilot.")
    else:
        click.echo("Update failed. Please run: pip install --upgrade otpilot")


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
