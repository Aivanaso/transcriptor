"""GTK3 settings dialog for Transcriptor."""

import logging
from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import GLib, Gdk, Gtk

from transcriptor.audio import get_input_devices

logger = logging.getLogger(__name__)

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

HOTKEY_MODES = {
    "toggle": "Toggle (pulsar para iniciar/parar)",
    "push-to-talk": "Push-to-talk (mantener pulsado)",
}

PASTE_OPTIONS = {
    "auto": "Auto (detectar terminal)",
    "ctrl+v": "Ctrl+V",
    "ctrl+shift+v": "Ctrl+Shift+V",
}


class SettingsDialog:
    """Settings dialog for Transcriptor using GTK3."""

    def __init__(self, config: dict, on_save: Callable[[dict], None]):
        self._config = config.copy()
        self._on_save = on_save
        self._capturing_hotkey = False
        self._devices = get_input_devices()

        self._dialog = Gtk.Dialog(
            title="Transcriptor - Configuración",
            flags=Gtk.DialogFlags.MODAL,
        )
        self._dialog.set_default_size(420, -1)
        self._dialog.set_resizable(False)
        self._dialog.set_position(Gtk.WindowPosition.CENTER)

        content = self._dialog.get_content_area()
        content.set_spacing(6)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(16)
        content.set_margin_bottom(8)

        # --- Model ---
        content.pack_start(self._make_label("Modelo de Whisper"), False, False, 0)
        self._model_combo = Gtk.ComboBoxText()
        current_model = config.get("model_size", "small")
        for i, model in enumerate(MODELS):
            self._model_combo.append_text(model)
            if model == current_model:
                self._model_combo.set_active(i)
        content.pack_start(self._model_combo, False, False, 4)

        # --- Language ---
        content.pack_start(self._make_label("Idioma"), False, False, 0)
        self._lang_combo = Gtk.ComboBoxText()
        self._lang_codes = list(LANGUAGES.keys())
        current_lang = config.get("language", "es")
        for i, code in enumerate(self._lang_codes):
            self._lang_combo.append_text(f"{LANGUAGES[code]} ({code})")
            if code == current_lang:
                self._lang_combo.set_active(i)
        content.pack_start(self._lang_combo, False, False, 4)

        # --- Audio device ---
        content.pack_start(self._make_label("Dispositivo de audio"), False, False, 0)
        self._device_combo = Gtk.ComboBoxText()
        self._device_combo.append_text("Por defecto (PipeWire/Pulse)")
        current_device = config.get("audio_device")
        active_device_idx = 0
        for i, dev in enumerate(self._devices):
            label = f"{dev['name']} ({int(dev['default_samplerate'])} Hz)"
            self._device_combo.append_text(label)
            if dev["index"] == current_device:
                active_device_idx = i + 1
        self._device_combo.set_active(active_device_idx)
        content.pack_start(self._device_combo, False, False, 4)

        # --- Hotkey mode ---
        content.pack_start(self._make_label("Modo de hotkey"), False, False, 0)
        self._mode_combo = Gtk.ComboBoxText()
        self._mode_keys = list(HOTKEY_MODES.keys())
        current_mode = config.get("hotkey_mode", "toggle")
        for i, key in enumerate(self._mode_keys):
            self._mode_combo.append_text(HOTKEY_MODES[key])
            if key == current_mode:
                self._mode_combo.set_active(i)
        content.pack_start(self._mode_combo, False, False, 4)

        # --- Hotkey ---
        content.pack_start(self._make_label("Tecla de grabación"), False, False, 0)
        self._hotkey_button = Gtk.Button(label=config.get("hotkey", "Key.f12"))
        self._hotkey_button.connect("clicked", self._on_hotkey_capture)
        content.pack_start(self._hotkey_button, False, False, 4)

        # --- Paste shortcut ---
        content.pack_start(self._make_label("Atajo de pegado"), False, False, 0)
        self._paste_combo = Gtk.ComboBoxText()
        self._paste_keys = list(PASTE_OPTIONS.keys())
        current_paste = config.get("paste_shortcut", "auto")
        for i, key in enumerate(self._paste_keys):
            self._paste_combo.append_text(PASTE_OPTIONS[key])
            if key == current_paste:
                self._paste_combo.set_active(i)
        content.pack_start(self._paste_combo, False, False, 4)

        # --- Auto-paste checkbox ---
        self._auto_paste_check = Gtk.CheckButton(label="Pegar texto automáticamente")
        self._auto_paste_check.set_active(config.get("auto_paste", True))
        content.pack_start(self._auto_paste_check, False, False, 8)

        # --- Notifications checkbox ---
        self._notif_check = Gtk.CheckButton(label="Mostrar notificaciones")
        self._notif_check.set_active(config.get("notifications", True))
        content.pack_start(self._notif_check, False, False, 4)

        # --- Buttons ---
        self._dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        save_btn = self._dialog.add_button("Guardar", Gtk.ResponseType.OK)
        save_btn.get_style_context().add_class("suggested-action")

        # Key capture handler
        self._dialog.connect("key-press-event", self._on_key_press)

        self._dialog.show_all()

    @staticmethod
    def _make_label(text: str) -> Gtk.Label:
        label = Gtk.Label(label=text, xalign=0)
        label.set_markup(f"<b>{text}</b>")
        label.set_margin_top(8)
        return label

    def _on_hotkey_capture(self, button) -> None:
        self._capturing_hotkey = True
        self._hotkey_button.set_label("Pulsa una tecla...")

    def _on_key_press(self, widget, event) -> bool:
        if not self._capturing_hotkey:
            return False
        self._capturing_hotkey = False

        keyval_name = Gdk.keyval_name(event.keyval)
        if keyval_name:
            pynput_key = f"Key.{keyval_name.lower()}"
            self._hotkey_button.set_label(pynput_key)
            self._config["hotkey"] = pynput_key
        return True

    def _collect_config(self) -> dict:
        """Read all widget values into a config dict."""
        config = self._config.copy()
        config["model_size"] = MODELS[self._model_combo.get_active()]
        config["language"] = self._lang_codes[self._lang_combo.get_active()]
        config["hotkey_mode"] = self._mode_keys[self._mode_combo.get_active()]
        config["auto_paste"] = self._auto_paste_check.get_active()
        config["notifications"] = self._notif_check.get_active()
        config["paste_shortcut"] = self._paste_keys[self._paste_combo.get_active()]

        # Audio device: None for default, int index for specific device
        device_idx = self._device_combo.get_active()
        if device_idx == 0:
            config["audio_device"] = None
        else:
            config["audio_device"] = self._devices[device_idx - 1]["index"]

        return config

    def run(self) -> None:
        """Run the dialog and handle the response."""
        response = self._dialog.run()
        if response == Gtk.ResponseType.OK:
            config = self._collect_config()
            self._on_save(config)
            logger.info("Settings saved")
        self._dialog.destroy()


def show_settings_dialog(config: dict, on_save: Callable[[dict], None]) -> None:
    """Show the settings dialog on the GTK main thread."""
    def _open():
        dialog = SettingsDialog(config, on_save)
        dialog.run()
        return GLib.SOURCE_REMOVE

    GLib.idle_add(_open)
