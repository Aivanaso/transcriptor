"""Inject transcribed text into the active application via clipboard."""

import os
import subprocess
import time

_TERMINAL_CLASSES = frozenset({
    "gnome-terminal-server", "gnome-terminal",
    "konsole", "xterm", "kitty", "alacritty",
    "terminator", "xfce4-terminal", "tilix",
    "st", "st-256color", "urxvt",
    "wezterm-gui", "foot", "tabby", "hyper",
})


def _is_wayland() -> bool:
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def _active_window_is_terminal() -> bool:
    """Check WM_CLASS of focused X11 window against known terminals."""
    try:
        result = subprocess.run(
            ["xdotool", "getactivewindow", "getwindowclassname"],
            capture_output=True, text=True, timeout=1,
        )
        wm_class = result.stdout.strip().lower()
        return wm_class in _TERMINAL_CLASSES
    except Exception:
        return False


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


def inject_text(text: str, paste_shortcut: str = "auto") -> None:
    """Inject text into the focused app via clipboard paste.

    Args:
        text: The text to inject.
        paste_shortcut: "auto" detects terminals for Ctrl+Shift+V,
                        or force "ctrl+v" / "ctrl+shift+v".
    """
    if not text:
        return

    wayland = _is_wayland()

    if paste_shortcut == "auto":
        shortcut = "ctrl+shift+v" if not wayland and _active_window_is_terminal() else "ctrl+v"
    else:
        shortcut = paste_shortcut

    _inject_via_clipboard(text, wayland, shortcut)


def _inject_via_clipboard(text: str, wayland: bool, shortcut: str) -> None:
    # Save previous clipboard
    if wayland:
        prev = _get_clipboard_wayland()
        _set_clipboard_wayland(text)
    else:
        prev = _get_clipboard_x11()
        _set_clipboard_x11(text)

    time.sleep(0.05)

    # Paste with the resolved shortcut
    if wayland:
        # Build wtype args: -M for each modifier, key, -m to release
        modifiers = shortcut.split("+")[:-1]  # e.g. ["ctrl", "shift"]
        key = shortcut.split("+")[-1]         # e.g. "v"
        wtype_args = ["wtype"]
        for mod in modifiers:
            wtype_args += ["-M", mod]
        wtype_args.append(key)
        for mod in reversed(modifiers):
            wtype_args += ["-m", mod]
        subprocess.run(wtype_args, timeout=5)
    else:
        subprocess.run(["xdotool", "key", "--clearmodifiers", shortcut], timeout=5)

    time.sleep(0.1)

    # Restore previous clipboard
    if wayland:
        _set_clipboard_wayland(prev)
    else:
        _set_clipboard_x11(prev)
