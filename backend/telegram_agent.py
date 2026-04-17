"""
TelegramBot Agent — Handles text messages from Telegram bots.
Uses polling (no webhook needed) with httpx async client.
"""

import asyncio
import httpx
import os
from pathlib import Path


class TelegramBot:
    def __init__(self, token: str = None, admin_chat_id: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = admin_chat_id or os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.running = False
        self._task = None
        self._message_callback = None
        # Pending message IDs to avoid processing duplicates
        self._processed_ids = set()

    def set_message_callback(self, callback):
        """callback(text, chat_id, message_id) — called for each incoming text message."""
        self._message_callback = callback

    async def _poll(self):
        """Background polling loop."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            while self.running:
                try:
                    # Get updates (long polling)
                    params = {"timeout": 25, "offset": self.offset}
                    resp = await client.get(f"{self.base_url}/getUpdates", params=params)
                    data = resp.json()

                    if data.get("ok") and data.get("result"):
                        for update in data["result"]:
                            self.offset = update["update_id"] + 1
                            # Process message
                            message = update.get("message", {})
                            if message.get("text") and message.get("chat", {}).get("id"):
                                msg_id = update["update_id"]
                                if msg_id not in self._processed_ids:
                                    self._processed_ids.add(msg_id)
                                    text = message["text"]
                                    chat_id = message["chat"]["id"]
                                    # Ignore very large messages (probably spam)
                                    if len(text) < 4000 and self._message_callback:
                                        try:
                                            asyncio.create_task(self._message_callback(text, chat_id))
                                        except Exception as e:
                                            print(f"[TELEGRAM] Callback error: {e}")

                    # Cleanup old processed IDs to prevent memory growth
                    if len(self._processed_ids) > 1000:
                        self._processed_ids = set(list(self._processed_ids)[-500:])

                except httpx.TimeoutException:
                    # Normal long poll timeout — just continue
                    pass
                except Exception as e:
                    print(f"[TELEGRAM] Poll error: {e}")
                    await asyncio.sleep(5)

    async def start(self):
        """Start the polling loop in background."""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._poll())
        print(f"[TELEGRAM] Bot started (token prefix: ...{self.token[-4:] if self.token else 'NONE'})")

    async def stop(self):
        """Stop the polling loop."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        print("[TELEGRAM] Bot stopped")

    async def send_message(self, chat_id: str, text: str, parse_mode: str = None):
        """Send a text message to a Telegram chat."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {"chat_id": chat_id, "text": text}
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                resp = await client.post(f"{self.base_url}/sendMessage", json=payload)
                result = resp.json()
                if not result.get("ok"):
                    print(f"[TELEGRAM] Send error: {result}")
                return result
        except Exception as e:
            print(f"[TELEGRAM] Send message error: {e}")
            return {"ok": False, "error": str(e)}

    async def send_voice(self, chat_id: str, audio_path: str, caption: str = None):
        """Send a voice message (OGG/MP3) to a Telegram chat."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"voice": open(audio_path, "rb")}
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption
                resp = await client.post(f"{self.base_url}/sendVoice", data=data, files=files)
                result = resp.json()
                if not result.get("ok"):
                    print(f"[TELEGRAM] Send voice error: {result}")
                return result
        except Exception as e:
            print(f"[TELEGRAM] Send voice error: {e}")
            return {"ok": False, "error": str(e)}

    async def send_photo(self, chat_id: str, photo_path: str, caption: str = None):
        """Send a photo to a Telegram chat."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                files = {"photo": open(photo_path, "rb")}
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption
                resp = await client.post(f"{self.base_url}/sendPhoto", data=data, files=files)
                result = resp.json()
                if not result.get("ok"):
                    print(f"[TELEGRAM] Send photo error: {result}")
                return result
        except Exception as e:
            print(f"[TELEGRAM] Send photo error: {e}")
            return {"ok": False, "error": str(e)}

    async def get_me(self):
        """Get bot info."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/getMe")
                return resp.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}


def create_telegram_bot():
    """Factory — reads token from environment or .env file."""
    dotenv_path = Path(__file__).parent / ".env"
    if dotenv_path.exists():
        from dotenv import load_dotenv
        load_dotenv(dotenv_path)
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    if not token:
        print("[TELEGRAM] WARNING: TELEGRAM_BOT_TOKEN not set in environment or .env file")
    return TelegramBot(token=token, admin_chat_id=admin)
