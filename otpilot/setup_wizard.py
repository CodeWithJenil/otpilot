"""Interactive first-run setup wizard for OTPilot.

Guides the user through credential import, OAuth authentication, and
hotkey configuration using ``rich`` for styled terminal output.
"""

import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from otpilot.config import DEFAULT_CONFIG, config_exists, get_config, save_config, token_exists
from otpilot.credentials import CREDENTIALS_FILE, credentials_exist, validate_credentials_file


console = Console()


def _print_banner() -> None:
    """Print the OTPilot welcome banner."""
    banner_text = Text()
    banner_text.append("✈  ", style="bold cyan")
    banner_text.append("OTPilot Setup", style="bold white")
    banner_text.append(" ✈", style="bold cyan")

    console.print()
    console.print(
        Panel(
            banner_text,
            subtitle="[dim]Background OTP copier for Gmail[/dim]",
            border_style="bright_blue",
            padding=(1, 4),
        )
    )
    console.print()


def _setup_credentials() -> bool:
    """Guide the user through providing their Google OAuth credentials.

    Offers a "Quick Setup" using a hosted proxy or "Manual Setup"
    by providing a ``credentials.json`` file.

    Returns:
        True if credentials/token are available, False if the user cannot proceed.
    """
    console.print("[bold cyan]Step 1:[/bold cyan] Google Cloud Credentials\n")

    # If token already exists, we might not need anything else
    if token_exists():
        console.print("  [dim]An authentication token was already found at ~/.otpilot/token.json[/dim]")
        if not Confirm.ask("  Use existing token?", default=True, console=console):
            # If they don't want the existing token, we fall through to setup
            pass
        else:
            console.print("  [green]✓[/green] Using existing token.\n")
            return True

    # Choice between Quick and Manual setup
    console.print("  [bold]1.[/bold] Quick setup (recommended) — [dim]no Google Cloud project needed[/dim]")
    console.print("  [bold]2.[/bold] Manual setup — [dim]use your own Google Cloud project[/dim]\n")
    
    choice = Prompt.ask(
        "  Select an option",
        choices=["1", "2"],
        default="1",
        console=console,
    )

    if choice == "1":
        console.print("\n  [bold]Quick Setup[/bold] uses our hosted OAuth proxy.")
        console.print("  Opening your browser for Gmail authorization...\n")

        from otpilot.gmail_client import run_proxy_oauth_flow
        try:
            run_proxy_oauth_flow()
            console.print("  [green]✓[/green] Authentication successful!\n")
            return True
        except Exception as exc:
            console.print(f"  [red]✗[/red] Quick Setup failed: {exc}")
            if not Confirm.ask("  Try manual setup instead?", default=True, console=console):
                return False
            # Fall through to manual setup
            console.print()
    else:
        # User chose manual setup
        pass

    # Manual Setup flow (existing logic)
    if credentials_exist() and validate_credentials_file(CREDENTIALS_FILE):
        console.print("  [dim]A credentials file was found at ~/.otpilot/credentials.json[/dim]")
        if not Confirm.ask("  Replace it?", default=False, console=console):
            console.print("  [green]✓[/green] Using existing credentials.\n")
            return True
        console.print()

    console.print(
        "  Manual Setup: You need a [bold]credentials.json[/bold] file from\n"
        "  the Google Cloud Console.\n"
    )
    console.print(
        "  [dim]See the full guide:[/dim] "
        "[link=https://github.com/otpilot/otpilot/blob/main/docs/SETUP.md]"
        "docs/SETUP.md[/link]\n"
    )

    has_credentials = Confirm.ask(
        "  Have you already downloaded your credentials.json?",
        default=False,
        console=console,
    )

    if not has_credentials:
        console.print()
        console.print(
            Panel(
                "[bold]Quick Steps:[/bold]\n\n"
                "  1. Go to [link=https://console.cloud.google.com]console.cloud.google.com[/link]\n"
                "  2. Create a new project (or use an existing one)\n"
                "  3. Enable the [bold]Gmail API[/bold]\n"
                "  4. Go to [bold]APIs & Services → Credentials[/bold]\n"
                "  5. Create [bold]OAuth 2.0 Client ID[/bold] (type: Desktop app)\n"
                "  6. Download the JSON file\n"
                "  7. Run [bold cyan]otpilot setup[/bold cyan] again\n\n"
                "  Full guide: [link=https://github.com/otpilot/otpilot/blob/main/docs/SETUP.md]"
                "docs/SETUP.md[/link]",
                border_style="yellow",
                title="[bold]How to get credentials.json[/bold]",
                padding=(1, 2),
            )
        )
        console.print()
        return False

    # Prompt for file path
    while True:
        cred_path_str = Prompt.ask(
            "\n  Enter the path to your credentials.json file",
            console=console,
        )
        cred_path = Path(cred_path_str.strip().strip("'\"")).expanduser().resolve()

        if not cred_path.exists():
            console.print(f"  [red]✗[/red] File not found: {cred_path}")
            if not Confirm.ask("  Try again?", default=True, console=console):
                return False
            continue

        if not validate_credentials_file(cred_path):
            console.print(
                "  [red]✗[/red] This doesn't look like a valid Google OAuth credentials file.\n"
                "  [dim]Expected a JSON file with an 'installed' or 'web' key containing 'client_id'.[/dim]"
            )
            if not Confirm.ask("  Try again?", default=True, console=console):
                return False
            continue

        # Valid file — copy to ~/.otpilot/
        CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(cred_path), str(CREDENTIALS_FILE))
        console.print("  [green]✓[/green] Credentials saved to [dim]~/.otpilot/credentials.json[/dim]\n")
        console.print("  [dim]Your credentials never leave your machine.[/dim]\n")
        return True


def _run_oauth() -> bool:
    """Run the OAuth2 authentication flow.

    Returns:
        True if authentication succeeded, False otherwise.
    """
    from otpilot.gmail_client import run_oauth_flow

    console.print("[bold cyan]Step 2:[/bold cyan] Google Account Sign-In")
    console.print("  Opening your browser for Gmail authorization...\n")

    try:
        run_oauth_flow()
        console.print("  [green]✓[/green] Authentication successful!\n")
        return True
    except Exception as exc:
        console.print(f"  [red]✗[/red] Authentication failed: {exc}\n")
        console.print(
            "  [dim]Make sure your credentials.json is valid and try again.[/dim]\n"
        )
        return False


def _capture_hotkey() -> str:
    """Interactively capture the user's desired hotkey.

    Returns:
        The captured hotkey string.
    """
    from otpilot.hotkey_listener import capture_hotkey

    console.print("[bold cyan]Step 3:[/bold cyan] Configure Hotkey")
    console.print(
        "  Press your desired hotkey combination now...\n"
        "  [dim](Must include at least one modifier: Ctrl, Alt, Shift, or Cmd)[/dim]\n"
    )

    hotkey = capture_hotkey()
    console.print(f"  [green]✓[/green] Hotkey set to: [bold]{hotkey}[/bold]\n")
    return hotkey


def _prompt_int(prompt_text: str, default: int, min_value: int, max_value: int) -> int:
    """Prompt for an integer within a bounded range."""
    while True:
        value_str = Prompt.ask(
            prompt_text,
            default=str(default),
            console=console,
        )
        try:
            value = int(value_str)
        except ValueError:
            console.print("  [red]✗[/red] Please enter a valid number.")
            continue

        if value < min_value or value > max_value:
            console.print(
                f"  [red]✗[/red] Enter a number between {min_value} and {max_value}."
            )
            continue

        return value


def _enable_auto_start() -> tuple[bool, list[str]]:
    """Configure OS-level auto-start behavior."""
    if sys.platform == "darwin":
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.otpilot.plist"
        plist_contents = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            '<plist version="1.0">\n'
            "<dict>\n"
            "  <key>Label</key>\n"
            "  <string>com.otpilot</string>\n"
            "  <key>ProgramArguments</key>\n"
            "  <array>\n"
            "    <string>/bin/sh</string>\n"
            "    <string>-lc</string>\n"
            "    <string>otpilot start</string>\n"
            "  </array>\n"
            "  <key>RunAtLoad</key>\n"
            "  <true/>\n"
            "</dict>\n"
            "</plist>\n"
        )
        plist_path.parent.mkdir(parents=True, exist_ok=True)
        plist_path.write_text(plist_contents, encoding="utf-8")
        return True, [
            f"Created: {plist_path}",
            f"To undo: launchctl unload {plist_path}",
            f"Then delete: {plist_path}",
        ]

    if sys.platform == "win32":
        try:
            import winreg  # type: ignore
        except Exception as exc:
            return False, [f"Failed to access registry: {exc}"]

        run_key = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        try:
            with winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_CURRENT_USER,  # type: ignore[attr-defined]
                run_key,
                0,
                winreg.KEY_SET_VALUE,  # type: ignore[attr-defined]
            ) as key:
                winreg.SetValueEx(  # type: ignore[attr-defined]
                    key, "OTPilot", 0, winreg.REG_SZ, "otpilot start"
                )
        except Exception as exc:
            return False, [f"Failed to write registry key: {exc}"]

        return True, [
            f"Created: HKCU\\{run_key} -> OTPilot = \"otpilot start\"",
            "To undo: remove the OTPilot value from that registry key",
        ]

    service_path = Path.home() / ".config" / "systemd" / "user" / "otpilot.service"
    service_contents = (
        "[Unit]\n"
        "Description=OTPilot\n\n"
        "[Service]\n"
        "Type=simple\n"
        "ExecStart=/bin/sh -lc 'otpilot start'\n"
        "Restart=on-failure\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )
    service_path.parent.mkdir(parents=True, exist_ok=True)
    service_path.write_text(service_contents, encoding="utf-8")
    return True, [
        f"Created: {service_path}",
        "To enable: systemctl --user enable --now otpilot.service",
        "To undo: systemctl --user disable --now otpilot.service",
        f"Then delete: {service_path}",
    ]


def run_setup() -> None:
    """Run the complete OTPilot setup wizard.

    This is the main entry point for the setup process. It can be
    re-run at any time via ``otpilot setup``.
    """
    had_config = config_exists()
    base_config = get_config() if had_config else DEFAULT_CONFIG.copy()
    first_time_setup = (not had_config) or (not base_config.get("setup_complete", False))

    _print_banner()

    console.print("[bold]Welcome to OTPilot setup![/bold]")
    console.print(
        "This wizard will help you import your Google credentials, "
        "authenticate, and configure your hotkey.\n"
    )

    # Step 1: Credentials
    if not _setup_credentials():
        console.print(
            "[yellow]Setup incomplete.[/yellow] Get your credentials.json and "
            "run [bold]otpilot setup[/bold] again.\n"
        )
        return

    # Step 2: OAuth
    if token_exists():
        # If we just did Quick Setup, Step 2 is already done.
        # If the token was there before, we ask to re-authenticate.
        # But for simplicity, if it's there, we just proceed.
        auth_ok = True
    else:
        auth_ok = _run_oauth()

    if not auth_ok:
        console.print(
            "[yellow]Setup incomplete.[/yellow] Fix the authentication issue "
            "and run [bold]otpilot setup[/bold] again.\n"
        )
        return

    # Step 3: Hotkey
    hotkey = _capture_hotkey()

    # Step 4: Auto-paste
    console.print("[bold cyan]Step 4:[/bold cyan] Auto-paste")
    auto_paste = Confirm.ask(
        "  Enable auto-paste? OTPilot will paste the OTP directly instead of just copying it. [y/N]",
        default=bool(base_config.get("auto_paste", False)),
        console=console,
    )
    console.print()

    # Step 5: Notifications
    console.print("[bold cyan]Step 5:[/bold cyan] Notifications")
    notify_on_copy = Confirm.ask(
        "  Show desktop notifications when OTP is copied? [Y/n]",
        default=bool(base_config.get("notify_on_copy", True)),
        console=console,
    )
    mask_otp_in_notification = bool(base_config.get("mask_otp_in_notification", True))
    if notify_on_copy:
        mask_otp_in_notification = Confirm.ask(
            "  Mask OTP digits in notification? (shows 84••93 instead of 847293) [Y/n]",
            default=mask_otp_in_notification,
            console=console,
        )
    console.print()

    # Step 6: OTP settings
    console.print("[bold cyan]Step 6:[/bold cyan] OTP settings")
    email_fetch_count = _prompt_int(
        "  How many recent emails to scan? [10]:",
        default=int(base_config.get("email_fetch_count", 10)),
        min_value=1,
        max_value=50,
    )
    otp_max_age_minutes = _prompt_int(
        "  Ignore OTPs older than how many minutes? [10]:",
        default=int(base_config.get("otp_max_age_minutes", 10)),
        min_value=1,
        max_value=60,
    )
    console.print()

    # Step 7: Updates
    console.print("[bold cyan]Step 7:[/bold cyan] Updates")
    check_updates_on_start = Confirm.ask(
        "  Check for updates automatically when OTPilot starts? [Y/n]",
        default=bool(base_config.get("check_updates_on_start", True)),
        console=console,
    )
    console.print()

    # Step 8: Auto-start on boot
    console.print("[bold cyan]Step 8:[/bold cyan] Auto-start on boot")
    auto_start_on_boot = Confirm.ask(
        "  Start OTPilot automatically when your computer starts? [y/N]",
        default=bool(base_config.get("auto_start_on_boot", False)),
        console=console,
    )
    if auto_start_on_boot:
        success, details = _enable_auto_start()
        if success:
            console.print("  [green]✓[/green] Auto-start configured.")
            for line in details:
                console.print(f"  {line}")
        else:
            console.print("  [red]✗[/red] Auto-start setup failed.")
            for line in details:
                console.print(f"  {line}")
            auto_start_on_boot = False
    console.print()

    # Save config at the end
    config = base_config.copy()
    config["hotkey"] = hotkey
    config["auto_paste"] = auto_paste
    config["notify_on_copy"] = notify_on_copy
    config["mask_otp_in_notification"] = mask_otp_in_notification
    config["email_fetch_count"] = email_fetch_count
    config["otp_max_age_minutes"] = otp_max_age_minutes
    config["check_updates_on_start"] = check_updates_on_start
    config["auto_start_on_boot"] = auto_start_on_boot
    config["setup_complete"] = True
    save_config(config)
    console.print("  [green]✓[/green] Configuration saved to [dim]~/.otpilot/config.json[/dim]\n")

    # Summary
    console.print(
        Panel(
            "[green bold]Setup complete![/green bold]\n\n"
            f"  Hotkey:       [bold]{hotkey}[/bold]\n"
            f"  Auto-paste:   [bold]{'On' if auto_paste else 'Off'}[/bold]\n"
            f"  Notifications:[bold]{' On' if notify_on_copy else ' Off'}[/bold]\n"
            f"  Mask OTP:     [bold]{'On' if mask_otp_in_notification else 'Off'}[/bold]\n"
            f"  Fetch count:  [bold]{email_fetch_count}[/bold]\n"
            f"  Max OTP age:  [bold]{otp_max_age_minutes} min[/bold]\n"
            f"  Updates:      [bold]{'On' if check_updates_on_start else 'Off'}[/bold]\n"
            f"  Auto-start:   [bold]{'On' if auto_start_on_boot else 'Off'}[/bold]\n"
            "  Credentials:  [dim]" + (str(CREDENTIALS_FILE) if credentials_exist() else "None (Quick Setup)") + "[/dim]\n"
            "  Token:        [dim]~/.otpilot/token.json[/dim]\n"
            "  Config:       [dim]~/.otpilot/config.json[/dim]\n\n"
            "Run [bold cyan]otpilot start[/bold cyan] to launch the background service.",
            border_style="green",
            title="[bold]Summary[/bold]",
            padding=(1, 2),
        )
    )

    if first_time_setup:
        console.print("\n💬 Feedback? github.com/CodeWithJenil/otpilot/discussions\n")

    # Offer to start now
    if Confirm.ask("\nStart OTPilot now?", default=True, console=console):
        console.print("\n[cyan]Starting OTPilot...[/cyan]\n")
        from otpilot.main import run
        run()
    else:
        console.print(
            "\n[dim]Run [bold]otpilot start[/bold] anytime to launch.[/dim]\n"
        )
