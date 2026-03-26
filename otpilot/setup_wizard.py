"""Interactive first-run setup wizard for OTPilot.

Guides the user through credential import, OAuth authentication, and
hotkey configuration using ``rich`` for styled terminal output.
"""

import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text

from otpilot.config import get_config, save_config, token_exists
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
    """Guide the user through providing their Google OAuth credentials.json.

    Returns:
        True if credentials are available (existing or newly imported),
        False if the user cannot proceed.
    """
    console.print("[bold cyan]Step 1:[/bold cyan] Google Cloud Credentials\n")

    if credentials_exist() and validate_credentials_file(CREDENTIALS_FILE):
        console.print("  [dim]A credentials file was found at ~/.otpilot/credentials.json[/dim]")
        if not Confirm.ask("  Replace it?", default=False, console=console):
            console.print("  [green]✓[/green] Using existing credentials.\n")
            return True
        console.print()

    console.print(
        "  To use OTPilot, you need a [bold]credentials.json[/bold] file from\n"
        "  the Google Cloud Console. This takes about 5 minutes.\n"
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


def _configure_settings(hotkey: str) -> None:
    """Save the configuration with the captured hotkey.

    Args:
        hotkey: The hotkey string to save.
    """
    config = get_config()
    config["hotkey"] = hotkey
    save_config(config)
    console.print("  [green]✓[/green] Configuration saved to [dim]~/.otpilot/config.json[/dim]\n")


def run_setup() -> None:
    """Run the complete OTPilot setup wizard.

    This is the main entry point for the setup process. It can be
    re-run at any time via ``otpilot setup``.
    """
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
        console.print("[dim]An existing authentication token was found.[/dim]")
        if Confirm.ask("  Re-authenticate?", default=False, console=console):
            auth_ok = _run_oauth()
        else:
            console.print("  [green]✓[/green] Using existing authentication.\n")
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

    # Step 4: Save config
    _configure_settings(hotkey)

    # Summary
    console.print(
        Panel(
            "[green bold]Setup complete![/green bold]\n\n"
            f"  Hotkey:       [bold]{hotkey}[/bold]\n"
            "  Credentials:  [dim]~/.otpilot/credentials.json[/dim]\n"
            "  Token:        [dim]~/.otpilot/token.json[/dim]\n"
            "  Config:       [dim]~/.otpilot/config.json[/dim]\n\n"
            "Run [bold cyan]otpilot start[/bold cyan] to launch the background service.",
            border_style="green",
            title="[bold]Summary[/bold]",
            padding=(1, 2),
        )
    )

    # Offer to start now
    if Confirm.ask("\nStart OTPilot now?", default=True, console=console):
        console.print("\n[cyan]Starting OTPilot...[/cyan]\n")
        from otpilot.main import run
        run()
    else:
        console.print(
            "\n[dim]Run [bold]otpilot start[/bold] anytime to launch.[/dim]\n"
        )
