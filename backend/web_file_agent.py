from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import os

import aiohttp


class WebFileAgent:
    def __init__(self, downloads_dir: str | Path, uploads_dir: str | Path):
        self.downloads_dir = Path(downloads_dir)
        self.uploads_dir = Path(uploads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)

    def _safe_filename_from_url(self, url: str, fallback: str = "downloaded_file") -> str:
        parsed = urlparse(url)
        name = Path(parsed.path).name or fallback
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", ".", " ")).strip().replace(" ", "_")
        return safe or fallback

    def _resolve_upload_path(self, path: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (self.uploads_dir.parent / candidate).resolve()
        return candidate

    async def download_file(self, url: str, filename: str | None = None) -> dict:
        url = (url or "").strip()
        if not url.startswith(("http://", "https://")):
            return {"ok": False, "result": "La URL debe comenzar con http:// o https://"}

        target_name = filename or self._safe_filename_from_url(url)
        output = self.downloads_dir / target_name

        try:
            timeout = aiohttp.ClientTimeout(total=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status >= 400:
                        return {"ok": False, "result": f"Descarga fallida ({resp.status}) desde {url}"}
                    with open(output, "wb") as f:
                        async for chunk in resp.content.iter_chunked(65536):
                            if chunk:
                                f.write(chunk)
            return {"ok": True, "path": str(output), "result": f"Archivo descargado en {output}"}
        except Exception as e:
            return {"ok": False, "result": f"Error descargando archivo: {e}"}

    async def upload_file(self, file_path: str, target_url: str, field_name: str = "file") -> dict:
        target_url = (target_url or "").strip()
        if not target_url.startswith(("http://", "https://")):
            return {"ok": False, "result": "La URL de subida debe comenzar con http:// o https://"}

        path = self._resolve_upload_path(file_path)
        if not path.exists() or not path.is_file():
            return {"ok": False, "result": f"No existe el archivo a subir: {path}"}

        try:
            timeout = aiohttp.ClientTimeout(total=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                with open(path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field(field_name, f, filename=os.path.basename(path))
                    async with session.post(target_url, data=data) as resp:
                        text = await resp.text()
                        if resp.status >= 400:
                            return {"ok": False, "result": f"Subida fallida ({resp.status}): {text[:1200]}"}
            return {"ok": True, "result": f"Archivo subido correctamente a {target_url}", "path": str(path)}
        except Exception as e:
            return {"ok": False, "result": f"Error subiendo archivo: {e}"}
