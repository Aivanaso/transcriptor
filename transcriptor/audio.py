"""Audio recording using sounddevice."""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"


class AudioRecorder:
    """Records audio from the default input device."""

    def __init__(self):
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            print(f"[audio] {status}")
        self._chunks.append(indata.copy())

    def start_recording(self) -> None:
        """Open an input stream and start recording."""
        if self._recording:
            return
        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._recording = True

    def stop_recording(self) -> np.ndarray | None:
        """Stop recording and return the audio as a 1-D float32 numpy array."""
        if not self._recording or self._stream is None:
            return None
        self._stream.stop()
        self._stream.close()
        self._stream = None
        self._recording = False

        if not self._chunks:
            return None
        audio = np.concatenate(self._chunks, axis=0).flatten()
        self._chunks = []
        return audio
