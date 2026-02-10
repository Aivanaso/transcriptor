"""System tray backend using AppIndicator3 + GTK3 (Linux native)."""

import signal
import threading
from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator
except ValueError:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator

from transcriptor.tray import ASSETS_DIR, STATE_ICONS, STATE_LABELS


class TrayIcon:
    """System tray icon using AppIndicator3 for native Linux support."""

    def __init__(self, on_settings: Callable[[], None], on_quit: Callable[[], None]):
        self._on_settings = on_settings
        self._on_quit = on_quit

        self._indicator = AppIndicator.Indicator.new(
            "transcriptor",
            STATE_ICONS["loading"],
            AppIndicator.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_icon_theme_path(str(ASSETS_DIR))
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._indicator.set_title("Transcriptor - Cargando...")

        self._build_menu()
        self._indicator.set_menu(self._menu)

    def _build_menu(self) -> None:
        """Build the GTK menu once. Only labels get updated later."""
        self._menu = Gtk.Menu()

        self._status_item = Gtk.MenuItem(label=STATE_LABELS["loading"])
        self._status_item.set_sensitive(False)
        self._menu.append(self._status_item)

        self._menu.append(Gtk.SeparatorMenuItem())

        settings_item = Gtk.MenuItem(label="Configuración")
        settings_item.connect("activate", self._settings_clicked)
        self._menu.append(settings_item)

        quit_item = Gtk.MenuItem(label="Salir")
        quit_item.connect("activate", self._quit_clicked)
        self._menu.append(quit_item)

        self._menu.show_all()

    def _settings_clicked(self, widget) -> None:
        threading.Thread(target=self._on_settings, daemon=True).start()

    def _quit_clicked(self, widget) -> None:
        self._on_quit()

    def set_state(self, state: str) -> None:
        """Update tray icon to reflect current app state (thread-safe)."""
        GLib.idle_add(self._update_state, state)

    def _update_state(self, state: str) -> bool:
        """Update icon and label on the GTK main thread."""
        icon_name = STATE_ICONS.get(state, "icon_idle")
        label = STATE_LABELS.get(state, state)

        self._indicator.set_icon_full(icon_name, label)
        self._indicator.set_title(f"Transcriptor - {label}")
        self._status_item.set_label(label)

        return GLib.SOURCE_REMOVE

    def run(self) -> None:
        """Start the GTK main loop. Blocks the calling thread."""
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()

    def stop(self) -> None:
        """Stop the GTK main loop."""
        GLib.idle_add(self._do_stop)

    def _do_stop(self) -> bool:
        self._indicator.set_status(AppIndicator.IndicatorStatus.PASSIVE)
        Gtk.main_quit()
        return GLib.SOURCE_REMOVE
