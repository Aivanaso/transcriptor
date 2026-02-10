"""System tray icon — selects the best backend for the current platform."""

import sys
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"

# Icon names without extension for AppIndicator (looks up PNGs by name),
# with .png extension added by the pystray backend when needed.
STATE_ICONS = {
    "loading": "icon_processing",
    "idle": "icon_idle",
    "recording": "icon_recording",
    "processing": "icon_processing",
}

STATE_LABELS = {
    "loading": "Cargando modelo...",
    "idle": "Listo (F12 para grabar)",
    "recording": "Grabando...",
    "processing": "Procesando...",
}

if sys.platform == "linux":
    try:
        from transcriptor._tray_linux import TrayIcon
    except (ImportError, ValueError):
        from transcriptor._tray_pystray import TrayIcon
else:
    from transcriptor._tray_pystray import TrayIcon

__all__ = ["TrayIcon", "ASSETS_DIR", "STATE_ICONS", "STATE_LABELS"]
