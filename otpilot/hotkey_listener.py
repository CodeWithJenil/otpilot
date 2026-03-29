"""Global hotkey capture for OTPilot.

This module wraps ``pynput`` to parse user-defined hotkey strings and listen
for global keyboard events in the background. It provides both runtime hotkey
listening and interactive hotkey capture used during setup.

Key exports:
    HotkeyListener: Background listener that triggers a callback on hotkey hit.
    capture_hotkey: Interactive helper for collecting a hotkey combination.
"""

import threading
from typing import Callable, FrozenSet, Optional, Set

try:
    from pynput import keyboard

    _PYNPUT_AVAILABLE = True
    _PYNPUT_IMPORT_ERROR: Optional[Exception] = None
except Exception as exc:  # Graceful fallback on headless environments.
    keyboard = None  # type: ignore[assignment]
    _PYNPUT_AVAILABLE = False
    _PYNPUT_IMPORT_ERROR = exc


if _PYNPUT_AVAILABLE:
    # Map user-friendly names to pynput's canonical modifier keys.
    _MODIFIER_MAP = {
        "ctrl": keyboard.Key.ctrl_l,
        "control": keyboard.Key.ctrl_l,
        "alt": keyboard.Key.alt_l,
        "option": keyboard.Key.alt_l,
        "shift": keyboard.Key.shift,
        "cmd": keyboard.Key.cmd,
        "command": keyboard.Key.cmd,
        "super": keyboard.Key.cmd,
        "win": keyboard.Key.cmd,
    }
else:
    _MODIFIER_MAP = {}


def _ensure_pynput_available() -> None:
    """Raise an error when global keyboard hooks are unavailable."""
    if not _PYNPUT_AVAILABLE:
        raise RuntimeError(
            "Hotkey listener unavailable on this platform."
        ) from _PYNPUT_IMPORT_ERROR


def _parse_hotkey(hotkey_str: str) -> tuple:
    """Parse a hotkey string into modifier and main key components.

    Args:
        hotkey_str (str): Human-readable hotkey such as ``ctrl+shift+o``.

    Returns:
        tuple: ``(frozenset(modifiers), main_key)`` where ``main_key`` may be
            ``None`` if parsing fails.

    Raises:
        RuntimeError: If ``pynput`` is not available on the current platform.
    """
    _ensure_pynput_available()

    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    modifiers: Set[object] = set()
    main_key = None

    for part in parts:
        if part in _MODIFIER_MAP:
            modifiers.add(_MODIFIER_MAP[part])
        else:
            try:
                main_key = keyboard.Key[part]
            except (KeyError, AttributeError):
                if len(part) == 1:
                    main_key = keyboard.KeyCode.from_char(part)
                else:
                    # Support common aliases for non-character main keys.
                    special_names = {
                        "space": keyboard.Key.space,
                        "enter": keyboard.Key.enter,
                        "return": keyboard.Key.enter,
                        "tab": keyboard.Key.tab,
                        "esc": keyboard.Key.esc,
                        "escape": keyboard.Key.esc,
                    }
                    main_key = special_names.get(part)

    return frozenset(modifiers), main_key


def _normalize_key(key: object) -> object:
    """Normalize key variants so left/right modifiers are treated equally.

    Args:
        key (object): Raw key event object from ``pynput``.

    Returns:
        object: Canonicalized key representation.

    Raises:
        RuntimeError: If ``pynput`` is not available on the current platform.
    """
    _ensure_pynput_available()

    normalization = {
        keyboard.Key.ctrl_r: keyboard.Key.ctrl_l,
        keyboard.Key.alt_r: keyboard.Key.alt_l,
        keyboard.Key.shift_l: keyboard.Key.shift,
        keyboard.Key.shift_r: keyboard.Key.shift,
        keyboard.Key.cmd_l: keyboard.Key.cmd,
        keyboard.Key.cmd_r: keyboard.Key.cmd,
    }
    return normalization.get(key, key)


class HotkeyListener:
    """Listen for a configured global hotkey and invoke a callback.

    Responsibilities:
    - Parse a human-readable hotkey string.
    - Track currently pressed keys.
    - Trigger a callback when all required keys are held.

    Key attributes:
        _hotkey_str: Original hotkey string from configuration.
        _modifiers: Canonical modifier key set required for activation.
        _main_key: Main non-modifier key for activation.
        _pressed: Set of currently pressed normalized keys.
    """

    def __init__(self, hotkey_str: str, callback: Callable[[], None]) -> None:
        """Initialize a hotkey listener instance.

        Args:
            hotkey_str (str): Hotkey definition, for example ``ctrl+shift+o``.
            callback (Callable[[], None]): Function called on hotkey activation.

        Returns:
            None: This constructor does not return a value.

        Raises:
            RuntimeError: If ``pynput`` is unavailable on this platform.
        """
        _ensure_pynput_available()
        self._hotkey_str = hotkey_str
        self._callback = callback
        self._modifiers: FrozenSet[object]
        self._main_key: Optional[object]
        self._modifiers, self._main_key = _parse_hotkey(hotkey_str)
        self._pressed: Set[object] = set()
        self._listener = None
        self._thread: Optional[threading.Thread] = None

    def _on_press(self, key: object) -> None:
        """Handle key-down events from ``pynput`` listener.

        Args:
            key (object): Raw key event.

        Returns:
            None: This callback does not return a value.
        """
        normalized = _normalize_key(key)
        self._pressed.add(normalized)

        # Lowercase characters so uppercase/lowercase presses match config.
        if isinstance(key, keyboard.KeyCode) and key.char:
            self._pressed.add(keyboard.KeyCode.from_char(key.char.lower()))

        if self._main_key is not None:
            modifiers_held = all(m in self._pressed for m in self._modifiers)
            main_held = self._main_key in self._pressed
            if modifiers_held and main_held:
                self._callback()

    def _on_release(self, key: object) -> None:
        """Handle key-up events from ``pynput`` listener.

        Args:
            key (object): Raw key event.

        Returns:
            None: This callback does not return a value.
        """
        normalized = _normalize_key(key)
        self._pressed.discard(normalized)

        if isinstance(key, keyboard.KeyCode) and key.char:
            self._pressed.discard(keyboard.KeyCode.from_char(key.char.lower()))

    def start(self) -> None:
        """Start listening for global hotkey events.

        Returns:
            None: This method does not return a value.

        Raises:
            RuntimeError: If ``pynput`` is unavailable on this platform.
        """
        _ensure_pynput_available()
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for global hotkey events.

        Returns:
            None: This method does not return a value.

        Raises:
            None: This method suppresses listener absence gracefully.
        """
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    @property
    def hotkey_string(self) -> str:
        """Return the configured hotkey string.

        Returns:
            str: Original human-readable hotkey configuration string.

        Raises:
            None: This property accessor does not raise application errors.
        """
        return self._hotkey_str


def capture_hotkey() -> str:
    """Interactively capture a hotkey combination from the keyboard.

    Returns:
        str: Captured hotkey string, or default ``ctrl+shift+o`` if capture
            times out.

    Raises:
        RuntimeError: If ``pynput`` is unavailable on this platform.
    """
    _ensure_pynput_available()

    captured_keys: Set[object] = set()
    result: list = []
    event = threading.Event()

    def on_press(key: object) -> None:
        normalized = _normalize_key(key)
        captured_keys.add(normalized)

    def on_release(key: object) -> Optional[bool]:
        parts: list = []

        # Keep a stable modifier order so captured strings are predictable.
        modifier_order = [
            (keyboard.Key.ctrl_l, "ctrl"),
            (keyboard.Key.alt_l, "alt"),
            (keyboard.Key.shift, "shift"),
            (keyboard.Key.cmd, "cmd"),
        ]
        has_modifier = False
        for mod_key, mod_name in modifier_order:
            if mod_key in captured_keys:
                parts.append(mod_name)
                has_modifier = True

        for k in captured_keys:
            if k not in {m[0] for m in modifier_order}:
                if isinstance(k, keyboard.KeyCode):
                    char = k.char if k.char else str(k)
                    parts.append(char.lower())
                elif isinstance(k, keyboard.Key):
                    parts.append(k.name)

        if has_modifier and len(parts) > 1:
            result.append("+".join(parts))
            event.set()
            return False
        return None

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    event.wait(timeout=30)
    listener.stop()

    if result:
        return result[0]
    return "ctrl+shift+o"
