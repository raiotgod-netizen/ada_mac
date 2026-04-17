"""
EchoSuppressor — Detects and suppresses ADA's own voice from microphone input.
Uses energy correlation between speaker output and mic input.
"""
import asyncio
import math
import struct
import threading
import numpy as np
from collections import deque


class EchoSuppressor:
    """
    Detects when ADA's own voice is being picked up by the microphone
    (acoustic echo) and suppresses it.

    How it works:
    1. We capture a fingerprint of what ADA is currently saying (output audio)
    2. When mic input arrives, we compare its energy fingerprint against recent output
    3. If they correlate strongly → it's echo → apply attenuation
    4. Suppression decays with time distance from last output
    """

    def __init__(self, sample_rate: int = 24000, history_seconds: float = 3.0):
        self.sample_rate = sample_rate
        self.history_size = int(sample_rate * history_seconds)  # ~72000 samples for 3s

        # Circular buffer of recent output audio (as numpy arrays)
        self._output_buffer = deque(maxlen=self.history_size)
        self._output_energy = deque(maxlen=100)  # Rolling energy average per chunk

        # Suppression state
        self._suppression_active = False
        self._suppression_level = 0.0  # 0.0 = no suppression, 1.0 = full suppress
        self._last_output_time = 0

        # Thresholds
        self._echo_threshold = 0.35   # Correlation above this = echo
        self._output_threshold_rms = 500  # Min output energy to consider "speaking"
        self._suppression_max = 0.85  # Max attenuation (don't kill real speech)
        self._decay_rate = 0.15       # Suppression decay per second

        self._lock = threading.Lock()
        self._output_chunks_since_last_check = 0

    def _rms(self, data: bytes) -> float:
        """Compute RMS energy of 16-bit PCM audio."""
        count = len(data) // 2
        if count == 0:
            return 0.0
        try:
            shorts = np.frombuffer(data[:count * 2], dtype=np.int16, count=count)
            if len(shorts) == 0:
                return 0.0
            return math.sqrt(np.mean(shorts.astype(np.float32) ** 2))
        except Exception:
            return 0.0

    def _energy_signature(self, data: bytes, chunk_size: int = 480) -> np.ndarray:
        """
        Create a downsampled energy signature of audio.
        Returns an array of RMS energies per chunk — a "fingerprint" of the audio.
        """
        count = len(data) // 2
        if count == 0:
            return np.array([], dtype=np.float32)
        try:
            shorts = np.frombuffer(data[:count * 2], dtype=np.int16, count=count)
            n_chunks = count // chunk_size
            if n_chunks == 0:
                return np.array([self._rms(data)], dtype=np.float32)
            chunks = shorts[:n_chunks * chunk_size].reshape(n_chunks, chunk_size)
            energies = np.sqrt(np.mean(chunks.astype(np.float32) ** 2, axis=1))
            return energies
        except Exception:
            return np.array([], dtype=np.float32)

    def _correlation(self, sig1: np.ndarray, sig2: np.ndarray) -> float:
        """Normalized correlation between two energy signatures. Returns 0-1."""
        if len(sig1) < 2 or len(sig2) < 2:
            return 0.0
        try:
            # Downsample to same length
            min_len = min(len(sig1), len(sig2), 50)
            s1 = sig1[:min_len].astype(np.float32)
            s2 = sig2[:min_len].astype(np.float32)
            # Normalize
            s1 = (s1 - np.mean(s1)) / (np.std(s1) + 1e-8)
            s2 = (s2 - np.mean(s2)) / (np.std(s2) + 1e-8)
            corr = np.correlate(s1, s2, mode='valid')
            # Normalize by length
            return float(np.clip(corr[0] / min_len, 0.0, 1.0))
        except Exception:
            return 0.0

    def feed_output(self, audio_data: bytes):
        """
        Feed audio that ADA is currently speaking (going to speaker).
        Call this when audio is sent to the user.
        """
        if not audio_data or len(audio_data) < 480:
            return
        rms = self._rms(audio_data)
        with self._lock:
            # Add to output buffer
            self._output_buffer.append((audio_data, rms))
            self._output_energy.append(rms)
            self._output_chunks_since_last_check += 1

            # If output energy is significant, activate suppression tracking
            if rms > self._output_threshold_rms:
                self._suppression_active = True
                self._last_output_time = 0  # Reset decay

    def process_mic(self, mic_data: bytes) -> bytes:
        """
        Process incoming mic audio and suppress echo.
        Returns the (potentially attenuated) mic audio.
        If the data is echo, it will be attenuated toward silence.
        """
        if not mic_data or len(mic_data) < 480:
            return mic_data

        mic_rms = self._rms(mic_data)

        # If mic is near-silence, just pass through
        if mic_rms < 200:
            with self._lock:
                self._suppression_level = max(0.0, self._suppression_level - 0.1)
                if self._suppression_level < 0.05:
                    self._suppression_active = False
            return mic_data

        with self._lock:
            # Check if we have recent output to compare against
            if not self._output_buffer or len(self._output_buffer) < 2:
                return mic_data

            # Calculate current suppression level
            suppression = self._suppression_level

            # Compute echo correlation
            mic_sig = self._energy_signature(mic_data)
            best_corr = 0.0
            recent_outputs = list(self._output_buffer)[-10:]  # Last 10 chunks

            for out_data, out_rms in reversed(recent_outputs):
                if out_rms < self._output_threshold_rms:
                    continue
                out_sig = self._energy_signature(out_data)
                corr = self._correlation(mic_sig, out_sig)
                best_corr = max(best_corr, corr)
                if best_corr > self._echo_threshold:
                    break

            # Update suppression based on correlation
            if best_corr > self._echo_threshold:
                # Strong correlation = likely echo
                suppression = min(self._suppression_max, best_corr * 1.2)
                self._suppression_level = suppression
                self._suppression_active = True
            else:
                # Decay suppression
                self._suppression_level = max(0.0, suppression - self._decay_rate * 0.1)

            # Apply attenuation
            if suppression > 0.1:
                # Mix mic_data with silence based on suppression level
                # 1.0 suppression = fully silent, 0.0 = unchanged
                attenuation = 1.0 - suppression
                count = len(mic_data) // 2
                try:
                    shorts = np.frombuffer(mic_data, dtype=np.int16, count=count)
                    attenuated = (shorts.astype(np.float32) * attenuation).astype(np.int16)
                    return attenuated.tobytes()
                except Exception:
                    return mic_data

            return mic_data

    def get_status(self) -> dict:
        with self._lock:
            return {
                "suppression_active": self._suppression_active,
                "suppression_level": round(self._suppression_level, 3),
                "output_buffer_chunks": len(self._output_buffer),
                "output_energy_avg": round(np.mean(list(self._output_energy)) if self._output_energy else 0, 1)
            }
