"""Global hotkey listener using pynput — push-to-talk mode."""

from typing import Callable

from pynput import keyboard


def _parse_key(key_string: str) -> keyboard.Key | keyboard.KeyCode:
    """Convert a string like 'Key.f12' or 'a' to a pynput key object."""
    if key_string.startswith("Key."):
        attr = key_string[4:]  # strip 'Key.'
        return getattr(keyboard.Key, attr)
    return keyboard.KeyCode.from_char(key_string)


class HotkeyListener:
    """Push-to-talk: press to start recording, release to stop.

    Handles X11 key repeat (repeated press events while held) via a
    ``_pressed`` flag that debounces spurious presses.
    """

    def __init__(
        self,
        key_string: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ):
        self._key = _parse_key(key_string)
        self._on_press_cb = on_press
        self._on_release_cb = on_release
        self._pressed = False
        self._listener: keyboard.Listener | None = None

    def _on_press(self, key) -> None:
        try:
            if key == self._key and not self._pressed:
                self._pressed = True
                self._on_press_cb()
        except Exception as e:
            print(f"[hotkey] Error in on_press callback: {e}")

    def _on_release(self, key) -> None:
        try:
            if key == self._key and self._pressed:
                self._pressed = False
                self._on_release_cb()
        except Exception as e:
            print(f"[hotkey] Error in on_release callback: {e}")

    def start(self) -> None:
        """Start the hotkey listener in a daemon thread."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
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
        self._pressed = False
        if self._listener is not None:
            self.stop()
            self.start()
