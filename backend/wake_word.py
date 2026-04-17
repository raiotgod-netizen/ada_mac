"""
Wake Word — Simple wake word detection using microphone audio energy threshold.
Uses a simple energy-based trigger rather than a full wake word model.
"""
from __future__ import annotations

import asyncio
import audioop
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WakeWordDetector:
    """
    Energy-based wake word trigger.
    Monitors microphone energy and fires when energy exceeds threshold
    after a period of silence (to avoid false triggers from speech).
    """

    def __init__(
        self,
        energy_threshold: int = 4000,
        silence_frames: int = 25,
        active_frames: int = 2,
        sample_rate: int = 16000,
    ):
        self.energy_threshold = energy_threshold
        self.silence_frames = silence_frames
        self.active_frames = active_frames
        self.sample_rate = sample_rate

        self._running = False
        self._thread: threading.Thread | None = None
        self._callback: Callable[[], None] | None = None
        self._energy_history: deque = deque(maxlen=50)
        self._last_trigger: float = 0.0
        self._cooldown_sec: float = 5.0

    def set_callback(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def start(self, mic_index: int = 0) -> bool:
        if self._running:
            return True
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(mic_index,), daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def _monitor_loop(self, mic_index: int) -> None:
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=1024,
            )

            silence_count = 0
            active_count = 0

            while self._running:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                except Exception:
                    continue

                try:
                    energy = audioop.rms(data, 2)
                except Exception:
                    energy = 0

                self._energy_history.append(energy)

                if energy > self.energy_threshold:
                    active_count += 1
                    silence_count = 0
                    if active_count >= self.active_frames:
                        now = datetime.now(timezone.utc).timestamp()
                        if now - self._last_trigger > self._cooldown_sec:
                            self._last_trigger = now
                            if self._callback:
                                try:
                                    loop = asyncio.new_event_loop()
                                    loop.run_until_complete(asyncio.to_thread(self._callback))
                                    loop.close()
                                except Exception:
                                    pass
                        active_count = 0
                else:
                    active_count = 0
                    silence_count += 1

            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as e:
            print(f"[WakeWordDetector] Error: {e}")
            self._running = False

    def snapshot(self) -> dict:
        avg_energy = sum(self._energy_history) / len(self._energy_history) if self._energy_history else 0
        return {
            "running": self._running,
            "energy_threshold": self.energy_threshold,
            "avg_energy": round(avg_energy, 1),
            "last_triggered": self._last_trigger,
        }