"""Token persistence backends for OTPilot authentication.

This module stores and retrieves OAuth token payloads, preferring OS keyring
storage and falling back to a local JSON file in the OTPilot config directory.
It provides the persistence layer used by Gmail authentication and setup
workflows.

Key exports:
    save_token: Persist token payload to keyring or fallback file.
    load_token: Load token payload from keyring or fallback file.
    token_exists: Boolean helper indicating token availability.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from otpilot.config import CONFIG_DIR, TOKEN_FILE

SERVICE_NAME = "otpilot"
ACCOUNT_NAME = "gmail_provider_token"
APP_PASSWORD_ACCOUNT_NAME = "gmail_app_password"
APP_PASSWORD_FILE = CONFIG_DIR / "app_password.txt"


def _load_keytar():
    """Import and return keyring backend when available.

    Returns:
        Any: Imported keyring module, or ``None`` when unavailable.
    """
    try:
        import keyring  # type: ignore

        return keyring
    except Exception:
        return None


def save_token(token_payload: Dict[str, Any]) -> None:
    """Save token payload to keyring, falling back to local JSON storage.

    Args:
        token_payload (Dict[str, Any]): Token data to persist.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If fallback file storage cannot be written.
        TypeError: If ``token_payload`` contains non-serializable values.
    """
    keyring = _load_keytar()
    raw = json.dumps(token_payload)

    if keyring is not None:
        try:
            keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, raw)
            return
        except Exception:
            pass

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(raw, encoding="utf-8")


def load_token() -> Optional[Dict[str, Any]]:
    """Load token payload from keyring or fallback file.

    Returns:
        Optional[Dict[str, Any]]: Parsed token payload when present, otherwise
            ``None``.

    Raises:
        None: Backend and parse failures are handled internally.
    """
    keyring = _load_keytar()
    if keyring is not None:
        try:
            raw = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
            if raw:
                return json.loads(raw)
        except Exception:
            pass

    if not TOKEN_FILE.exists():
        return None

    try:
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_app_password(password: str) -> None:
    """Save Gmail App Password to keyring, falling back to local text storage.

    Args:
        password (str): App Password value to persist.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If fallback file storage cannot be written.
    """
    keyring = _load_keytar()
    if keyring is not None:
        try:
            keyring.set_password(SERVICE_NAME, APP_PASSWORD_ACCOUNT_NAME, password)
            return
        except Exception:
            pass

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    APP_PASSWORD_FILE.write_text(password, encoding="utf-8")
    os.chmod(APP_PASSWORD_FILE, 0o600)


def load_app_password() -> Optional[str]:
    """Load Gmail App Password from keyring or fallback text file.

    Returns:
        Optional[str]: Stored App Password when present, otherwise ``None``.

    Raises:
        None: Backend and parse failures are handled internally.
    """
    keyring = _load_keytar()
    if keyring is not None:
        try:
            raw = keyring.get_password(SERVICE_NAME, APP_PASSWORD_ACCOUNT_NAME)
            if raw:
                return raw
        except Exception:
            pass

    if not APP_PASSWORD_FILE.exists():
        return None

    try:
        raw = APP_PASSWORD_FILE.read_text(encoding="utf-8").strip()
        return raw or None
    except Exception:
        return None


def token_exists() -> bool:
    """Check whether a token payload can be loaded from storage.

    Returns:
        bool: ``True`` when a token payload exists, otherwise ``False``.

    Raises:
        None: This helper delegates error handling to ``load_token``.
    """
    token_payload = load_token()
    app_password = load_app_password()
    return token_payload is not None or bool(app_password)
