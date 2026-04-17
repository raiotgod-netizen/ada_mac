"""
EchoSuppressor v2 — Improved ADA Echo Cancellation
================================================
Acoustic Echo Suppression (AES) + Adaptive Filtering for ADA.

Improvements over v1:
1. LMS adaptive filter (efficient, real-time safe)
2. Zero numpy — pure struct/math only
3. Adaptive threshold calibration on startup
4. Double-talk detection — don't cancel user speech
5. Two-stage: LMS cancellation + energy suppression
6. Proper 16kHz support (v1 defaulted to 24kHz — BUG FIXED)

Algorithm:
  1. Maintain circular buffer of recent speaker output (reference)
  2. For each mic sample: e = mic - w · ref  (error = mic minus echo estimate)
  3. LMS update: w += μ * e * ref / ||ref||²
  4. If e ≈ mic (echo was strong), suppress
  5. Double-talk: if mic >> ref, don't update (user is speaking)
"""

import math
import random
import struct
import threading
from collections import deque


class EchoSuppressor:
    """
    Two-stage echo suppressor:
      Stage 1 — LMS Adaptive Echo Cancellation
      Stage 2 — Energy-based spectral attenuation
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        filter_taps: int = 64,        # LMS filter length (power of 2)
        mu: float = 0.15,              # LMS step size (0-1)
        suppression_max: float = 0.80,
    ):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.filter_taps = filter_taps
        self.mu = mu
        self.suppression_max = suppression_max

        # ── LMS Filter ─────────────────────────────────────────
        # Circular buffer: holds last filter_taps speaker samples
        self._ref_buf = [0.0] * filter_taps
        self._ref_idx = 0  # newest sample at this position

        # Filter coefficients (what LMS adapts)
        self._w = [random.uniform(-5e-3, 5e-3) for _ in range(filter_taps)]

        # ── Suppression state ──────────────────────────────────
        self._suppression_persistent = 0.0   # leaky integrator
        self._suppression_decay = 0.04      # per-chunk decay

        # ── Calibration ────────────────────────────────────────
        self._calibrated = False
        self._noise_floor = 200.0          # measured on startup
        self._cal_chunks = 0
        self._max_cal = 30                  # ~2s at 64ms/chunk

        # ── Double-talk ────────────────────────────────────────
        self._mic_history = deque(maxlen=8)
        self._ref_history = deque(maxlen=8)

        # ── Stats ──────────────────────────────────────────────
        self._lock = threading.Lock()
        self._chunks = 0
        self._total_sup = 0.0

    # ── Helpers ─────────────────────────────────────────────────

    def _bytes_to_samples(self, data: bytes):
        if not data:
            return [], 0
        try:
            count = len(data) // 2
            shorts = struct.unpack(f"<{count}h", data)
            return [float(s) for s in shorts], count
        except Exception:
            return [], 0

    def _samples_to_bytes(self, samples: list) -> bytes:
        clipped = [max(-32768, min(32767, int(round(s)))) for s in samples]
        return struct.pack(f"<{len(clipped)}h", *clipped)

    def _rms(self, samples: list) -> float:
        n = len(samples)
        if n == 0:
            return 0.0
        return math.sqrt(sum(s * s for s in samples) / n)

    def _get_ref(self, n: int) -> list:
        """Get n most recent ref samples, oldest first."""
        if n > self.filter_taps:
            n = self.filter_taps
        out = []
        for i in range(n):
            idx = (self._ref_idx - i - 1) % self.filter_taps
            out.append(self._ref_buf[idx])
        out.reverse()
        return out

    def _calibrate(self, mic_rms: float):
        if self._cal_chunks < self._max_cal:
            # Exponential moving average of silence RMS
            self._noise_floor = self._noise_floor * 0.8 + mic_rms * 0.2
            self._cal_chunks += 1
            if self._cal_chunks >= self._max_cal:
                self._calibrated = True

    # ── LMS echo cancellation (sample-by-sample) ────────────────

    def _lms_sample(self, mic_sample: float, ref_sample: float) -> float:
        """
        Process one mic sample against one ref sample.
        Returns: error (echo-cancelled mic sample)
        """
        # Write ref to circular buffer
        self._ref_buf[self._ref_idx] = ref_sample
        self._ref_idx = (self._ref_idx + 1) % self.filter_taps

        # Compute echo estimate: y = Σ w[k] * x[k]
        echo_est = 0.0
        for k in range(self.filter_taps):
            idx = (self._ref_idx - 1 - k) % self.filter_taps
            echo_est += self._w[k] * self._ref_buf[idx]

        # Error = mic - echo_estimate
        error = mic_sample - echo_est

        # LMS update: w[k] += μ * error * x[k] / ||x||²
        # Compute ||x||² (ref signal power in filter buffer)
        ref_power = sum(self._ref_buf[i] * self._ref_buf[i] for i in range(self.filter_taps))
        if ref_power > 1e-6:
            mu_norm = self.mu / ref_power
            for k in range(self.filter_taps):
                idx = (self._ref_idx - 1 - k) % self.filter_taps
                self._w[k] += mu_norm * error * self._ref_buf[idx]

        return error

    # ── Public API ──────────────────────────────────────────────

    def feed_output(self, audio_data: bytes):
        """Feed ADA's output audio — the reference signal for AEC."""
        if not audio_data:
            return
        samples, _ = self._bytes_to_samples(audio_data)
        with self._lock:
            for s in samples:
                self._ref_buf[self._ref_idx] = s
                self._ref_idx = (self._ref_idx + 1) % self.filter_taps

    def process_mic(self, mic_data: bytes) -> bytes:
        """
        Process incoming mic audio: cancel ADA's echo, return cleaned audio.
        """
        if not mic_data:
            return mic_data

        mic_samples, count = self._bytes_to_samples(mic_data)
        if count == 0:
            return mic_data

        mic_rms = self._rms(mic_samples)

        # ── Calibration ─────────────────────────────────────────
        self._calibrate(mic_rms)

        # ── Near-silence: skip processing ────────────────────────
        if mic_rms < self._noise_floor * 0.7:
            with self._lock:
                self._suppression_persistent = max(0.0, self._suppression_persistent - 0.25)
            return mic_data

        # ── Double-talk: is user speaking? ───────────────────────
        self._mic_history.append(mic_rms)
        ref_rms = self._rms(self._ref_buf)
        self._ref_history.append(ref_rms)

        avg_mic = sum(self._mic_history) / max(1, len(self._mic_history))
        avg_ref = sum(self._ref_history) / max(1, len(self._ref_history))

        is_double_talk = (
            avg_ref > self._noise_floor * 1.5
            and avg_mic > avg_ref * 2.0
        )

        # ── Process each sample with LMS ───────────────────────
        # Get ref samples aligned with mic samples (ref is ~1 chunk behind)
        ref_samples = self._get_ref(count)
        error_samples = []
        update = not is_double_talk

        if update and ref_rms > self._noise_floor * 0.5:
            # Full LMS update
            for i, mic_s in enumerate(mic_samples):
                # Corresponding ref sample (oldest of the block)
                ref_s = ref_samples[i] if i < len(ref_samples) else 0.0
                err = self._lms_sample(mic_s, ref_s)
                error_samples.append(err)
        else:
            # No filter update: just subtract reference at 0 gain
            # (pass through with mild attenuation)
            for i, mic_s in enumerate(mic_samples):
                self._ref_buf[self._ref_idx] = 0.0  # clear ref while silent
                self._ref_idx = (self._ref_idx + 1) % self.filter_taps
                error_samples.append(mic_s)

        error_rms = self._rms(error_samples)

        # ── Echo detection: how much of mic is echo? ─────────────
        if mic_rms > 1.0:
            echo_ratio = max(0.0, 1.0 - error_rms / mic_rms)
        else:
            echo_ratio = 0.0

        # ── Adaptive suppression ────────────────────────────────
        user_threshold = self._noise_floor * 6

        with self._lock:
            if not is_double_talk and mic_rms < user_threshold:
                if echo_ratio > 0.30:
                    target = min(self.suppression_max, echo_ratio * 1.05)
                    self._suppression_persistent = min(
                        self.suppression_max,
                        max(self._suppression_persistent, target)
                    )
                else:
                    self._suppression_persistent = max(
                        0.0,
                        self._suppression_persistent - self._suppression_decay
                    )
            else:
                self._suppression_persistent = max(
                    0.0,
                    self._suppression_persistent - 0.12
                )

            sup = self._suppression_persistent

        # ── Apply attenuation ───────────────────────────────────
        if sup > 0.05:
            atten = 1.0 - sup
            error_samples = [s * atten for s in error_samples]

        # ── Output ──────────────────────────────────────────────
        self._chunks += 1
        self._total_sup += sup

        return self._samples_to_bytes(error_samples)

    def get_status(self) -> dict:
        """Diagnostics for debugging."""
        with self._lock:
            return {
                "chunks_processed": self._chunks,
                "calibrated": self._calibrated,
                "noise_floor": round(self._noise_floor, 1),
                "suppression": round(self._suppression_persistent, 3),
                "suppression_avg": round(
                    self._total_sup / max(1, self._chunks), 4
                ),
                "filter_avg_coef": round(
                    sum(abs(v) for v in self._w) / len(self._w), 6
                ),
                "ref_rms": round(self._rms(self._ref_buf), 1),
                "lms_taps": self.filter_taps,
                "lms_mu": self.mu,
            }
