"""Global hotkey listener using pynput — toggle and push-to-talk modes."""

import logging
import threading
from typing import Callable

from pynput import keyboard

logger = logging.getLogger(__name__)

# Time to wait before treating a release as real (seconds).
# X11 auto-repeat fires release+press pairs <10ms apart; 100ms is safe for KDE.
_RELEASE_DEBOUNCE = 0.1


def _parse_key(key_string: str) -> keyboard.Key | keyboard.KeyCode:
    """Convert a string like 'Key.f12' or 'a' to a pynput key object."""
    if key_string.startswith("Key."):
        attr = key_string[4:]  # strip 'Key.'
        return getattr(keyboard.Key, attr)
    return keyboard.KeyCode.from_char(key_string)


class HotkeyListener:
    """Hotkey listener with two modes:

    - **toggle**: press once to start recording, press again to stop.
    - **push-to-talk**: hold to record, release to stop (with X11 debounce).
    """

    def __init__(
        self,
        key_string: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
        mode: str = "toggle",
    ):
        self._key = _parse_key(key_string)
        self._on_press_cb = on_press
        self._on_release_cb = on_release
        self._mode = mode
        self._pressed = False
        self._release_timer: threading.Timer | None = None
        self._listener: keyboard.Listener | None = None

    @property
    def mode(self) -> str:
        return self._mode

    def update_mode(self, mode: str) -> None:
        """Change hotkey mode at runtime (toggle / push-to-talk)."""
        if mode not in ("toggle", "push-to-talk"):
            logger.warning("Unknown hotkey mode '%s', ignoring", mode)
            return
        logger.info("Hotkey mode changed: %s -> %s", self._mode, mode)
        self._mode = mode
        self._pressed = False
        if self._release_timer is not None:
            self._release_timer.cancel()
            self._release_timer = None

    def _on_press(self, key) -> None:
        try:
            if key != self._key:
                return

            if self._mode == "toggle":
                self._on_press_toggle()
            else:
                self._on_press_push_to_talk()
        except Exception as e:
            logger.error("Error in on_press callback: %s", e)

    def _on_press_toggle(self) -> None:
        """Toggle mode: each press fires the press callback (app decides action)."""
        # Cancel any pending debounce timer from a previous push-to-talk session
        if self._release_timer is not None:
            self._release_timer.cancel()
            self._release_timer = None

        # Ignore X11 auto-repeat: only fire on the first press
        if not self._pressed:
            self._pressed = True
            self._on_press_cb()

    def _on_press_push_to_talk(self) -> None:
        """Push-to-talk: press starts recording, with X11 debounce."""
        # Cancel pending release — it was X11 auto-repeat, not real
        if self._release_timer is not None:
            self._release_timer.cancel()
            self._release_timer = None
        if not self._pressed:
            self._pressed = True
            self._on_press_cb()

    def _on_release(self, key) -> None:
        try:
            if key != self._key or not self._pressed:
                return

            if self._mode == "toggle":
                # Toggle mode: release resets pressed flag, no callback
                self._pressed = False
            else:
                # Push-to-talk: debounce to filter X11 auto-repeat
                self._release_timer = threading.Timer(
                    _RELEASE_DEBOUNCE, self._handle_real_release,
                )
                self._release_timer.daemon = True
                self._release_timer.start()
        except Exception as e:
            logger.error("Error in on_release callback: %s", e)

    def _handle_real_release(self) -> None:
        """Called after debounce delay — this is a genuine key release."""
        self._release_timer = None
        self._pressed = False
        try:
            self._on_release_cb()
        except Exception as e:
            logger.error("Error in on_release callback: %s", e)

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
