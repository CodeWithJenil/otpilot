"""Configuration management for OTPilot.

Handles reading and writing of ~/.otpilot/config.json.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


# Default configuration directory and file paths
CONFIG_DIR: Path = Path.home() / ".otpilot"
CONFIG_FILE: Path = CONFIG_DIR / "config.json"
TOKEN_FILE: Path = CONFIG_DIR / "token.json"

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "ctrl+shift+o",
    "notify_on_copy": True,
    "otp_max_age_minutes": 10,
    "email_fetch_count": 10,
}


def _ensure_config_dir() -> None:
    """Create the configuration directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def get_config() -> Dict[str, Any]:
    """Load and return the current configuration.

    If the config file doesn't exist, creates it with default values.

    Returns:
        Dictionary containing all configuration values.
    """
    _ensure_config_dir()

    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            stored_config: Dict[str, Any] = json.load(f)
    except (json.JSONDecodeError, OSError):
        # If config is corrupted, reset to defaults
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Merge with defaults so new keys are always present
    merged = DEFAULT_CONFIG.copy()
    merged.update(stored_config)
    return merged


def save_config(data: Dict[str, Any]) -> None:
    """Save configuration data to disk.

    Args:
        data: Dictionary of configuration values to persist.
    """
    _ensure_config_dir()

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def config_exists() -> bool:
    """Check whether a configuration file already exists.

    Returns:
        True if config.json is present, False otherwise.
    """
    return CONFIG_FILE.exists()


def token_exists() -> bool:
    """Check whether an OAuth token file already exists.

    Returns:
        True if token.json is present, False otherwise.
    """
    return TOKEN_FILE.exists()


def get_value(key: str, default: Optional[Any] = None) -> Any:
    """Retrieve a single configuration value.

    Args:
        key: The config key to look up.
        default: Fallback value if the key is missing.

    Returns:
        The configuration value, or *default* if not found.
    """
    config = get_config()
    return config.get(key, default)


def set_value(key: str, value: Any) -> None:
    """Update a single configuration value and persist to disk.

    Args:
        key: The config key to update.
        value: The new value.
    """
    config = get_config()
    config[key] = value
    save_config(config)
