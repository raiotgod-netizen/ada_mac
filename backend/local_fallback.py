"""
Local Fallback — Routes commands locally when cloud is unavailable.
Provides basic intent parsing and local TTS without external API calls.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


LOCAL_COMMANDS = {
    # (keywords -> intent)
    ("abre", "abrir", "open"): "open_app",
    ("cierra", "cerrar", "close"): "close_app",
    ("enciende", "apaga", "turn on", "turn off"): "smart_home",
    ("meteoro", "clima", "weather"): "weather",
    ("hora", "time", "qué hora"): "time",
    ("volumen", "volume"): "volume",
    ("nota", "note", "recordatorio"): "reminder",
    ("busca", "search", "google"): "web_search",
    ("reinicia", "restart"): "system_control",
    ("apagar", "shutdown"): "system_control",
}


class LocalFallbackRouter:
    """
    Simple local command parser. Matches input against known patterns
    and returns a routing decision without cloud dependency.
    """

    def __init__(self):
        self._last_fallback = None

    def parse(self, text: str) -> Dict[str, Any]:
        t = (text or "").strip().lower()

        # Basic intent detection
        for keywords, intent in LOCAL_COMMANDS:
            if any(kw in t for kw in keywords):
                return {
                    "intent": intent,
                    "route": "local",
                    "confidence": 0.7,
                    "tools": [],
                    "fallback": True,
                    "original_text": text,
                }

        # No match — return conversation as fallback
        return {
            "intent": "conversation",
            "route": "cloud_required",
            "confidence": 0.0,
            "tools": [],
            "fallback": True,
            "original_text": text,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "available": True,
            "last_fallback": self._last_fallback,
            "local_commands_count": sum(len(k) for k in LOCAL_COMMANDS),
        }


class LocalTTS:
    """
    Use Windows SAPI (pyttsx3) or PowerShell for local TTS.
    Falls back to silent operation if no voice is available.
    """

    def __init__(self):
        self._engine = None
        self._init_pyttsx3()

    def _init_pyttsx3(self) -> None:
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty('voices')
            if voices:
                self._engine.setProperty('voice', voices[0].id)
                self._engine.setProperty('rate', 155)
            print("[LocalTTS] pyttsx3 initialized OK")
        except Exception as e:
            print(f"[LocalTTS] pyttsx3 init failed: {e}")
            self._engine = None

    def speak(self, text: str) -> bool:
        if not text:
            return False
        if self._engine:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
                return True
            except Exception as e:
                print(f"[LocalTTS] speak error: {e}")
                return False
        # Fallback: PowerShell System.Speech
        return self._speak_powershell(text)

    def _speak_powershell(self, text: str) -> bool:
        try:
            escaped = text.replace('"', "'").replace('\n', ' ').replace('\r', '')
            script = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{escaped}")'
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                timeout=15,
            )
            return result.returncode == 0
        except Exception:
            return False

    def list_voices(self) -> List[str]:
        if self._engine:
            try:
                return [v.name for v in self._engine.getProperty('voices')]
            except Exception:
                pass
        return []


class LocalSTT:
    """
    Local speech-to-text using Windows native recognition.
    Simplified version — full implementation would use edge-tts or vosk.
    """

    def __init__(self):
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        # Check for Whisper or other local STT binaries
        possible_paths = [
            os.environ.get("WHISPER_PATH", ""),
            str(Path(__file__).parent.parent / "whisper.exe"),
            "whisper",
        ]
        for p in possible_paths:
            if p and Path(p).exists():
                return True
        # Check for edge-tts (pip package)
        try:
            subprocess.run(["edge-tts", "--version"], capture_output=True, timeout=5)
            return True
        except Exception:
            pass
        return False

    def is_available(self) -> bool:
        return self._available

    def snapshot(self) -> Dict[str, Any]:
        return {
            "available": self._available,
            "engine": "edge-tts" if self._available else None,
            "note": "Local STT requires edge-tts pip package" if not self._available else "",
        }