"""Audio recording using sounddevice with PipeWire compatibility."""

import contextlib
import logging
import os
import time

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

TARGET_RATE = 16000
CANDIDATE_RATES = [16000, 48000, 44100, 32000, 22050, 8000, 96000]
CHANNELS = 1
DTYPE = "float32"


@contextlib.contextmanager
def _suppress_stderr():
    """Redirect fd 2 to /dev/null to silence PortAudio C-level error messages."""
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    old_stderr_fd = os.dup(2)
    try:
        os.dup2(devnull_fd, 2)
        yield
    finally:
        os.dup2(old_stderr_fd, 2)
        os.close(devnull_fd)
        os.close(old_stderr_fd)


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
        self._device = device if device is not None else "pulse"
        self._original_device = self._device
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._recording = False
        self._capture_rate: int = TARGET_RATE
        self._fallback_used = False
        self._cached_rate: int | None = None
        self._cached_device: int | str | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def fallback_used(self) -> bool:
        """True if the last recording fell back to a different device."""
        return self._fallback_used

    def set_device(self, device: int | str | None) -> None:
        """Change the input device. Takes effect on the next recording."""
        if self._recording:
            logger.warning("Changing device while recording — will apply on next recording")
        self._device = device if device is not None else "pulse"
        self._original_device = self._device
        self._cached_rate = None
        self._cached_device = None

    def _negotiate_sample_rate(self) -> int:
        """Find a working sample rate for the current device.

        Tries the device's default_samplerate first, then CANDIDATE_RATES.
        Returns the first rate that works, or raises RuntimeError.
        """
        rates = list(CANDIDATE_RATES)

        try:
            dev_info = sd.query_devices(self._device)
            dev_default = int(dev_info["default_samplerate"])
            if dev_default in rates:
                rates.remove(dev_default)
            rates.insert(0, dev_default)
        except Exception:
            pass

        for rate in rates:
            if self._try_sample_rate(rate):
                return rate

        raise RuntimeError(
            f"No supported sample rate found for device {self._device}. "
            f"Tried: {rates}"
        )

    def _try_sample_rate(self, rate: int) -> bool:
        """Test if a sample rate works for the current device, suppressing stderr."""
        with _suppress_stderr():
            try:
                stream = sd.InputStream(
                    samplerate=rate,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    device=self._device,
                )
                stream.close()
                logger.info("Using capture rate: %d Hz (device=%s)", rate, self._device)
                return True
            except sd.PortAudioError:
                logger.debug("Rate %d Hz not supported by device %s", rate, self._device)
                return False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        if status:
            logger.warning("Audio callback status: %s", status)
        self._chunks.append(indata.copy())

    def start_recording(self) -> None:
        """Open an input stream and start recording.

        If the configured device fails completely, falls back to "pulse"
        and then to the system default.
        """
        if self._recording:
            return
        self._chunks = []
        self._fallback_used = False
        self._device = self._original_device

        try:
            if self._cached_rate is not None and self._device == self._cached_device:
                self._capture_rate = self._cached_rate
            else:
                self._capture_rate = self._negotiate_sample_rate()
                self._cached_rate = self._capture_rate
                self._cached_device = self._device
        except RuntimeError:
            if self._device is not None:
                logger.warning("Device %s failed, trying fallback devices", self._device)
                for fallback in ("pulse", None):
                    try:
                        self._device = fallback
                        self._capture_rate = self._negotiate_sample_rate()
                        self._fallback_used = True
                        break
                    except RuntimeError:
                        continue
                else:
                    raise RuntimeError("No working audio input device found")
            else:
                raise

        self._open_stream()
        self._recording = True
        logger.info(
            "Recording started: device=%s, rate=%d Hz",
            self._device, self._capture_rate,
        )

    def _open_stream(self) -> None:
        """Open and start the audio stream, with one retry on failure."""
        for attempt in range(2):
            try:
                self._stream = sd.InputStream(
                    samplerate=self._capture_rate,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    device=self._device,
                    callback=self._audio_callback,
                )
                self._stream.start()
                return
            except sd.PortAudioError as e:
                if attempt == 0:
                    logger.warning("Stream open failed, retrying in 200ms: %s", e)
                    time.sleep(0.2)
                else:
                    raise

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

        # Trim initial ~100ms to discard PipeWire stream-open clicks
        trim_samples = int(self._capture_rate * 0.1)
        if len(audio) > trim_samples:
            audio = audio[trim_samples:]

        if self._capture_rate != TARGET_RATE:
            audio = self._resample(audio, self._capture_rate, TARGET_RATE)

        # Normalize to [-1, 1] — Whisper expects float32 in this range.
        # Safe after trim (no PipeWire click inflating the peak).
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val

        return audio

    @staticmethod
    def _resample(audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio using polyphase filter (better for non-integer ratios)."""
        from math import gcd

        from scipy.signal import resample_poly

        ratio_gcd = gcd(from_rate, to_rate)
        up = to_rate // ratio_gcd
        down = from_rate // ratio_gcd
        logger.info("Resampling: %d Hz → %d Hz (up=%d, down=%d)", from_rate, to_rate, up, down)
        return resample_poly(audio, up, down).astype(np.float32)
