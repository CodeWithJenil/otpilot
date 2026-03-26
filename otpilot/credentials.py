"""OAuth2 credential paths and scopes for OTPilot.

Users provide their own ``credentials.json`` downloaded from the
Google Cloud Console.  The file is stored at ``~/.otpilot/credentials.json``
and never leaves the user's machine.
"""

from pathlib import Path


# OAuth2 configuration
SCOPES: list = ["https://www.googleapis.com/auth/gmail.readonly"]

# Paths
CREDENTIALS_FILE: Path = Path.home() / ".otpilot" / "credentials.json"


def credentials_exist() -> bool:
    """Check whether a user-provided credentials.json file exists.

    Returns:
        True if ``~/.otpilot/credentials.json`` is present, False otherwise.
    """
    return CREDENTIALS_FILE.exists()


def validate_credentials_file(path: Path) -> bool:
    """Validate that a file looks like a Google OAuth2 credentials JSON.

    Performs a basic structural check — verifies the file is valid JSON
    and contains either an ``installed`` or ``web`` top-level key with
    a ``client_id`` field.

    Args:
        path: Path to the credentials JSON file.

    Returns:
        True if the file appears valid, False otherwise.
    """
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    # Google credentials JSON has either "installed" or "web" as a top key
    for key in ("installed", "web"):
        if key in data and "client_id" in data[key]:
            return True

    return False
