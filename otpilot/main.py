"""CLI and runtime entry point for OTPilot.

This module wires together OTPilot's configuration, Gmail fetching, OTP
extraction, clipboard integration, notifications, tray UI, and command-line
interface. It is the operational core that starts background services and
exposes user-facing CLI commands.

Key exports:
    run: Start the OTPilot background service.
    cli: Root Click command group for OTPilot commands.
    main: Console script entry point.
"""

import os
import shutil
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

# Global references for cleanup.
_listener: Optional[object] = None
_tray: Optional[object] = None


def _fetch_latest_version() -> Optional[str]:
    """Fetch the latest OTPilot version string from PyPI metadata.

    Returns:
        Optional[str]: Latest published version string, or ``None`` if lookup
            fails.
    """
    try:
        # Query the PyPI JSON API for package metadata.
        response = requests.get("https://pypi.org/pypi/otpilot/json", timeout=5)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None

    return payload.get("info", {}).get("version")


def _is_update_available(current: str, latest: str) -> bool:
    """Compare installed and latest version strings.

    Args:
        current (str): Currently installed OTPilot version.
        latest (str): Latest available OTPilot version.

    Returns:
        bool: ``True`` when ``latest`` is newer than ``current``.
    """
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
                    # Extract digits from labels like "rc1" for fallback compare.
                    digits = "".join(ch for ch in piece if ch.isdigit())
                    if digits:
                        parts.append(int(digits))
            return tuple(parts)

        return _version_tuple(latest) > _version_tuple(current)


def _check_for_update() -> Optional[str]:
    """Return latest version only when an update is available.

    Returns:
        Optional[str]: Newer version string when available, otherwise ``None``.
    """
    latest = _fetch_latest_version()
    if not latest:
        return None
    if _is_update_available(__version__, latest):
        return latest
    return None


def _on_hotkey_triggered() -> None:
    """Handle OTP retrieval workflow triggered by hotkey or CLI.

    Returns:
        None: This function does not return a value.
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
            # Auto-paste is optional; clipboard copy already succeeded.
            pass

    if config.get("notify_on_copy", True):
        # Mask middle digits for privacy in notification popups.
        masked = otp
        if config.get("mask_otp_in_notification", True) and len(otp) > 4:
            masked = otp[:2] + "•" * (len(otp) - 4) + otp[-2:]
        notify("OTPilot", f"OTP copied: {masked}")


def _cleanup() -> None:
    """Stop background listeners and tray resources.

    Returns:
        None: This function does not return a value.
    """
    global _listener, _tray
    if _listener is not None:
        _listener.stop()
        _listener = None
    if _tray is not None:
        _tray.stop()
        _tray = None


def _block_forever_until_signal() -> None:
    """Block process lifetime in environments without tray UI.

    Returns:
        None: This function does not return a value.
    """
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        _cleanup()


def _print_feedback_prompt() -> None:
    """Print feedback prompt for users.

    Returns:
        None: This function does not return a value.
    """
    console.print("Feedback? github.com/codewithjenil/otpilot/discussions")


def _select_background_python() -> str:
    """Select the Python executable for background launch.

    Returns:
        str: Path to the Python executable suitable for background use.
    """
    if sys.platform == "darwin":
        pythonw = shutil.which("pythonw")
        if pythonw:
            return pythonw
    return sys.executable


def _launch_detached_background() -> subprocess.Popen:
    """Launch OTPilot as a detached background process.

    Returns:
        subprocess.Popen: Handle to the newly launched background process.
    """
    log_path = os.path.expanduser("~/.otpilot/otpilot.log")
    pid_path = os.path.expanduser("~/.otpilot/otpilot.pid")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    env = os.environ.copy()
    env["OTPILOT_BACKGROUND"] = "1"

    python_exec = _select_background_python()
    args = [python_exec, "-m", "otpilot.main", "start"]

    log_file = open(log_path, "a", encoding="utf-8")
    try:
        popen_kwargs = {
            "close_fds": True,
            "stdout": log_file,
            "stderr": log_file,
            "env": env,
        }

        if sys.platform.startswith("win"):
            popen_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_kwargs["start_new_session"] = True

        process = subprocess.Popen(args, **popen_kwargs)
    finally:
        log_file.close()

    with open(pid_path, "w", encoding="utf-8") as pid_file:
        pid_file.write(str(process.pid))

    return process


def run() -> None:
    """Start the OTPilot background service.

    Returns:
        None: This function does not return a value.

    Raises:
        None: Startup errors are handled internally with notifications/logging.
    """
    global _listener, _tray

    # Force first-run setup when either config or auth token is missing.
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

    # Handle termination signals so tray and listener are always released.
    def _signal_handler(sig: int, frame: object) -> None:
        _cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Start global hotkey listener when platform backend is available.
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

    # Start tray on main thread; otherwise keep process alive without UI.
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


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Root OTPilot command group.

    Args:
        ctx (click.Context): Click context for command dispatch.

    Returns:
        None: This command callback does not return a value.

    Raises:
        None: Click handles CLI-level errors.
    """
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
def setup() -> None:
    """Run or re-run the interactive setup wizard.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Setup errors are handled within wizard flow.
    """
    from otpilot.setup_wizard import run_setup

    run_setup()
    _print_feedback_prompt()


@cli.command()
def start() -> None:
    """Start the OTPilot background service.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Runtime errors are handled during service startup.
    """
    if os.environ.get("OTPILOT_BACKGROUND") != "1":
        process = _launch_detached_background()
        console.print("OTPilot started in background. Press your hotkey to fetch an OTP.")
        console.print(f"PID: {process.pid}")
        _print_feedback_prompt()
        return

    run()
    _print_feedback_prompt()


@cli.command()
def fetch() -> None:
    """Trigger a one-time OTP fetch using current settings.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Runtime errors are handled inside the fetch workflow.
    """
    _on_hotkey_triggered()
    click.echo("OTP fetch triggered.")
    _print_feedback_prompt()


@cli.command()
def status() -> None:
    """Print current OTPilot configuration and authentication status.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Missing state is displayed to the user instead of raising.
    """
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
    _print_feedback_prompt()


@cli.command()
@click.option("--set", "hotkey_value", default=None, help='Set hotkey directly, e.g. --set "ctrl+shift+o"')
def hotkey(hotkey_value: Optional[str]) -> None:
    """View or update the configured global hotkey.

    Args:
        hotkey_value (Optional[str]): Optional direct hotkey value from
            ``--set``.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Input errors are handled interactively.
    """
    from otpilot.config import get_value, set_value
    from otpilot.hotkey_listener import capture_hotkey

    current = get_value("hotkey", "not set")

    if hotkey_value is not None:
        set_value("hotkey", hotkey_value)
        console.print(f"\n  [green]✓[/green] Hotkey changed: [dim]{current}[/dim] → [bold]{hotkey_value}[/bold]")
        console.print("  [dim]Restart OTPilot for changes to take effect.[/dim]\n")
        _print_feedback_prompt()
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
    _print_feedback_prompt()


@cli.command()
def version() -> None:
    """Print the installed OTPilot version.

    Returns:
        None: This command does not return a value.

    Raises:
        None: This command does not raise application-level exceptions.
    """
    click.echo(f"OTPilot v{__version__}")
    _print_feedback_prompt()


@cli.command()
def update() -> None:
    """Check for and optionally install OTPilot updates via pip.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Update failures are reported to the user.
    """
    latest = _fetch_latest_version()
    if latest is None:
        click.echo("Could not check for updates. Please try again later.")
        _print_feedback_prompt()
        return

    if not _is_update_available(__version__, latest):
        click.echo(f"OTPilot is up to date (v{__version__})")
        _print_feedback_prompt()
        return

    click.echo(f"Update available: v{__version__} → v{latest}")
    click.echo("Run: pip install --upgrade otpilot")

    if not click.confirm("Update now?", default=True):
        _print_feedback_prompt()
        return

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "otpilot"]
    )
    if result.returncode == 0:
        click.echo("Updated successfully. Restart OTPilot.")
    else:
        click.echo("Update failed. Please run: pip install --upgrade otpilot")
    _print_feedback_prompt()


def main() -> None:
    """Invoke the OTPilot CLI entry point.

    Returns:
        None: This function does not return a value.

    Raises:
        None: Command errors are managed by Click.
    """
    cli()


if __name__ == "__main__":
    main()
