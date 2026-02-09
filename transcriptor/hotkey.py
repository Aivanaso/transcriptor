"""Global hotkey listener using pynput."""

from typing import Callable

from pynput import keyboard


def _parse_key(key_string: str) -> keyboard.Key | keyboard.KeyCode:
    """Convert a string like 'Key.f12' or 'a' to a pynput key object."""
    if key_string.startswith("Key."):
        attr = key_string[4:]  # strip 'Key.'
        return getattr(keyboard.Key, attr)
    return keyboard.KeyCode.from_char(key_string)


class HotkeyListener:
    """Listens for a global hotkey and calls a callback on press."""

    def __init__(self, key_string: str, callback: Callable[[], None]):
        self._key = _parse_key(key_string)
        self._callback = callback
        self._listener: keyboard.Listener | None = None

    def _on_press(self, key) -> None:
        try:
            if key == self._key:
                self._callback()
        except Exception as e:
            print(f"[hotkey] Error in callback: {e}")

    def start(self) -> None:
        """Start the hotkey listener in a daemon thread."""
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def update_key(self, key_string: str) -> None:
        """Change the hotkey. Restarts the listener."""
        self._key = _parse_key(key_string)
        if self._listener is not None:
            self.stop()
            self.start()
