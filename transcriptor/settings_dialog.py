"""CustomTkinter settings dialog for Transcriptor."""

import threading
from typing import Callable

import customtkinter as ctk

from transcriptor.audio import get_input_devices

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

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


class SettingsDialog:
    """Settings window for Transcriptor using CustomTkinter."""

    def __init__(self, config: dict, on_save: Callable[[dict], None]):
        self._config = config.copy()
        self._on_save = on_save
        self._capturing_hotkey = False
        self._lang_codes = list(LANGUAGES.keys())
        self._lang_labels = [f"{LANGUAGES[c]} ({c})" for c in self._lang_codes]

        self._root = ctk.CTk()
        self._root.title("Transcriptor - Configuración")
        self._root.geometry("420x480")
        self._root.resizable(False, False)

        frame = ctk.CTkFrame(self._root, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Model
        ctk.CTkLabel(frame, text="Modelo de Whisper", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w"
        )
        self._model_var = ctk.StringVar(value=config.get("model_size", "small"))
        ctk.CTkOptionMenu(frame, variable=self._model_var, values=MODELS).pack(
            fill="x", pady=(4, 12)
        )

        # Language
        ctk.CTkLabel(frame, text="Idioma", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w"
        )
        current_lang = config.get("language", "es")
        current_idx = self._lang_codes.index(current_lang) if current_lang in self._lang_codes else 0
        self._lang_var = ctk.StringVar(value=self._lang_labels[current_idx])
        ctk.CTkOptionMenu(frame, variable=self._lang_var, values=self._lang_labels).pack(
            fill="x", pady=(4, 12)
        )

        # Audio device
        ctk.CTkLabel(frame, text="Dispositivo de audio", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w"
        )
        self._devices = get_input_devices()
        device_labels = ["Por defecto (PipeWire/Pulse)"] + [
            f"{d['name']} ({int(d['default_samplerate'])} Hz)" for d in self._devices
        ]
        current_device = config.get("audio_device")
        current_device_label = "Por defecto (PipeWire/Pulse)"
        if current_device is not None:
            for d in self._devices:
                if d["index"] == current_device:
                    current_device_label = f"{d['name']} ({int(d['default_samplerate'])} Hz)"
                    break
        self._device_var = ctk.StringVar(value=current_device_label)
        ctk.CTkOptionMenu(frame, variable=self._device_var, values=device_labels).pack(
            fill="x", pady=(4, 12)
        )

        # Hotkey
        ctk.CTkLabel(frame, text="Tecla de grabación", font=ctk.CTkFont(size=13, weight="bold")).pack(
            anchor="w"
        )
        self._hotkey_var = ctk.StringVar(value=config.get("hotkey", "Key.f12"))
        self._hotkey_button = ctk.CTkButton(
            frame,
            textvariable=self._hotkey_var,
            command=self._on_hotkey_capture,
            fg_color="gray30",
            hover_color="gray40",
        )
        self._hotkey_button.pack(fill="x", pady=(4, 12))

        # Auto-paste
        self._auto_paste_var = ctk.BooleanVar(value=config.get("auto_paste", True))
        ctk.CTkCheckBox(frame, text="Pegar texto automáticamente", variable=self._auto_paste_var).pack(
            anchor="w", pady=(0, 4)
        )

        # Notifications
        self._notif_var = ctk.BooleanVar(value=config.get("notifications", True))
        ctk.CTkCheckBox(frame, text="Mostrar notificaciones", variable=self._notif_var).pack(
            anchor="w", pady=(0, 16)
        )

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        ctk.CTkButton(
            btn_frame, text="Guardar", command=self._on_save_clicked, width=120
        ).pack(side="right")
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._root.destroy,
            width=100,
            fg_color="gray30",
            hover_color="gray40",
        ).pack(side="right", padx=(0, 8))

        self._root.bind("<KeyPress>", self._on_key_press)

    def _on_hotkey_capture(self) -> None:
        self._capturing_hotkey = True
        self._hotkey_var.set("Pulsa una tecla...")
        self._hotkey_button.configure(fg_color="#b5651d", hover_color="#c47a2a")

    def _on_key_press(self, event) -> None:
        if not self._capturing_hotkey:
            return
        self._capturing_hotkey = False
        keysym = event.keysym
        pynput_key = f"Key.{keysym.lower()}"
        self._hotkey_var.set(pynput_key)
        self._config["hotkey"] = pynput_key
        self._hotkey_button.configure(fg_color="gray30", hover_color="gray40")

    def _on_save_clicked(self) -> None:
        self._config["model_size"] = self._model_var.get()
        self._config["language"] = self._lang_codes[self._lang_labels.index(self._lang_var.get())]
        self._config["auto_paste"] = self._auto_paste_var.get()
        self._config["notifications"] = self._notif_var.get()

        # Audio device: None for default, int index for specific device
        device_label = self._device_var.get()
        if device_label == "Por defecto (PipeWire/Pulse)":
            self._config["audio_device"] = None
        else:
            # Strip " (48000 Hz)" suffix to get the raw device name
            selected_name = device_label.rsplit(" (", 1)[0]
            for d in self._devices:
                if d["name"] == selected_name:
                    self._config["audio_device"] = d["index"]
                    break

        self._on_save(self._config)
        self._root.destroy()

    def run(self) -> None:
        self._root.mainloop()


def show_settings_dialog(config: dict, on_save: Callable[[dict], None]) -> None:
    """Show the settings dialog in a new thread (customtkinter runs its own mainloop)."""
    def _run():
        dialog = SettingsDialog(config, on_save)
        dialog.run()
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
