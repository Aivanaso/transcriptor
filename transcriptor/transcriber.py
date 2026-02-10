"""Speech-to-text transcription using faster-whisper."""

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    """Wraps faster-whisper for speech transcription."""

    def __init__(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8"):
        self._model: WhisperModel | None = None
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> None:
        """Download (if needed) and load the Whisper model. This is slow (~5-10s)."""
        print(f"[transcriber] Loading model '{self._model_size}' on {self._device} ({self._compute_type})...")
        self._model = WhisperModel(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        print("[transcriber] Model loaded. Warming up VAD...")
        self._warmup_vad()
        print("[transcriber] VAD ready.")

    def _warmup_vad(self) -> None:
        """Run a dummy transcription with silence to initialize Silero VAD."""
        silence = np.zeros(16000, dtype=np.float32)
        # transcribe() returns a generator — must consume it to trigger VAD init
        segments, _ = self._model.transcribe(
            silence,
            language="es",
            vad_filter=True,
            vad_parameters={"threshold": 0.3, "min_speech_duration_ms": 100},
        )
        list(segments)

    def transcribe(self, audio_data: np.ndarray, language: str = "es") -> str:
        """Transcribe a float32 numpy array and return the text."""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        segments, info = self._model.transcribe(
            audio_data,
            language=language,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.3,
                "min_speech_duration_ms": 100,
            },
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()

    def change_model(self, model_size: str) -> None:
        """Unload current model and load a new one."""
        self._model = None
        self._model_size = model_size
        self.load_model()
