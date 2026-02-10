"""Audio recording using sounddevice with PipeWire compatibility."""

import logging

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

TARGET_RATE = 16000
CANDIDATE_RATES = [16000, 48000, 44100]
CHANNELS = 1
DTYPE = "float32"


def get_input_devices() -> list[dict]:
    """Return a list of available input devices.

    Each dict contains: index, name, max_input_channels, default_samplerate.
    """
    devices = sd.query_devices()
    result = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            result.append({
                "index": i,
                "name": dev["name"],
                "max_input_channels": dev["max_input_channels"],
                "default_samplerate": dev["default_samplerate"],
            })
    return result


class AudioRecorder:
    """Records audio from an input device with automatic sample rate negotiation."""

    def __init__(self, device: int | str | None = None):
        self._device = device
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._capture_rate: int = TARGET_RATE

    @property
    def is_recording(self) -> bool:
        return self._recording

    def set_device(self, device: int | str | None) -> None:
        """Change the input device. Takes effect on the next recording."""
        if self._recording:
            logger.warning("Changing device while recording — will apply on next recording")
        self._device = device

    def _negotiate_sample_rate(self) -> int:
        """Find a working sample rate for the current device.

        Tries CANDIDATE_RATES in order (16kHz first for zero-overhead).
        Returns the first rate that works, or raises RuntimeError.
        """
        for rate in CANDIDATE_RATES:
            try:
                test_stream = sd.InputStream(
                    samplerate=rate,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    device=self._device,
                )
                test_stream.close()
                logger.info("Using capture rate: %d Hz (device=%s)", rate, self._device)
                return rate
            except sd.PortAudioError:
                logger.debug("Rate %d Hz not supported by device %s", rate, self._device)
                continue
        raise RuntimeError(
            f"No supported sample rate found for device {self._device}. "
            f"Tried: {CANDIDATE_RATES}"
        )

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)
        self._chunks.append(indata.copy())

    def start_recording(self) -> None:
        """Open an input stream and start recording."""
        if self._recording:
            return
        self._chunks = []
        self._capture_rate = self._negotiate_sample_rate()
        self._stream = sd.InputStream(
            samplerate=self._capture_rate,
            channels=CHANNELS,
            dtype=DTYPE,
            device=self._device,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._recording = True

    def stop_recording(self) -> np.ndarray | None:
        """Stop recording and return audio as a 1-D float32 array at TARGET_RATE."""
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

        if self._capture_rate != TARGET_RATE:
            audio = self._resample(audio, self._capture_rate, TARGET_RATE)

        return audio

    @staticmethod
    def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio from from_rate to to_rate using scipy."""
        from scipy.signal import resample

        num_samples = int(len(audio) * to_rate / from_rate)
        logger.info("Resampling: %d Hz → %d Hz (%d → %d samples)", from_rate, to_rate, len(audio), num_samples)
        resampled = resample(audio, num_samples).astype(np.float32)

        # Normalize to [-1, 1] to avoid clipping
        max_val = np.max(np.abs(resampled))
        if max_val > 0:
            resampled = resampled / max_val

        return resampled
