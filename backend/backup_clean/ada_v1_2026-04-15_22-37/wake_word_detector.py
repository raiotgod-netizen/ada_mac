"""
Wake Word Detector using openwakeword.
Runs in a background thread, listens continuously to microphone.
When wake word is detected, fires a callback.
"""
import threading
import numpy as np
import pyaudio
import queue
from openwakeword.model import Model
import time


class WakeWordDetector:
    def __init__(self, wake_words=None, callback=None, audio_device_index=None):
        """
        wake_words: list of wake word models to use (e.g. ['hey_ada', 'hey_nabu'])
                    If None, uses 'hey_ada' by default.
        callback: function to call when wake word is detected
        audio_device_index: mic device index (None = default)
        """
        self.wake_words = wake_words or ["hey_ada"]
        self.callback = callback
        self.audio_device_index = audio_device_index

        self._running = False
        self._thread = None
        self._pyaudio = None
        self._audio_stream = None
        self._model = None

        # For VAD-free continuous listening
        self._chunk_size = 1280  # ~80ms at 16kHz
        self._sample_rate = 16000
        self._silence_threshold = 500  # RMS threshold for silence detection
        self._silence_frames = 0
        self._silence_frames_to_reset = 20  # ~1.6s of silence before新一轮 listening

        # Frame buffer for openwakeword (needs 1.28s of audio = 20480 samples)
        self._oww_buffer = np.array([], dtype=np.int16)
        self._oww_buffer_size = 20480  # 1.28s at 16kHz

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[WAKE WORD] Detector started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        print("[WAKE WORD] Detector stopped.")

    def _init_audio(self):
        self._pyaudio = pyaudio.PyAudio()
        self._audio_stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._sample_rate,
            input=True,
            input_device_index=self.audio_device_index,
            frames_per_buffer=self._chunk_size,
            start=False
        )

    def _init_model(self):
        self._model = Model(
            wakeword_models=self.wake_words,
            inference_framework="onnx"
        )
        print(f"[WAKE WORD] Models loaded: {self.wake_words}")

    def _run(self):
        self._init_audio()
        self._init_model()
        self._audio_stream.start_stream()

        print("[WAKE WORD] Listening...")
        try:
            while self._running:
                try:
                    data = self._audio_stream.read(self._chunk_size, exception_on_overflow=False)
                except Exception as e:
                    print(f"[WAKE WORD] Audio read error: {e}")
                    break

                audio_np = np.frombuffer(data, dtype=np.int16)

                # VAD: check if there's actual audio (not silence)
                rms = np.sqrt(np.mean(audio_np.astype(np.float32) ** 2))
                is_speech = rms > 30  # Adjustable threshold

                # Add to buffer
                self._oww_buffer = np.concatenate([self._oww_buffer, audio_np])
                if len(self._oww_buffer) > self._oww_buffer_size:
                    self._oww_buffer = self._oww_buffer[-self._oww_buffer_size:]

                # Run inference when buffer is full enough
                if len(self._oww_buffer) >= self._oww_buffer_size // 2:
                    scores = self._model.predict(
                        audio=np.concatenate([self._oww_buffer, np.zeros(max(0, self._oww_buffer_size - len(self._oww_buffer)), dtype=np.int16)])[:self._oww_buffer_size]
                    )
                    for ww, score in scores.items():
                        if score > 0.5:  # Confidence threshold
                            print(f"[WAKE WORD] Detected: {ww} (score: {score:.3f})")
                            if self.callback:
                                self.callback(ww, score)
                            # Reset buffer to avoid repeated detections
                            self._oww_buffer = np.array([], dtype=np.int16)

                # Reset logic
                if is_speech:
                    self._silence_frames = 0
                else:
                    self._silence_frames += 1

        except Exception as e:
            print(f"[WAKE WORD] Error: {e}")
        finally:
            self._cleanup()

    def _cleanup(self):
        if self._audio_stream:
            self._audio_stream.stop_stream()
            self._audio_stream.close()
        if self._pyaudio:
            self._pyaudio.terminate()
        print("[WAKE WORD] Audio stream closed.")

    def set_callback(self, callback):
        self.callback = callback


if __name__ == "__main__":
    import sys

    def on_wake_word(wake_word, score):
        print(f"\n>>> WAKE WORD DETECTED: {wake_word} (score: {score:.3f}) <<<\n")

    detector = WakeWordDetector(
        wake_words=["hey_ada"],
        callback=on_wake_word
    )
    detector.start()

    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        detector.stop()
        sys.exit(0)
