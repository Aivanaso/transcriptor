"""GTK 3 settings dialog for Transcriptor."""

from typing import Callable

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

MODELS = ["tiny", "base", "small", "medium", "large-v3"]

LANGUAGES = {
    "es": "Español",
    "en": "English",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "pt": "Português",
    "ca": "Català",
    "eu": "Euskara",
    "gl": "Galego",
}


class SettingsDialog(Gtk.Window):
    """Settings window for Transcriptor."""

    def __init__(self, config: dict, on_save: Callable[[dict], None]):
        super().__init__(title="Transcriptor - Configuración")
        self._config = config.copy()
        self._on_save = on_save
        self._capturing_hotkey = False

        self.set_default_size(400, 350)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_border_width(16)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)

        # Model
        vbox.pack_start(self._label("Modelo de Whisper"), False, False, 0)
        self._model_combo = Gtk.ComboBoxText()
        for m in MODELS:
            self._model_combo.append_text(m)
        self._model_combo.set_active(MODELS.index(config.get("model_size", "small")))
        vbox.pack_start(self._model_combo, False, False, 0)

        # Language
        vbox.pack_start(self._label("Idioma"), False, False, 0)
        self._lang_combo = Gtk.ComboBoxText()
        lang_codes = list(LANGUAGES.keys())
        for code in lang_codes:
            self._lang_combo.append_text(f"{LANGUAGES[code]} ({code})")
        current_lang = config.get("language", "es")
        if current_lang in lang_codes:
            self._lang_combo.set_active(lang_codes.index(current_lang))
        else:
            self._lang_combo.set_active(0)
        self._lang_codes = lang_codes
        vbox.pack_start(self._lang_combo, False, False, 0)

        # Hotkey
        vbox.pack_start(self._label("Tecla de grabación"), False, False, 0)
        self._hotkey_button = Gtk.Button(label=config.get("hotkey", "Key.f12"))
        self._hotkey_button.connect("clicked", self._on_hotkey_capture)
        vbox.pack_start(self._hotkey_button, False, False, 0)

        # Auto-paste toggle
        self._auto_paste_switch = Gtk.CheckButton(label="Pegar texto automáticamente")
        self._auto_paste_switch.set_active(config.get("auto_paste", True))
        vbox.pack_start(self._auto_paste_switch, False, False, 0)

        # Notifications toggle
        self._notif_switch = Gtk.CheckButton(label="Mostrar notificaciones")
        self._notif_switch.set_active(config.get("notifications", True))
        vbox.pack_start(self._notif_switch, False, False, 0)

        # Buttons
        btn_box = Gtk.Box(spacing=8)
        save_btn = Gtk.Button(label="Guardar")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda _: self.close())
        btn_box.pack_end(save_btn, False, False, 0)
        btn_box.pack_end(cancel_btn, False, False, 0)
        vbox.pack_end(btn_box, False, False, 0)

        self.connect("key-press-event", self._on_key_press)

    def _label(self, text: str) -> Gtk.Label:
        label = Gtk.Label(label=text, xalign=0)
        label.set_markup(f"<b>{text}</b>")
        return label

    def _on_hotkey_capture(self, button) -> None:
        self._capturing_hotkey = True
        button.set_label("Pulsa una tecla...")

    def _on_key_press(self, widget, event) -> bool:
        if not self._capturing_hotkey:
            return False
        self._capturing_hotkey = False
        key_name = Gdk.keyval_name(event.keyval)
        # Map GDK key names to pynput format
        pynput_key = f"Key.{key_name.lower()}"
        self._hotkey_button.set_label(pynput_key)
        self._config["hotkey"] = pynput_key
        return True

    def _on_save_clicked(self, button) -> None:
        self._config["model_size"] = MODELS[self._model_combo.get_active()]
        self._config["language"] = self._lang_codes[self._lang_combo.get_active()]
        self._config["auto_paste"] = self._auto_paste_switch.get_active()
        self._config["notifications"] = self._notif_switch.get_active()
        self._on_save(self._config)
        self.close()


def show_settings_dialog(config: dict, on_save: Callable[[dict], None]) -> None:
    """Show the settings dialog. Must be called from any thread - uses GLib.idle_add."""
    def _show():
        dialog = SettingsDialog(config, on_save)
        dialog.show_all()
        return False  # remove from idle
    GLib.idle_add(_show)
