"""Interactive setup workflow for OTPilot.

This module implements OTPilot's first-run and reconfiguration wizard,
including authentication, hotkey capture, preference collection, and
persistence of resulting settings. It is the primary onboarding entry point
for CLI and tray-based setup actions.

Key exports:
    run_setup: Execute the full interactive setup sequence.
"""

import imaplib
import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from otpilot.config import DEFAULT_CONFIG, config_exists, get_config, save_config, set_value, token_exists
from otpilot.logger import get_logger

console = Console()
logger = get_logger(__name__)


def _print_banner() -> None:
    """Render the setup banner in the terminal UI.

    Returns:
        None: This function does not return a value.
    """
    banner_text = Text()
    banner_text.append("✈  ", style="bold cyan")
    banner_text.append("OTPilot Setup", style="bold white")
    banner_text.append(" ✈", style="bold cyan")

    console.print()
    console.print(Panel(banner_text, subtitle="[dim]Background OTP copier for Gmail[/dim]", border_style="bright_blue", padding=(1, 4)))
    console.print()


def _setup_auth() -> bool:
    """Authenticate the user and ensure a token is stored.

    Returns:
        bool: ``True`` when authentication succeeds or existing token is kept,
            otherwise ``False``.
    """
    console.print("[bold cyan]Step 1:[/bold cyan] Authentication Mode\n")

    if token_exists():
        console.print("  [dim]An authentication token is already stored.[/dim]")
        if Confirm.ask("  Re-authenticate now?", default=False, console=console):
            pass
        else:
            console.print("  [green]✓[/green] Using existing token.\n")
            return True

    console.print("  [1] Firebase Auth — Sign in via browser (hosted Firebase web app). Recommended.")
    console.print("  [2] My own credentials.json — Use your own Google Cloud OAuth client. Full control.")
    console.print("  [3] Gmail App Password — No OAuth. Use a Gmail App Password with IMAP.\n")

    choice = Prompt.ask("  Select mode", choices=["1", "2", "3"], default="1", console=console)
    mode_map = {"1": "firebase", "2": "credentials", "3": "imap"}
    auth_mode = mode_map[choice]
    set_value("auth_mode", auth_mode)

    from otpilot.gmail_client import run_oauth_flow_credentials, run_oauth_flow_firebase
    from otpilot.token_store import save_app_password

    try:
        if auth_mode == "firebase":
            config = get_config()
            firebase_web_url = str(config.get("firebase_web_url", "")).strip()
            if not firebase_web_url:
                console.print(
                    "  [dim]Enter the URL of your Firebase-hosted auth page (must perform Google sign-in and redirect).[/dim]"
                )
                firebase_web_url = Prompt.ask("  Firebase auth page URL", console=console).strip()
                set_value("firebase_web_url", firebase_web_url)
            console.print("  Opening your browser for Gmail authorization...\n")
            run_oauth_flow_firebase(firebase_web_url=firebase_web_url)
        elif auth_mode == "credentials":
            console.print("[bold cyan]Step 1 of 3:[/bold cyan] Create a Google Cloud Project & OAuth Client\n")
            console.print("  1. Go to [dim]console.cloud.google.com[/dim]")
            console.print("  2. Click the project dropdown (top left) → [bold]New Project[/bold]")
            console.print("     Name it anything (e.g. \"OTPilot\") → [bold]Create[/bold]")
            console.print("  3. Go to APIs & Services → Library")
            console.print("     Search \"Gmail API\" → click it → [bold]Enable[/bold]")
            console.print("  4. Go to APIs & Services → OAuth consent screen")
            console.print("     - Choose [bold]External[/bold] → [bold]Create[/bold]")
            console.print("     - App name: OTPilot")
            console.print("     - User support email: your Gmail")
            console.print("     - Developer contact: your Gmail")
            console.print("     → [bold]Save and Continue[/bold]")
            console.print("  5. On the Scopes step → Add or Remove Scopes")
            console.print("     Search \"gmail.readonly\" → check it → [bold]Update[/bold]")
            console.print("     → [bold]Save and Continue[/bold]")
            console.print("  6. On Test users → Add Users → add your Gmail address")
            console.print("     → [bold]Save and Continue[/bold] → Back to Dashboard")
            console.print("  7. Go to APIs & Services → Credentials")
            console.print("     → [bold]Create Credentials[/bold] → [bold]OAuth client ID[/bold]")
            console.print("     - Application type: Desktop app")
            console.print("     - Name: OTPilot CLI")
            console.print("     → [bold]Create[/bold]")
            console.print("  8. Click the download icon (⬇) next to the new client")
            console.print("     Rename the downloaded file to: [bold]credentials.json[/bold]")
            console.print("     Move it to: [bold]~/.otpilot/credentials.json[/bold]\n")
            console.print("     On macOS/Linux:")
            console.print("       [dim]mv ~/Downloads/client_secret_*.json ~/.otpilot/credentials.json[/dim]\n")
            console.print("     On Windows:")
            console.print(
                "       [dim]move %USERPROFILE%\\Downloads\\client_secret_*.json %USERPROFILE%\\.otpilot\\credentials.json[/dim]\n"
            )

            creds_path = Path.home() / ".otpilot" / "credentials.json"
            while True:
                Confirm.ask("  I've placed credentials.json at ~/.otpilot/credentials.json", console=console)
                if creds_path.exists():
                    break
                console.print("  [red]✗[/red] File not found at ~/.otpilot/credentials.json")
                console.print("  Double-check the path and try again.\n")

            console.print("  [green]✓[/green] credentials.json found.")
            console.print("  Opening browser for Google sign-in...")
            console.print("  [dim]Complete the sign-in in your browser. The tab will close automatically.[/dim]")
            run_oauth_flow_credentials()
        else:
            console.print("Enable IMAP & Create an App Password")
            console.print("  1. Open Gmail in your browser")
            console.print("  2. Click the gear icon (top right) → See all settings")
            console.print("  3. Go to the Forwarding and POP/IMAP tab")
            console.print("  4. Under IMAP access → select Enable IMAP → Save Changes\n")
            console.print("  5. Go to [dim]myaccount.google.com/security[/dim]")
            console.print("  6. Under \"How you sign in to Google\" → 2-Step Verification")
            console.print("     Enable it if not already on (required for App Passwords)\n")
            console.print("  7. Go to [dim]myaccount.google.com/apppasswords[/dim]")
            console.print("     [dim](If you don't see App Passwords, 2-Step Verification is not enabled)[/dim]")
            console.print("  8. In the \"App name\" field type: OTPilot → click Create")
            console.print("  9. Google shows a 16-character password — copy it now")
            console.print("     [dim]You won't be able to see it again after closing the dialog[/dim]\n")

            config = get_config()
            while True:
                imap_user = Prompt.ask("  Enter your Gmail address", console=console).strip()
                while True:
                    app_password = Prompt.ask("  Paste your App Password (16 characters)", password=True, console=console)
                    normalized_password = app_password.replace(" ", "")
                    if len(normalized_password) == 16:
                        break
                    console.print(
                        "  [red]✗[/red] App Passwords are exactly 16 characters. Please check and try again."
                    )

                console.print("  Testing IMAP connection...")
                try:
                    mail = imaplib.IMAP4_SSL(
                        config.get("imap_host", "imap.gmail.com"), config.get("imap_port", 993)
                    )
                    mail.login(imap_user, normalized_password)
                    mail.logout()
                except imaplib.IMAP4.error:
                    console.print("  [red]✗[/red] IMAP login failed. Common reasons:")
                    console.print("    - IMAP is not enabled in Gmail settings (check Step 3 above)")
                    console.print(
                        "    - The App Password is incorrect (re-generate one at [dim]myaccount.google.com/apppasswords[/dim])"
                    )
                    console.print("    - 2-Step Verification is not fully enabled")
                    if Confirm.ask("  Try again?", console=console):
                        continue
                    return False

                console.print("  [green]✓[/green] IMAP connection successful.")
                set_value("imap_user", imap_user)
                save_app_password(normalized_password)
                break

        console.print("  [green]✓[/green] Authentication setup successful!\n")
        return True
    except Exception as exc:
        console.print(f"  [red]✗[/red] Authentication failed: {exc}\n")
        return False


def _capture_hotkey() -> str:
    """Capture a user-selected hotkey or fall back to default.

    Returns:
        str: Captured hotkey string, or configured default when unavailable.
    """
    from otpilot.hotkey_listener import capture_hotkey

    console.print("[bold cyan]Step 2:[/bold cyan] Configure Hotkey")
    console.print("  Press your desired hotkey combination now...\n  [dim](Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)[/dim]\n")

    try:
        hotkey = capture_hotkey()
    except RuntimeError:
        hotkey = DEFAULT_CONFIG["hotkey"]
        console.print(
            "  [yellow]⚠[/yellow] Hotkey capture unavailable in this environment."
            f" Using default: [bold]{hotkey}[/bold]\n"
        )
        return hotkey

    console.print(f"  [green]✓[/green] Hotkey set to: [bold]{hotkey}[/bold]\n")
    return hotkey


def _prompt_int(prompt_text: str, default: int, min_value: int, max_value: int) -> int:
    """Prompt for a validated integer inside inclusive bounds.

    Args:
        prompt_text (str): Prompt label displayed to the user.
        default (int): Default value shown in the prompt.
        min_value (int): Minimum accepted numeric value.
        max_value (int): Maximum accepted numeric value.

    Returns:
        int: Validated user-provided integer.
    """
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
    """Configure OS-specific auto-start entries for OTPilot.

    Returns:
        tuple[bool, list[str]]: ``(success, post_commands)`` where
            ``post_commands`` are shell commands to execute immediately after
            file creation (used for macOS launchctl activation).
    """
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
    """Run the complete interactive OTPilot setup wizard.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If configuration files cannot be written.
        TypeError: If configuration data cannot be serialized.
    """
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
                # Post-setup commands apply platform-specific startup registration.
                subprocess.run(cmd, shell=True, check=False)
            except Exception:
                pass

    config = DEFAULT_CONFIG.copy()
    if config_exists():
        # Preserve existing non-interactive settings while updating prompted keys.
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
    logger.info("Setup complete.")

    console.print()
    console.print(
        Panel(
            "[bold green]Setup complete![/bold green]\n\n"
            "Run [bold cyan]otpilot start[/bold cyan] to launch OTPilot in the background.",
            border_style="green",
            padding=(1, 2),
        )
    )
