"""
TelegramToolExecutor — Ejecuta commands reales en la PC desde Telegram.
Aislado de ada.py para no interferir con el audio/voice pipeline.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from urllib.parse import quote

# Ensure backend path is available
sys.path.insert(0, str(Path(__file__).parent))

from desktop_automation import DesktopAutomation
from kasa_agent import KasaAgent
from file_agent import FileAgent
from email_agent import EmailAgent


class TelegramToolExecutor:
    """Ejecutor de comandos reales para Telegram — no depende de ada.py ni del audio loop."""

    def __init__(self):
        self._desktop = None
        self._kasa = None
        self._file_agent = None
        self._email_agent = None
        self._workspace_root = Path(__file__).parent

    def _get_desktop(self):
        if self._desktop is None:
            self._desktop = DesktopAutomation()
        return self._desktop

    def _get_kasa(self):
        if self._kasa is None:
            self._kasa = KasaAgent()
        return self._kasa

    def _get_file_agent(self):
        if self._file_agent is None:
            self._file_agent = FileAgent(workspace_root=str(self._workspace_root))
        return self._file_agent

    def _get_email_agent(self):
        if self._email_agent is None:
            self._email_agent = EmailAgent()
        return self._email_agent

    async def execute(self, command: str) -> str:
        """Parse command and execute. Returns result text."""
        command = command.strip()
        lower = command.lower()

        # --- Spotify ---
        if lower.startswith("spotify ") or lower == "spotify":
            return await self._cmd_spotify(command)

        # --- Volume ---
        if lower.startswith("volumen ") or lower.startswith("volume "):
            return await self._cmd_volume(command)

        # --- Kasa / Luces ---
        if "luz" in lower or "light" in lower or "kasa" in lower:
            return await self._cmd_kasa(command)

        # --- Read file ---
        if lower.startswith("leer ") or lower.startswith("read "):
            return await self._cmd_read_file(command)

        # --- Write file ---
        if lower.startswith("escribir ") or lower.startswith("write "):
            return await self._cmd_write_file(command)

        # --- List directory ---
        if lower.startswith("ls ") or lower.startswith("dir "):
            return await self._cmd_list_dir(command)

        # --- Send email ---
        if lower.startswith("email ") or lower.startswith("send email "):
            return await self._cmd_email(command)

        # --- Open URL ---
        if lower.startswith("abrir ") or lower.startswith("open "):
            return await self._cmd_open_url(command)

        # --- PC control ---
        if "apagar pc" in lower or "shutdown pc" in lower:
            return await self._cmd_shutdown()

        return None  # No command matched — let Groq handle it

    async def _cmd_spotify(self, command: str) -> str:
        """spotify [play|pause|next|prev|search <query>]"""
        parts = command.split(" ", 1)
        action = "play"
        query = None

        if len(parts) > 1:
            rest = parts[1].strip().lower()
            if rest in {"play", "pause", "toggle", "next", "prev", "previous", "open"}:
                action = rest
            else:
                action = "search"
                query = parts[1].strip()

        try:
            desk = self._get_desktop()
            result = await asyncio.to_thread(desk.spotify_playback, action, query)
            return f"🎵 {result.get('result', 'OK')}"
        except Exception as e:
            return f"❌ Error Spotify: {e}"

    async def _cmd_volume(self, command: str) -> str:
        """volumen [0-100]"""
        parts = command.split()
        try:
            level = int(parts[-1])
            level = max(0, min(100, level))
        except ValueError:
            return "❌ Uso: /volumen 0-100"

        try:
            desk = self._get_desktop()
            result = await asyncio.to_thread(desk.set_volume, level)
            return f"🔊 Volumen puesto a {level}%"
        except Exception as e:
            return f"❌ Error volumen: {e}"

    async def _cmd_kasa(self, command: str) -> str:
        """controlar luces: 'encender luz', 'apagar luz', 'toggle luz'"""
        lower = command.lower()
        action = None
        target = None

        if "encender" in lower or "prender" in lower or "on" in lower:
            action = "on"
        elif "apagar" in lower or "off" in lower:
            action = "off"
        elif "toggle" in lower:
            action = "toggle"

        # Try to extract device name
        words = lower.replace("luz", "").replace("light", "").replace("kasa", "").strip().split()
        target = " ".join(words) if words else None

        try:
            kasa = self._get_kasa()
            await asyncio.to_thread(kasa.initialize)
            devices = await asyncio.to_thread(kasa.discover_devices)
            if not devices:
                return "⚠️ No encontré dispositivos Kasa"

            # Find device
            device = None
            for d in devices:
                alias = d.get("alias", "").lower()
                if target and target in alias:
                    device = d
                    break
                elif not target and ("luz" in alias or "light" in alias):
                    device = d
                    break

            if not device:
                device = devices[0]  # Default to first

            ip = device["ip"]
            state = await asyncio.to_thread(kasa.set_device_state, ip, action)
            return f"💡 {device.get('alias', ip)}: {state}"
        except Exception as e:
            return f"❌ Error Kasa: {e}"

    async def _cmd_read_file(self, command: str) -> str:
        """leer <path>"""
        parts = command.split(" ", 1)
        if len(parts) < 2:
            return "❌ Uso: leer <ruta del archivo>"
        path = parts[1].strip()
        try:
            agent = self._get_file_agent()
            result = await asyncio.to_thread(agent.read_file, path)
            if result.get("ok"):
                content = result.get("content", "")[:500]
                return f"📄 {path}\n\n{content}"
            else:
                return f"❌ {result.get('error', 'No se pudo leer')}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def _cmd_write_file(self, command: str) -> str:
        """escribir <path> <content>"""
        # Format: escribir <path> || <content>
        parts = command.split(" || ", 1)
        if len(parts) < 2:
            return "❌ Uso: escribir <path> || <contenido>"
        path = parts[0].split(" ", 1)[1].strip()
        content = parts[1].strip()
        try:
            agent = self._get_file_agent()
            result = await asyncio.to_thread(agent.write_file, path, content)
            if result.get("ok"):
                return f"✅ Archivo escrito: {path}"
            else:
                return f"❌ {result.get('error', 'Error desconocido')}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def _cmd_list_dir(self, command: str) -> str:
        """ls <path>"""
        parts = command.split(" ", 1)
        path = parts[1].strip() if len(parts) > 1 else "."
        try:
            agent = self._get_file_agent()
            result = await asyncio.to_thread(agent.list_directory, path)
            if result.get("ok"):
                items = result.get("files", []) + result.get("directories", [])
                return "📁 " + "\n".join(items[:20])
            else:
                return f"❌ {result.get('error', 'No se pudo listar')}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def _cmd_email(self, command: str) -> str:
        """email <to> || <subject> || <body>"""
        parts = command.split(" || ", 2)
        if len(parts) < 3:
            return "❌ Uso: email <destinatario> || <asunto> || <cuerpo>"
        to = parts[0].split(" ", 1)[1].strip()
        subject = parts[1].strip()
        body = parts[2].strip()
        try:
            agent = self._get_email_agent()
            result = await asyncio.to_thread(agent.send_email, to, subject, body)
            if result.get("ok"):
                return f"✅ Email enviado a {to}"
            else:
                return f"❌ {result.get('error', 'Error al enviar')}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def _cmd_open_url(self, command: str) -> str:
        """abrir <url>"""
        parts = command.split(" ", 1)
        if len(parts) < 2:
            return "❌ Uso: abrir <url>"
        url = parts[1].strip()
        try:
            desk = self._get_desktop()
            result = await asyncio.to_thread(desk.open_url, url)
            return f"🌐 {result.get('result', 'Abierto')}"
        except Exception as e:
            return f"❌ Error: {e}"

    async def _cmd_shutdown(self) -> str:
        """Apagar PC"""
        try:
            subprocess.run(["shutdown", "/s", "/t", "30"], check=True)
            return "🖥️ PC apagándose en 30 segundos..."
        except Exception as e:
            return f"❌ No pude apagar: {e}"


# Singleton
_executor = None

def get_executor():
    global _executor
    if _executor is None:
        _executor = TelegramToolExecutor()
    return _executor
