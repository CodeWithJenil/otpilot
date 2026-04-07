"""Configuration management for OTPilot.

This module reads and writes persistent OTPilot settings from
``~/.otpilot/config.json`` and defines default values used during first-run
setup. It is the central configuration layer used by setup, runtime service,
and UI commands.

Key exports:
    get_config: Load effective config with defaults merged in.
    save_config: Persist config values to disk.
    get_value: Read one config value with an optional fallback.
    set_value: Update one config value and save immediately.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


# Default configuration directory and file paths.
CONFIG_DIR: Path = Path.home() / ".otpilot"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
TOKEN_FILE: Path = CONFIG_DIR / "token.json"

# Default configuration values used for first run and missing keys.
DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "ctrl+shift+o",
    "notify_on_copy": True,
    "otp_max_age_minutes": 10,
    "email_fetch_count": 10,
    "otp_history_count": 10,
    "auto_paste": False,
    "auto_start_on_boot": False,
    "notification_sound": False,
    "mask_otp_in_notification": True,
    "check_updates_on_start": True,
    "theme": "default",
    "setup_complete": False,
}


def _ensure_config_dir() -> None:
    """Create the configuration directory when it is missing."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """Load OTPilot configuration and merge it with defaults.

    If the config file does not exist or cannot be decoded, this function
    recreates it from ``DEFAULT_CONFIG``.

    Returns:
        Dict[str, Any]: Effective configuration dictionary with all default
            keys present.

    Raises:
        OSError: If reading or writing the config file fails unexpectedly.
        TypeError: If a value cannot be serialized while rewriting defaults.
    """
    _ensure_config_dir()

    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            stored_config: Dict[str, Any] = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Reset to known-safe defaults when stored JSON is corrupted.
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Merge stored values onto defaults so newly introduced keys exist.
    merged = DEFAULT_CONFIG.copy()
    merged.update(stored_config)
    return merged


def save_config(data: Dict[str, Any]) -> None:
    """Persist configuration data to disk.

    Args:
        data (Dict[str, Any]): Configuration values to save.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If the config file cannot be written.
        TypeError: If ``data`` contains non-JSON-serializable values.
    """
    _ensure_config_dir()

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def config_exists() -> bool:
    """Check whether ``config.json`` exists.

    Returns:
        bool: ``True`` when the config file exists, otherwise ``False``.

    Raises:
        None: This function does not raise application-level exceptions.
    """
    return CONFIG_FILE.exists()


def token_exists() -> bool:
    """Check whether an OAuth token is already stored.

    The function prefers ``otpilot.token_store`` and falls back to checking the
    legacy token file path when token storage backends are unavailable.

    Returns:
        bool: ``True`` if a token is available, otherwise ``False``.

    Raises:
        None: Exceptions are handled internally to support graceful fallback.
    """
    try:
        from otpilot.token_store import token_exists as stored_token_exists

        return stored_token_exists()
    except Exception:
        # Fall back to legacy file presence checks when token store import fails.
        return TOKEN_FILE.exists()


def get_value(key: str, default: Optional[Any] = None) -> Any:
    """Get a single configuration value.

    Args:
        key (str): Configuration key to read.
        default (Optional[Any]): Fallback value when the key is missing.

    Returns:
        Any: The stored value for ``key`` or ``default`` when not present.

    Raises:
        OSError: If loading configuration from disk fails unexpectedly.
        TypeError: If defaults must be rewritten and serialization fails.
    """
    _ensure_config_dir()

    stored_config: Dict[str, Any] = {}
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
    else:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    stored_config = loaded
        except (json.JSONDecodeError, OSError):
            save_config(DEFAULT_CONFIG)

    if key in stored_config:
        return stored_config[key]
    if default is not None:
        return default
    return DEFAULT_CONFIG.get(key)


def set_value(key: str, value: Any) -> None:
    """Set and persist a single configuration value.

    Args:
        key (str): Configuration key to update.
        value (Any): New value to assign.

    Returns:
        None: This function does not return a value.

    Raises:
        OSError: If the config file cannot be read or written.
        TypeError: If ``value`` is not JSON serializable.
    """
    config = get_config()
    config[key] = value
    save_config(config)
