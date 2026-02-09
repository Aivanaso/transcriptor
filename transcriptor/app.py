"""Main application coordinator with state machine."""

import enum
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor

from transcriptor.audio import AudioRecorder, SAMPLE_RATE
from transcriptor.config import load_config, save_config
from transcriptor.hotkey import HotkeyListener
from transcriptor.text_input import inject_text
from transcriptor.transcriber import Transcriber
from transcriptor.tray import TrayIcon


class State(enum.Enum):
    LOADING = "loading"
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class App:
    """Coordinates all components of Transcriptor."""

    def __init__(self):
        self.config = load_config()
        self._state = State.LOADING
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)

        # Components
        self.transcriber = Transcriber(
            model_size=self.config["model_size"],
            device=self.config["device"],
            compute_type=self.config["compute_type"],
        )
        self.audio = AudioRecorder()
        self.hotkey = HotkeyListener(self.config["hotkey"], self._on_hotkey)
        self.tray = TrayIcon(
            on_settings=self._on_settings,
            on_quit=self._on_quit,
        )

        # Load model in background
        self._executor.submit(self._load_model)

    @property
    def state(self) -> State:
        return self._state

    def _set_state(self, new_state: State) -> None:
        self._state = new_state
        self.tray.set_state(new_state.value)

    def _notify(self, summary: str, body: str = "") -> None:
        if not self.config.get("notifications", True):
            return
        cmd = ["notify-send", "-a", "Transcriptor", summary]
        if body:
            cmd.append(body)
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            pass

    def _load_model(self) -> None:
        try:
            self.transcriber.load_model()
            self._set_state(State.IDLE)
            self._notify("Transcriptor", "Modelo cargado. Pulsa F12 para grabar.")
        except Exception as e:
            print(f"[app] Error loading model: {e}")
            self._notify("Transcriptor - Error", f"No se pudo cargar el modelo: {e}")

    def _on_hotkey(self) -> None:
        with self._lock:
            if self._state == State.IDLE:
                self._start_recording()
            elif self._state == State.RECORDING:
                self._stop_and_transcribe()
            elif self._state == State.PROCESSING:
                self._notify("Transcriptor", "Procesando... espera un momento.")
            elif self._state == State.LOADING:
                self._notify("Transcriptor", "Cargando modelo... espera un momento.")

    def _start_recording(self) -> None:
        try:
            self.audio.start_recording()
            self._set_state(State.RECORDING)
            self._notify("Grabando", "Pulsa F12 para detener.")
        except Exception as e:
            print(f"[app] Error starting recording: {e}")
            self._notify("Error", f"No se pudo iniciar la grabación: {e}")

    def _stop_and_transcribe(self) -> None:
        audio_data = self.audio.stop_recording()
        if audio_data is None or len(audio_data) == 0:
            self._notify("Transcriptor", "No se grabó audio.")
            self._set_state(State.IDLE)
            return
        # Ignore audio shorter than 0.5s to avoid Whisper hallucinations
        min_samples = int(SAMPLE_RATE * 0.5)
        if len(audio_data) < min_samples:
            self._notify("Transcriptor", "Audio demasiado corto.")
            self._set_state(State.IDLE)
            return
        self._set_state(State.PROCESSING)
        self._executor.submit(self._transcribe_worker, audio_data)

    def _transcribe_worker(self, audio_data) -> None:
        try:
            text = self.transcriber.transcribe(audio_data, language=self.config["language"])
            if not text:
                self._notify("Transcriptor", "No se detectó voz.")
                self._set_state(State.IDLE)
                return

            print(f"[app] Transcribed: {text}")

            if self.config.get("auto_paste", True):
                inject_text(text)

            self._notify("Transcripción", text[:200])
        except Exception as e:
            print(f"[app] Transcription error: {e}")
            self._notify("Error de transcripción", str(e))
        finally:
            self._set_state(State.IDLE)

    def _on_settings(self) -> None:
        """Open the settings dialog (called from tray menu)."""
        # Import here to avoid GTK init issues in non-main threads
        from transcriptor.settings_dialog import show_settings_dialog
        show_settings_dialog(self.config, self._apply_settings)

    def _apply_settings(self, new_config: dict) -> None:
        """Apply new settings from the dialog."""
        old_model = self.config["model_size"]
        old_hotkey = self.config["hotkey"]

        self.config = new_config
        save_config(new_config)

        # Reload model if changed
        if new_config["model_size"] != old_model:
            self._set_state(State.LOADING)
            self._executor.submit(self._reload_model, new_config["model_size"])

        # Update hotkey if changed
        if new_config["hotkey"] != old_hotkey:
            self.hotkey.update_key(new_config["hotkey"])

    def _reload_model(self, model_size: str) -> None:
        try:
            self._notify("Transcriptor", f"Cambiando a modelo '{model_size}'...")
            self.transcriber.change_model(model_size)
            self._set_state(State.IDLE)
            self._notify("Transcriptor", f"Modelo '{model_size}' cargado.")
        except Exception as e:
            print(f"[app] Error reloading model: {e}")
            self._notify("Error", f"No se pudo cambiar el modelo: {e}")

    def _on_quit(self) -> None:
        """Clean shutdown."""
        print("[app] Shutting down...")
        self.hotkey.stop()
        if self.audio.is_recording:
            self.audio.stop_recording()
        self._executor.shutdown(wait=False)
        self.tray.stop()

    def run(self) -> None:
        """Start the app. Blocks on tray icon loop."""
        self.hotkey.start()
        print("[app] Transcriptor running. Press F12 to record.")
        self.tray.run()  # blocks
