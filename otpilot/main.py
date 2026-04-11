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

import imaplib
import os
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import click
import requests
from rich.console import Console

from otpilot import __version__
from otpilot.clipboard import ClipboardError, copy_to_clipboard
from otpilot.config import CONFIG_FILE, config_exists, get_config, get_value, token_exists
from otpilot.gmail_client import GmailAuthError, NotAuthenticatedError, get_fetch_function
from otpilot.logger import LOG_FILE, get_logger

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
logger = get_logger(__name__)

PID_FILE: str = os.path.expanduser("~/.otpilot/otpilot.pid")

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
    logger.info("Hotkey trigger received.")
    try:
        fetch_fn = get_fetch_function()
        emails = fetch_fn()
    except NotAuthenticatedError:
        notify("OTPilot", "Please re-authenticate. Run: otpilot setup")
        logger.warning("Hotkey fetch failed: not authenticated.")
        return
    except GmailAuthError:
        notify("OTPilot", "Authentication error. Run: otpilot setup")
        logger.warning("Hotkey fetch failed: Gmail auth error.")
        return
    except Exception as exc:
        notify("OTPilot Error", f"Could not fetch emails: {exc}")
        logger.exception("Hotkey fetch failed with exception.")
        return

    otp = extract_otp(emails)

    if otp is None:
        notify("OTPilot", "No OTP found in recent emails.")
        logger.info("No OTP found in recent emails.")
        return

    try:
        copy_to_clipboard(otp)
    except ClipboardError as exc:
        notify("OTPilot Error", str(exc))
        logger.warning("Clipboard copy failed: %s", exc)
        return
    logger.info("OTP copied to clipboard.")

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

    try:
        from otpilot.history import save_entry

        sender, subject = _find_email_metadata(emails, otp)
        save_entry(otp, sender=sender, subject=subject)
        logger.debug("OTP history entry saved.")
    except Exception:
        logger.exception("Failed to save OTP history entry.")


def _cleanup() -> None:
    """Stop background listeners and tray resources.

    Returns:
        None: This function does not return a value.
    """
    global _listener, _tray
    logger.info("OTPilot shutting down.")
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


def _find_email_metadata(emails: List[Dict[str, Any]], otp: str) -> Tuple[str, str]:
    """Find sender and subject for the email that contains the OTP.

    Args:
        emails (list): List of email dictionaries.
        otp (str): OTP value to match against email content.

    Returns:
        Tuple[str, str]: ``(sender, subject)`` when a match is found, else empty strings.
    """
    for email in emails:
        subject = str(email.get("subject", ""))
        body = str(email.get("body", ""))
        if otp in subject or otp in body:
            sender = str(email.get("sender", ""))
            return sender, subject
    return "", ""


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
    log_path = LOG_FILE
    pid_path = PID_FILE
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
    logger.info("OTPilot starting.")

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
            logger.warning("System tray unavailable on this platform.")
            _tray = None
            _block_forever_until_signal()
            return

    logger.warning("System tray unavailable on this platform.")
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
def stop() -> None:
    """Stop the OTPilot background service.

    Returns:
        None: This command does not return a value.

    Raises:
        None: Errors are handled and reported to the user.
    """
    if not os.path.exists(PID_FILE):
        click.echo("OTPilot is not running.")
        return

    try:
        with open(PID_FILE, "r", encoding="utf-8") as pid_file:
            pid_str = pid_file.read().strip()
            pid = int(pid_str)
    except (OSError, ValueError):
        click.echo("Could not read PID file. Please remove it manually.")
        return

    try:
        os.kill(pid, signal.SIGTERM)
        click.echo("OTPilot stop signal sent.")
        os.remove(PID_FILE)
    except ProcessLookupError:
        os.remove(PID_FILE)
        click.echo("No running OTPilot process found. Removed stale PID file.")
    except PermissionError:
        click.echo("Permission denied while trying to stop OTPilot.")


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
def doctor() -> None:
    """Run diagnostic checks to validate OTPilot environment health.

    Returns:
        None: This command does not return a value.
    """
    from otpilot.token_store import load_app_password, load_token

    console.print("[bold]OTPilot Doctor[/bold]")
    console.print("Running diagnostics...")

    passed = 0
    warnings = 0
    failed = 0

    auth_mode: Optional[str] = None
    gmail_reachable: Optional[bool] = None
    imap_reachable: Optional[bool] = None

    try:
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 10):
            console.print(f"[green]✓[/green] Python {version} — OK")
            passed += 1
        else:
            console.print(f"[red]✗[/red] Python {version} — OTPilot requires 3.10+")
            failed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Python version: unexpected error — {exc}")
        failed += 1

    try:
        if config_exists():
            console.print(f"[green]✓[/green] Config file found at {CONFIG_FILE}")
            passed += 1
        else:
            console.print("[red]✗[/red] Config file missing — run [bold]otpilot setup[/bold]")
            failed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Config file exists: unexpected error — {exc}")
        failed += 1

    try:
        auth_mode = get_value("auth_mode")
        console.print(f"[green]✓[/green] Auth mode: {auth_mode}")
        passed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Auth mode: unexpected error — {exc}")
        failed += 1

    try:
        if token_exists():
            console.print("[green]✓[/green] Credential stored")
            passed += 1
        else:
            console.print("[red]✗[/red] No credential found — run [bold]otpilot setup[/bold]")
            failed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Token stored: unexpected error — {exc}")
        failed += 1

    if auth_mode in {"firebase", "credentials"}:
        try:
            token_payload = load_token() or {}
            expires_at = token_payload.get("expires_at")
            if not expires_at:
                console.print(
                    "[yellow]⚠[/yellow]  Token expiry unknown — no expires_at stored"
                )
                warnings += 1
            else:
                now = time.time()
                expires_at_int = int(expires_at)
                delta = expires_at_int - now
                if delta < 0:
                    minutes_ago = int((abs(delta) + 59) // 60)
                    console.print(
                        "[red]✗[/red] Token expired "
                        f"{minutes_ago} minutes ago — run [bold]otpilot fetch[/bold] "
                        "to trigger silent refresh or [bold]otpilot setup[/bold] to re-authenticate"
                    )
                    failed += 1
                elif delta <= 5 * 60:
                    minutes_left = int((delta + 59) // 60)
                    console.print(
                        "[yellow]⚠[/yellow]  Token expires in "
                        f"{minutes_left} minutes — will auto-refresh on next fetch"
                    )
                    warnings += 1
                else:
                    minutes_left = int((delta + 59) // 60)
                    console.print(f"[green]✓[/green] Token valid — expires in {minutes_left} minutes")
                    passed += 1
        except Exception as exc:
            console.print(f"[red]✗[/red] Token expiry: unexpected error — {exc}")
            failed += 1

        try:
            token_payload = load_token() or {}
            refresh_token = str(token_payload.get("refresh_token", "")).strip()
            if refresh_token:
                console.print("[green]✓[/green] Refresh token stored — silent renewal enabled")
                passed += 1
            else:
                console.print(
                    "[red]✗[/red] No refresh token — token cannot be silently renewed. "
                    "Re-run [bold]otpilot setup[/bold] to fix this"
                )
                failed += 1
        except Exception as exc:
            console.print(f"[red]✗[/red] Refresh token present: unexpected error — {exc}")
            failed += 1

        try:
            requests.get("https://gmail.googleapis.com", timeout=5)
            console.print("[green]✓[/green] Gmail API reachable")
            passed += 1
            gmail_reachable = True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            console.print("[red]✗[/red] Gmail API unreachable — check your internet connection")
            failed += 1
            gmail_reachable = False
        except Exception as exc:
            console.print(f"[red]✗[/red] Gmail API reachability: unexpected error — {exc}")
            failed += 1

    if auth_mode == "imap":
        host = ""
        port = 993
        try:
            host = str(get_value("imap_host", ""))
            port = int(get_value("imap_port", 993) or 993)
            _ = get_value("imap_user", "")
            previous_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(5)
            client: Optional[imaplib.IMAP4_SSL] = None
            try:
                client = imaplib.IMAP4_SSL(host, port)
                console.print(f"[green]✓[/green] IMAP server {host}:{port} reachable")
                passed += 1
                imap_reachable = True
            finally:
                if client is not None:
                    try:
                        client.logout()
                    except Exception:
                        pass
                socket.setdefaulttimeout(previous_timeout)
        except (OSError, socket.timeout, imaplib.IMAP4.error):
            console.print(
                f"[red]✗[/red] IMAP server {host}:{port} unreachable — check your internet connection or imap settings"
            )
            failed += 1
            imap_reachable = False
        except Exception as exc:
            console.print(f"[red]✗[/red] IMAP connectivity: unexpected error — {exc}")
            failed += 1

        try:
            app_password = load_app_password()
            if app_password:
                console.print("[green]✓[/green] App password stored")
                passed += 1
            else:
                console.print("[red]✗[/red] App password missing — run [bold]otpilot setup[/bold]")
                failed += 1
        except Exception as exc:
            console.print(f"[red]✗[/red] App password stored: unexpected error — {exc}")
            failed += 1

    try:
        hotkey = get_value("hotkey", "")
        if hotkey == "":
            console.print("[yellow]⚠[/yellow]  Hotkey is empty — run [bold]otpilot hotkey[/bold]")
            warnings += 1
        else:
            console.print(f"[green]✓[/green] Hotkey configured: {hotkey}")
            passed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Hotkey configured: unexpected error — {exc}")
        failed += 1

    try:
        if _HOTKEY_LISTENER_AVAILABLE:
            console.print("[green]✓[/green] Hotkey listener available")
            passed += 1
        else:
            console.print(
                "[yellow]⚠[/yellow]  Hotkey listener unavailable on this platform — OTPilot will run without hotkey support"
            )
            warnings += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Hotkey listener available: unexpected error — {exc}")
        failed += 1

    try:
        if _TRAY_AVAILABLE:
            console.print("[green]✓[/green] System tray available")
            passed += 1
        else:
            console.print(
                "[yellow]⚠[/yellow]  System tray unavailable — OTPilot will run headlessly without a tray icon"
            )
            warnings += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] System tray available: unexpected error — {exc}")
        failed += 1

    try:
        if not os.path.exists(PID_FILE):
            console.print(
                "[yellow]⚠[/yellow]  OTPilot is not running — use [bold]otpilot start[/bold]"
            )
            warnings += 1
        else:
            with open(PID_FILE, "r", encoding="utf-8") as pid_file:
                pid_str = pid_file.read().strip()
                pid = int(pid_str)
            try:
                os.kill(pid, 0)
                console.print(f"[green]✓[/green] OTPilot is running (PID {pid})")
                passed += 1
            except ProcessLookupError:
                console.print(
                    "[yellow]⚠[/yellow]  Stale PID file found "
                    f"(process {pid} is gone) — run [bold]otpilot stop[/bold] to clean up"
                )
                warnings += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] OTPilot process running: unexpected error — {exc}")
        failed += 1

    try:
        latest = _check_for_update()
        if latest:
            console.print(f"[yellow]⚠[/yellow]  Update available: v{latest} — run [bold]otpilot update[/bold]")
            warnings += 1
        else:
            if (auth_mode in {"firebase", "credentials"} and gmail_reachable is False) or (
                auth_mode == "imap" and imap_reachable is False
            ):
                console.print(
                    "[dim]  Could not check for updates (no internet or PyPI unreachable)[/dim]"
                )
            else:
                console.print(f"[green]✓[/green] OTPilot v{__version__} is up to date")
                passed += 1
    except Exception as exc:
        console.print(f"[red]✗[/red] Update available: unexpected error — {exc}")
        failed += 1

    console.print(f"[bold]{passed} passed   {warnings} warnings   {failed} failed[/bold]")
    if failed > 0:
        console.print(
            "[dim]Run [bold]otpilot setup[/bold] to fix authentication issues, or [bold]otpilot logs[/bold] for runtime errors.[/dim]"
        )
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
@click.option("--clear", is_flag=True, help="Clear stored OTP history.")
@click.option("--count", type=int, default=None, help="Number of entries to show.")
def history(clear: bool, count: Optional[int]) -> None:
    """Display or clear OTP history entries.

    Args:
        clear (bool): Whether to clear the stored history.
        count (Optional[int]): Optional maximum number of entries to show.

    Returns:
        None: This command does not return a value.
    """
    from rich.table import Table

    from otpilot.history import clear_history, load_history

    if clear:
        if click.confirm("Clear OTP history?", default=False):
            clear_history()
            click.echo("OTP history cleared.")
        return

    entries = load_history()
    if count is not None:
        entries = entries[: max(0, count)]

    if not entries:
        click.echo("No OTP history available.")
        return

    table = Table(title="OTP History", show_lines=False)
    table.add_column("Time", style="dim")
    table.add_column("OTP")
    table.add_column("Sender")
    table.add_column("Subject")

    for entry in entries:
        table.add_row(
            str(entry.get("timestamp", "")),
            str(entry.get("otp", "")),
            str(entry.get("sender", "")),
            str(entry.get("subject", "")),
        )

    console.print(table)


@cli.command()
@click.option("--lines", default=50)
def logs(lines: int) -> None:
    """Show the most recent log lines.

    Args:
        lines (int): Number of log lines to display.

    Returns:
        None: This command does not return a value.
    """
    if not os.path.exists(LOG_FILE):
        click.echo("No logs found.")
        return
    try:
        if os.path.getsize(LOG_FILE) == 0:
            click.echo("No logs found.")
            return
    except OSError:
        click.echo("Unable to read log file.")
        return

    if sys.platform.startswith("win"):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as log_file:
                content_lines = log_file.readlines()
        except OSError:
            click.echo("Unable to read log file.")
            return
        tail_lines = content_lines[-lines:] if lines > 0 else []
        click.echo("".join(tail_lines), nl=False)
        return

    result = subprocess.run(
        ["tail", "-n", str(lines), LOG_FILE],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        click.echo("Unable to read log file.")
        return
    click.echo(result.stdout, nl=False)


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
