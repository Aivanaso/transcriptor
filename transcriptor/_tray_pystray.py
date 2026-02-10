"""System tray backend using pystray (fallback for macOS/Windows)."""

import threading
from typing import Callable

import pystray
from PIL import Image

from transcriptor.tray import ASSETS_DIR, STATE_ICONS, STATE_LABELS


def _icon_path(state: str) -> "Path":
    """Resolve icon name to a full .png path."""
    name = STATE_ICONS.get(state, "icon_idle")
    return ASSETS_DIR / f"{name}.png"


class TrayIcon:
    """System tray icon with state-based visuals and context menu."""

    def __init__(self, on_settings: Callable[[], None], on_quit: Callable[[], None]):
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._state = "loading"

        path = _icon_path("loading")
        image = Image.open(path) if path.exists() else _generate_icon("yellow")

        self._icon = pystray.Icon(
            name="transcriptor",
            icon=image,
            title="Transcriptor - Cargando...",
            menu=self._build_menu(),
        )

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda _: STATE_LABELS.get(self._state, ""),
                action=None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Configuración", self._settings_clicked),
            pystray.MenuItem("Salir", self._quit_clicked),
        )

    def _settings_clicked(self, icon, item) -> None:
        threading.Thread(target=self._on_settings, daemon=True).start()

    def _quit_clicked(self, icon, item) -> None:
        self._on_quit()

    def set_state(self, state: str) -> None:
        """Update tray icon to reflect current app state."""
        self._state = state
        path = _icon_path(state)

        if path.exists():
            image = Image.open(path)
        else:
            colors = {"idle": "green", "recording": "red", "processing": "yellow", "loading": "yellow"}
            image = _generate_icon(colors.get(state, "gray"))

        self._icon.icon = image
        self._icon.title = f"Transcriptor - {STATE_LABELS.get(state, state)}"
        self._icon.menu = self._build_menu()

    def run(self) -> None:
        """Start the tray icon. Blocks the calling thread."""
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon."""
        self._icon.stop()


def _generate_icon(color: str, size: int = 64) -> Image.Image:
    """Generate a simple colored circle icon as fallback."""
    from PIL import ImageDraw

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 4
    draw.ellipse([margin, margin, size - margin, size - margin], fill=color)
    return img
