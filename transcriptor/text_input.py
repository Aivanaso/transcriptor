"""Inject transcribed text into the active application."""

import os
import subprocess
import time

CLIPBOARD_THRESHOLD = 100  # chars; above this, use clipboard + Ctrl+V


def _is_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def _get_clipboard_x11() -> str:
    """Get current X11 clipboard contents."""
    try:
        return subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _set_clipboard_x11(text: str) -> None:
    proc = subprocess.Popen(
        ["xclip", "-selection", "clipboard"],
        stdin=subprocess.PIPE,
    )
    proc.communicate(input=text.encode("utf-8"))


def _get_clipboard_wayland() -> str:
    try:
        return subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True, text=True, timeout=2,
        ).stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _set_clipboard_wayland(text: str) -> None:
    proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
    proc.communicate(input=text.encode("utf-8"))


def inject_text(text: str) -> None:
    """Type text into the currently focused application."""
    if not text:
        return

    wayland = _is_wayland()

    if len(text) > CLIPBOARD_THRESHOLD:
        _inject_via_clipboard(text, wayland)
    else:
        _inject_via_typing(text, wayland)


def _inject_via_typing(text: str, wayland: bool) -> None:
    if wayland:
        subprocess.run(["wtype", text], timeout=5)
    else:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", "12", text],
            timeout=10,
        )


def _inject_via_clipboard(text: str, wayland: bool) -> None:
    # Save previous clipboard
    if wayland:
        prev = _get_clipboard_wayland()
        _set_clipboard_wayland(text)
    else:
        prev = _get_clipboard_x11()
        _set_clipboard_x11(text)

    time.sleep(0.05)

    # Paste
    if wayland:
        subprocess.run(["wtype", "-M", "ctrl", "v", "-m", "ctrl"], timeout=5)
    else:
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+v"], timeout=5)

    time.sleep(0.1)

    # Restore previous clipboard
    if wayland:
        _set_clipboard_wayland(prev)
    else:
        _set_clipboard_x11(prev)
