"""Real-time binaural / isochronic tone synthesis. No GUI imports here."""
from __future__ import annotations

import threading

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 44_100
FADE_SECONDS = 0.050          # play/stop and mode-switch envelope
PULSE_EDGE_SECONDS = 0.007    # micro-fade on isochronic pulse edges
HEADROOM = 0.8                # peak amplitude at 100% volume

BINAURAL = "binaural"
ISOCHRONIC = "isochronic"


def _smooth(x: np.ndarray) -> np.ndarray:
    """Raised-cosine ramp 0..1 over x in [0, 1]."""
    return 0.5 - 0.5 * np.cos(np.pi * np.clip(x, 0.0, 1.0))


class ToneGenerator:
    """Generates tones iteratively inside a sounddevice callback.

    Phase accumulators carry across blocks, so output is seamless forever and
    parameter changes never cause phase discontinuities. All setters are safe
    to call from the GUI thread.
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._lock = threading.Lock()
        self._stream: sd.OutputStream | None = None

        # Parameters (written by GUI thread, read by audio thread).
        self._desired_mode = BINAURAL
        self._base = 200.0
        self._beat = 10.0
        self._volume = 0.5
        self._playing = False

        # Audio-thread state.
        self._active_mode = BINAURAL
        self._env = 0.0
        self._vol_smoothed = self._volume
        self._ph_left = 0.0
        self._ph_right = 0.0
        self._ph_carrier = 0.0
        self._ph_pulse = 0.0

    # ------------------------------------------------------------ parameters
    def set_mode(self, mode: str) -> None:
        self._desired_mode = mode

    def set_base_frequency(self, hz: float) -> None:
        self._base = float(hz)

    def set_beat_frequency(self, hz: float) -> None:
        self._beat = float(hz)

    def set_volume(self, volume: float) -> None:
        self._volume = min(max(float(volume), 0.0), 1.0)

    @property
    def playing(self) -> bool:
        return self._playing

    # --------------------------------------------------------------- control
    def start(self) -> None:
        with self._lock:
            if self._stream is None:
                self._stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=2,
                    dtype="float32",
                    callback=self._callback,
                    latency="low",
                )
                self._stream.start()
            self._playing = True

    def stop(self) -> None:
        """Begin the fade-out. Call close_if_idle() shortly afterwards."""
        self._playing = False

    def close_if_idle(self) -> None:
        with self._lock:
            if self._playing or self._stream is None:
                return
            self._close_stream()

    def shutdown(self) -> None:
        with self._lock:
            self._playing = False
            self._close_stream()

    def _close_stream(self) -> None:
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except sd.PortAudioError:
                pass
        self._env = 0.0

    # ------------------------------------------------------------------- DSP
    def _callback(self, outdata, frames, time_info, status) -> None:
        sr = self.sample_rate
        n = frames

        # Mode switches happen only while silent (after fading out).
        if self._env <= 0.0 and self._active_mode != self._desired_mode:
            self._active_mode = self._desired_mode

        target = 1.0 if (self._playing and self._active_mode == self._desired_mode) else 0.0
        step = 1.0 / (FADE_SECONDS * sr)
        idx = np.arange(1, n + 1)
        if target >= 1.0:
            env = np.minimum(self._env + step * idx, 1.0)
        else:
            env = np.maximum(self._env - step * idx, 0.0)
        self._env = float(env[-1])

        # Volume ramps linearly across the block to avoid zipper noise.
        vol = np.linspace(self._vol_smoothed, self._volume, n, endpoint=False)
        self._vol_smoothed = self._volume
        gain = (env * vol * HEADROOM).astype(np.float64)

        base, beat = self._base, self._beat
        t = np.arange(n)

        if self._active_mode == BINAURAL:
            ph_l = self._ph_left + (base / sr) * t
            ph_r = self._ph_right + ((base + beat) / sr) * t
            self._ph_left = (self._ph_left + base / sr * n) % 1.0
            self._ph_right = (self._ph_right + (base + beat) / sr * n) % 1.0
            left = np.sin(2 * np.pi * ph_l)
            right = np.sin(2 * np.pi * ph_r)
        else:
            ph_c = self._ph_carrier + (base / sr) * t
            ph_p = self._ph_pulse + (beat / sr) * t
            self._ph_carrier = (self._ph_carrier + base / sr * n) % 1.0
            self._ph_pulse = (self._ph_pulse + beat / sr * n) % 1.0
            carrier = np.sin(2 * np.pi * ph_c)
            left = right = carrier * self._pulse_gate(ph_p % 1.0, beat)

        outdata[:, 0] = left * gain
        outdata[:, 1] = right * gain

    @staticmethod
    def _pulse_gate(phase: np.ndarray, pulse_hz: float) -> np.ndarray:
        """50% duty square gate with raised-cosine edges (phase in cycles)."""
        edge = min(PULSE_EDGE_SECONDS * pulse_hz, 0.25)  # edge width in cycles
        return _smooth(phase / edge) - _smooth((phase - 0.5) / edge)
