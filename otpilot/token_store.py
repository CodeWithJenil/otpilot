"""Token persistence with keytar-first storage and file fallback."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from otpilot.config import CONFIG_DIR, TOKEN_FILE

SERVICE_NAME = "otpilot"
ACCOUNT_NAME = "gmail_provider_token"


def _load_keytar():
    try:
        import keyring  # type: ignore

        return keyring
    except Exception:
        return None


def save_token(token_payload: Dict[str, Any]) -> None:
    """Save token payload to keyring when available, else JSON file."""
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
    """Load token payload from keyring or fallback file."""
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


def token_exists() -> bool:
    return load_token() is not None
