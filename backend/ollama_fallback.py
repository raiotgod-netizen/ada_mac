"""
Ollama Fallback — LLM local para cuando Gemini no está disponible.
No toca audio, voz, ni el pipeline de audio de ADA.
Solo activa cuando todos los retries de Gemini fallan.
"""

import os
import asyncio
from pathlib import Path

class OllamaFallback:
    """Fallback a LLM local via Ollama cuando Gemini se cae."""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        self._personality = self._load_personality()

    def _load_personality(self) -> str:
        p = Path(__file__).parent / "jarvis_personality.txt"
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
        return "You are ADA, a voice assistant. Be concise and helpful."

    async def chat(self, prompt: str, history: list | None = None) -> str:
        """Envía prompt a Ollama y retorna la respuesta."""
        try:
            import httpx
            messages = [{"role": "system", "content": self._personality}]
            if history:
                for h in history[-10:]:  # últimos 10 mensajes
                    role = "user" if h.get("sender") == "User" else "assistant"
                    messages.append({"role": role, "content": h.get("text", "")})
            messages.append({"role": "user", "content": prompt})

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json={"model": self.model, "messages": messages, "stream": False}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("message", {}).get("content", "No pude generar respuesta.")
                else:
                    return f"[Ollama error {resp.status_code}]"

        except Exception as e:
            return f"[Ollama unreachable: {e}]"

    async def tools_available(self) -> bool:
        """Ollama no tiene tools.function calling en este modelo. Retorna False."""
        return False

    def snapshot(self) -> dict:
        return {
            "available": True,
            "model": self.model,
            "url": self.base_url,
            "mode": "text_only_fallback",
            "note": "Audio/voice no disponible en fallback — solo texto"
        }


_instance = None

def get_fallback() -> OllamaFallback:
    global _instance
    if _instance is None:
        _instance = OllamaFallback()
    return _instance