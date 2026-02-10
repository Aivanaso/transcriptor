"""Global hotkey listener using pynput — push-to-talk mode."""

import threading
from typing import Callable

from pynput import keyboard

# Time to wait before treating a release as real (seconds).
# X11 auto-repeat fires release+press pairs <10ms apart; 50ms is safe.
_RELEASE_DEBOUNCE = 0.05


def _parse_key(key_string: str) -> keyboard.Key | keyboard.KeyCode:
    """Convert a string like 'Key.f12' or 'a' to a pynput key object."""
    if key_string.startswith("Key."):
        attr = key_string[4:]  # strip 'Key.'
        return getattr(keyboard.Key, attr)
    return keyboard.KeyCode.from_char(key_string)


class HotkeyListener:
    """Push-to-talk: press to start recording, release to stop.

    X11 key repeat generates synthetic ``release → press`` pairs while a key
    is held down.  We debounce releases with a short timer: if a press arrives
    within ``_RELEASE_DEBOUNCE`` seconds, the release was fake and we cancel it.
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
        self._release_timer: threading.Timer | None = None
        self._listener: keyboard.Listener | None = None

    def _on_press(self, key) -> None:
        try:
            if key != self._key:
                return
            # Cancel pending release — it was X11 auto-repeat, not real
            if self._release_timer is not None:
                self._release_timer.cancel()
                self._release_timer = None
            if not self._pressed:
                self._pressed = True
                print("[hotkey] PRESS (real)")
                self._on_press_cb()
            else:
                print("[hotkey] press (repeat, ignored)")
        except Exception as e:
            print(f"[hotkey] Error in on_press callback: {e}")

    def _on_release(self, key) -> None:
        try:
            if key == self._key and self._pressed:
                # Delay: real releases have no press following within 50ms
                self._release_timer = threading.Timer(
                    _RELEASE_DEBOUNCE, self._handle_real_release,
                )
                self._release_timer.daemon = True
                self._release_timer.start()
        except Exception as e:
            print(f"[hotkey] Error in on_release callback: {e}")

    def _handle_real_release(self) -> None:
        """Called after debounce delay — this is a genuine key release."""
        self._release_timer = None
        self._pressed = False
        try:
            print("[hotkey] RELEASE (real)")
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
        if self._release_timer is not None:
            self._release_timer.cancel()
            self._release_timer = None
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def update_key(self, key_string: str) -> None:
        """Change the hotkey. Restarts the listener."""
        self._key = _parse_key(key_string)
        self._pressed = False
        if self._release_timer is not None:
            self._release_timer.cancel()
            self._release_timer = None
        if self._listener is not None:
            self.stop()
            self.start()
