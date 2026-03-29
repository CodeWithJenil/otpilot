"""Interactive first-run setup wizard for OTPilot."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from otpilot.config import DEFAULT_CONFIG, config_exists, get_config, save_config, token_exists

console = Console()


def _print_banner() -> None:
    banner_text = Text()
    banner_text.append("✈  ", style="bold cyan")
    banner_text.append("OTPilot Setup", style="bold white")
    banner_text.append(" ✈", style="bold cyan")

    console.print()
    console.print(Panel(banner_text, subtitle="[dim]Background OTP copier for Gmail[/dim]", border_style="bright_blue", padding=(1, 4)))
    console.print()


def _setup_auth() -> bool:
    console.print("[bold cyan]Step 1:[/bold cyan] Google Account Sign-In via Supabase\n")

    if token_exists():
        console.print("  [dim]An authentication token is already stored.[/dim]")
        if Confirm.ask("  Re-authenticate now?", default=False, console=console):
            pass
        else:
            console.print("  [green]✓[/green] Using existing token.\n")
            return True

    from otpilot.gmail_client import run_oauth_flow

    console.print("  Opening your browser for Gmail authorization...\n")
    try:
        run_oauth_flow()
        console.print("  [green]✓[/green] Authentication successful!\n")
        return True
    except Exception as exc:
        console.print(f"  [red]✗[/red] Authentication failed: {exc}\n")
        return False


def _capture_hotkey() -> str:
    from otpilot.hotkey_listener import capture_hotkey

    console.print("[bold cyan]Step 2:[/bold cyan] Configure Hotkey")
    console.print("  Press your desired hotkey combination now...\n  [dim](Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)[/dim]\n")

    hotkey = capture_hotkey()
    console.print(f"  [green]✓[/green] Hotkey set to: [bold]{hotkey}[/bold]\n")
    return hotkey


def _prompt_int(prompt_text: str, default: int, min_value: int, max_value: int) -> int:
    while True:
        value_str = Prompt.ask(prompt_text, default=str(default), console=console)
        try:
            value = int(value_str)
        except ValueError:
            console.print("  [red]✗[/red] Please enter a valid number.")
            continue

        if value < min_value or value > max_value:
            console.print(f"  [red]✗[/red] Enter a number between {min_value} and {max_value}.")
            continue

        return value


def _enable_auto_start() -> tuple[bool, list[str]]:
    if sys.platform == "darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.otpilot.plist"
        plist_contents = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n<dict>\n'
            '  <key>Label</key>\n  <string>com.otpilot</string>\n'
            '  <key>ProgramArguments</key>\n  <array>\n'
            '    <string>/bin/sh</string>\n    <string>-lc</string>\n    <string>otpilot start</string>\n'
            '  </array>\n  <key>RunAtLoad</key>\n  <true/>\n</dict>\n</plist>\n'
        )
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(plist_contents, encoding="utf-8")
        return True, [f"launchctl load -w {plist_path}"]
    if sys.platform.startswith("linux"):
        autostart_dir = Path.home() / ".config" / "autostart"
        desktop_file = autostart_dir / "otpilot.desktop"
        desktop_contents = (
            "[Desktop Entry]\nType=Application\nName=OTPilot\nExec=otpilot start\n"
            "X-GNOME-Autostart-enabled=true\nNoDisplay=false\n"
        )
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file.write_text(desktop_contents, encoding="utf-8")
        return True, []
    if sys.platform == "win32":
        return True, []
    return False, []


def run_setup() -> None:
    _print_banner()

    if not _setup_auth():
        console.print("[yellow]Setup incomplete.[/yellow] Authentication is required before OTPilot can run.")
        return

    hotkey = _capture_hotkey()

    console.print("[bold cyan]Step 3:[/bold cyan] Preferences\n")
    notify_on_copy = Confirm.ask("  Show desktop notification after copying OTP?", default=True, console=console)
    auto_paste = Confirm.ask("  Auto-paste OTP after copying?", default=False, console=console)
    otp_max_age = _prompt_int("  Max OTP email age (minutes)", default=10, min_value=1, max_value=60)
    fetch_count = _prompt_int("  Number of recent emails to scan", default=10, min_value=1, max_value=50)
    auto_start = Confirm.ask("  Start OTPilot automatically on login?", default=False, console=console)

    if auto_start:
        ok, post_cmds = _enable_auto_start()
        if not ok:
            console.print("  [yellow]⚠[/yellow] Auto-start isn't supported on this OS.")
        for cmd in post_cmds:
            try:
                subprocess.run(cmd, shell=True, check=False)
            except Exception:
                pass

    config = DEFAULT_CONFIG.copy()
    if config_exists():
        config.update(get_config())

    config.update(
        {
            "hotkey": hotkey,
            "notify_on_copy": notify_on_copy,
            "auto_paste": auto_paste,
            "otp_max_age_minutes": otp_max_age,
            "email_fetch_count": fetch_count,
            "auto_start_on_boot": auto_start,
            "setup_complete": True,
        }
    )
    save_config(config)

    console.print()
    console.print(
        Panel(
            "[bold green]Setup complete![/bold green]\n\n"
            "Run [bold cyan]otpilot start[/bold cyan] to launch OTPilot in the background.",
            border_style="green",
            padding=(1, 2),
        )
    )
