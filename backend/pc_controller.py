import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, Any

# FULL AUTONOMY — no app restrictions
ALLOWED_APPS: dict = None  # accept any app name

USER_HOME = Path.home()


async def open_app(app_name: str) -> Dict[str, Any]:
    # FULL AUTONOMY — open any app by name
    try:
        subprocess.Popen([app_name])
        return {"ok": True, "result": f"Aplicación abierta: {app_name}"}
    except Exception as e:
        return {"ok": False, "result": f"No pude abrir {app_name}: {e}"}


async def list_directory(path: str) -> Dict[str, Any]:
    try:
        p = Path(path).expanduser()
        if not p.exists() or not p.is_dir():
            return {"ok": False, "result": f"Directorio no existe: {p}"}
        items = sorted([x.name for x in p.iterdir()])
        return {"ok": True, "result": f"Contenido de {p}: {', '.join(items[:500])}"}
    except Exception as e:
        return {"ok": False, "result": f"Error leyendo directorio: {e}"}


async def read_text_file(path: str) -> Dict[str, Any]:
    try:
        p = Path(path).expanduser()
        content = p.read_text(encoding='utf-8', errors='ignore')[:50000]
        return {"ok": True, "result": f"Contenido de {p}:\n{content}"}
    except Exception as e:
        return {"ok": False, "result": f"Error leyendo archivo: {e}"}


async def write_text_file(path: str, content: str) -> Dict[str, Any]:
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        return {"ok": True, "result": f"Archivo escrito: {p}"}
    except Exception as e:
        return {"ok": False, "result": f"Error escribiendo archivo: {e}"}


async def run_safe_command(command: str) -> Dict[str, Any]:
    # FULL AUTONOMY — all commands allowed
    raw = (command or '').strip()
    try:
        proc = await asyncio.create_subprocess_shell(
            raw,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = (stdout or b'').decode(errors='ignore')
        err = (stderr or b'').decode(errors='ignore')
        text = (output + ('\n' + err if err else '')).strip()[:12000]
        return {"ok": proc.returncode == 0, "result": text or f"Comando ejecutado con código {proc.returncode}"}
    except Exception as e:
        return {"ok": False, "result": f"Error ejecutando comando: {e}"}


async def shutdown_pc(delay_seconds: int = 0) -> Dict[str, Any]:
    # FULL AUTONOMY — shutdown without confirmation
    seconds = max(0, int(delay_seconds or 0))
    try:
        subprocess.Popen(["shutdown", "/s", "/t", str(seconds)])
        return {"ok": True, "result": f"Apagado del PC programado en {seconds} segundos."}
    except Exception as e:
        return {"ok": False, "result": f"No pude programar el apagado del PC: {e}"}


async def restart_pc(delay_seconds: int = 0) -> Dict[str, Any]:
    seconds = max(0, int(delay_seconds or 0))
    try:
        subprocess.Popen(["shutdown", "/r", "/t", str(seconds)])
        return {"ok": True, "result": f"Reinicio programado en {seconds} segundos."}
    except Exception as e:
        return {"ok": False, "result": f"Error: {e}"}


async def lock_pc() -> Dict[str, Any]:
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return {"ok": True, "result": "PC bloqueado."}
    except Exception as e:
        return {"ok": False, "result": f"Error: {e}"}
