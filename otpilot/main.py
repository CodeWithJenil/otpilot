"""Entry point for OTPilot.

Starts the system tray icon and global hotkey listener. On hotkey
trigger, fetches recent emails, extracts the OTP, copies it to the
clipboard, and shows a desktop notification.
"""

import signal
import sys
import threading
from typing import Optional

import click
from rich.console import Console

from otpilot import __version__
from otpilot.clipboard import ClipboardError, copy_to_clipboard
from otpilot.config import config_exists, get_config, token_exists
from otpilot.gmail_client import CredentialsNotFoundError, GmailAuthError, NotAuthenticatedError, fetch_recent_emails
from otpilot.hotkey_listener import HotkeyListener
from otpilot.notifier import notify
from otpilot.otp_extractor import extract_otp
from otpilot.tray import TrayApp


console = Console()

# Global references for cleanup
_listener: Optional[HotkeyListener] = None
_tray: Optional[TrayApp] = None


def _on_hotkey_triggered() -> None:
    """Callback invoked when the user presses the configured hotkey.

    Fetches recent emails, extracts the OTP, copies it to clipboard,
    and shows a notification. All errors are caught and surfaced as
    notifications — the service never crashes silently.
    """
    try:
        emails = fetch_recent_emails()
    except CredentialsNotFoundError:
        notify("OTPilot", "credentials.json not found. Run `otpilot setup` again.")
        return
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
    if config.get("notify_on_copy", True):
        # Mask middle digits for privacy in notification
        if len(otp) > 4:
            masked = otp[:2] + "•" * (len(otp) - 4) + otp[-2:]
        else:
            masked = otp
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


def run() -> None:
    """Start the OTPilot background service.

    Initializes the hotkey listener in a background thread and starts
    the system tray icon in the main thread (required by pystray on
    macOS).
    """
    global _listener, _tray

    # First-run check
    from otpilot.credentials import credentials_exist
    if not config_exists() or not token_exists() or not credentials_exist():
        from otpilot.setup_wizard import run_setup
        run_setup()
        return

    config = get_config()
    hotkey_str = config.get("hotkey", "ctrl+shift+o")

    # Set up signal handlers for clean exit
    def _signal_handler(sig: int, frame: object) -> None:
        _cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Start hotkey listener in background thread
    _listener = HotkeyListener(hotkey_str, _on_hotkey_triggered)
    _listener.start()

    notify("OTPilot", f"Running! Press {hotkey_str} to fetch OTP.")

    # Start tray in main thread (blocks until quit)
    _tray = TrayApp(on_quit=_cleanup)
    _tray.run()


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

    from otpilot.credentials import credentials_exist
    has_credentials = credentials_exist()
    console.print(
        f"  Credentials:    {'[green]Yes[/green]' if has_credentials else '[red]No[/red]'}"
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


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
