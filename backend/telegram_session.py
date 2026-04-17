"""
TelegramSession — Text-only Groq session for Telegram bot integration.
Uses Groq Chat API (completely independent from ADA's Gemini voice/audio pipeline).
Commands that need PC access are executed via HTTP call to server.py /telegram/exec endpoint.
"""

import asyncio
import os
import httpx
from pathlib import Path
from groq import AsyncGroq

# Groq client — separate from ADA's Gemini
_groq_client = None

def _get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in .env")
        _groq_client = AsyncGroq(api_key=api_key)
    return _groq_client

# Lazy-load personality
_jarvis_personality = None

def _get_personality():
    global _jarvis_personality
    if _jarvis_personality is None:
        p = Path(__file__).parent / "jarvis_personality.txt"
        _jarvis_personality = p.read_text(encoding="utf-8").strip()
    return _jarvis_personality

# Commands that need real PC execution (not just AI chat)
TOOL_COMMANDS = {
    "spotify", "volumen", "volume", "luz", "light", "kasa",
    "leer", "read ", "escribir", "write ", "ls ", "dir ",
    "email ", "abrir", "open ", "apagar pc", "shutdown pc",
}


class TelegramSession:
    """Manages a Groq text session per Telegram user (by chat_id)."""

    def __init__(self, telegram_bot):
        self.bot = telegram_bot
        self.conversations = {}  # {chat_id: [ {"role":"user"|"assistant", "content":...}, ...]}
        self.max_history = 20
        self._responding = set()
        self.model = "llama-3.3-70b-versatile"

    def _needs_tool(self, text: str) -> bool:
        """Check if message looks like a PC control command."""
        lower = text.strip().lower()
        # Exact matches
        if lower == "spotify":
            return True
        # Prefix matches
        for cmd in TOOL_COMMANDS:
            if lower.startswith(cmd) or f" {cmd}" in lower:
                return True
        return False

    async def handle_message(self, text: str, chat_id: str):
        """Called by TelegramBot when a text message arrives."""
        if chat_id in self._responding:
            await self.bot.send_message(chat_id, "Un momento... ya estoy procesando tu mensaje anterior. 💬")
            return

        # Admin-only check
        admin_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        if admin_id and str(chat_id) != str(admin_id):
            await self.bot.send_message(
                chat_id,
                "No estás autorizado para usar este bot. Solo el administrador puede interactuar con ADA por Telegram. 🚫"
            )
            return

        stripped = text.strip().lower()

        # --- Built-in commands ---
        if stripped in ("/reset", "/reset@adadebolsillobot"):
            self.reset_conversation(chat_id)
            await self.bot.send_message(chat_id, "🔄 Conversación reiniciada.")
            return

        if stripped in ("/help", "/start", "/help@adadebolsillobot", "/start@adadebolsillobot"):
            await self.bot.send_message(
                chat_id,
                "🤖 *ADA Telegram Bot*\n\n"
                "Comandos:\n"
                "  /reset — Reinicia la conversación\n"
                "  /help — Muestra este mensaje\n\n"
                "También podés pedirme cosas como:\n"
                "  • Spotify play/pause/next/prev\n"
                "  • Volumen 0-100\n"
                "  • Encender/apagar luces\n"
                "  • Leer archivo <ruta>\n"
                "  • Escribir archivo <ruta> || <contenido>\n"
                "  • Email <to> || <asunto> || <cuerpo>\n"
                "  • Abrir <url>\n"
                "Todo lo demás se responde con IA.",
                parse_mode="Markdown"
            )
            return

        if stripped in ("/status", "/status@adadebolsillobot"):
            hist_len = len(self.conversations.get(chat_id, []))
            await self.bot.send_message(
                chat_id,
                f"✅ ADA conectada\nModelo: {self.model}\nMensajes en historial: {hist_len // 2}"
            )
            return

        # --- Tool commands: execute for real, skip Groq ---
        if self._needs_tool(text):
            await self.bot.send_message(chat_id, "⚙️ Ejecutando...")
            try:
                result = await self._exec_tool(text)
                await self.bot.send_message(chat_id, result)
            except Exception as e:
                await self.bot.send_message(chat_id, f"❌ Error: {str(e)[:200]}")
            return

        # --- Normal Groq chat ---
        self._responding.add(chat_id)
        try:
            if chat_id not in self.conversations:
                self.conversations[chat_id] = []

            history = self.conversations[chat_id]
            if len(history) > self.max_history:
                history = history[-self.max_history:]
                self.conversations[chat_id] = history

            messages = [{"role": "system", "content": _get_personality()}]
            messages.extend(history)
            messages.append({"role": "user", "content": text})

            await self.bot.send_message(chat_id, "✍️ Pensando...")
            response_text = await self._get_groq_response(messages)
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": response_text})
            await self.bot.send_message(chat_id, response_text)

        except Exception as e:
            print(f"[TELEGRAM SESSION] Error: {e}")
            await self.bot.send_message(chat_id, f"Error: {str(e)[:200]}")
        finally:
            self._responding.discard(chat_id)

    async def _exec_tool(self, command: str) -> str:
        """Execute a real command via the server's HTTP endpoint."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "http://127.0.0.1:8000/telegram/exec",
                    json={"command": command}
                )
                if resp.status_code != 200:
                    return f"❌ Server error: {resp.status_code}"
                data = resp.json()
                if data.get("handled"):
                    return data.get("result", "OK")
                else:
                    # Command not recognized by executor — let Groq handle it
                    return None
        except httpx.ConnectError:
            return "❌ ADA no está corriendo en la PC (server offline)"
        except Exception as e:
            return f"❌ Error de conexión: {str(e)[:200]}"

    async def _get_groq_response(self, messages) -> str:
        """Send to Groq and return the text response."""
        try:
            client = _get_groq_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip() or "No recibí respuesta."
        except Exception as e:
            print(f"[TELEGRAM SESSION] Groq error: {e}")
            return f"Error de conexión: {str(e)[:200]}"

    def reset_conversation(self, chat_id: str):
        """Clear history for a chat."""
        if chat_id in self.conversations:
            self.conversations[chat_id] = []
            return True
        return False
