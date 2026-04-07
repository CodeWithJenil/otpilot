"""OTP history storage helpers for OTPilot.

This module persists recent OTP fetches to a JSON history file so users can
review previously copied codes via the CLI.

Key exports:
    load_history: Load stored OTP history entries.
    save_entry: Prepend a new OTP history entry.
    clear_history: Remove stored OTP history entries.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from otpilot.config import CONFIG_DIR, get_config

HISTORY_FILE: Path = CONFIG_DIR / "history.json"
MAX_HISTORY_COUNT: int = 50


def _ensure_history_dir() -> None:
    """Ensure the OTPilot configuration directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> List[Dict[str, Any]]:
    """Load OTP history entries from disk.

    Returns:
        List[Dict[str, Any]]: List of history entries ordered newest to oldest.
    """
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    return [entry for entry in data if isinstance(entry, dict)]


def _history_limit() -> int:
    """Return the configured OTP history limit, capped to a safe maximum."""
    try:
        count = int(get_config().get("otp_history_count", 10))
    except (TypeError, ValueError):
        return 10
    if count < 0:
        return 0
    return min(count, MAX_HISTORY_COUNT)


def save_entry(otp: str, sender: str = "", subject: str = "") -> None:
    """Prepend an OTP history entry, respecting configured limits.

    Args:
        otp (str): OTP code that was fetched.
        sender (str): Email sender address or label.
        subject (str): Email subject line.

    Returns:
        None: This function does not return a value.
    """
    history_count = _history_limit()
    if history_count <= 0:
        return

    entry = {
        "otp": otp,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sender": sender or "",
        "subject": subject or "",
    }

    history = load_history()
    history.insert(0, entry)

    if len(history) > history_count:
        history = history[:history_count]

    _ensure_history_dir()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, sort_keys=False)


def clear_history() -> None:
    """Remove stored OTP history from disk.

    Returns:
        None: This function does not return a value.
    """
    try:
        HISTORY_FILE.unlink()
    except FileNotFoundError:
        pass
