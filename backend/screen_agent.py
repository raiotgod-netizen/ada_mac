from __future__ import annotations

import base64
import io
from datetime import datetime
from pathlib import Path

import mss
from PIL import Image


class ScreenAgent:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def capture_snapshot(self, filename: str | None = None, monitor_index: int = 1) -> dict:
        safe_name = filename or f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in ("-", "_", ".")).strip() or "screen.png"
        if not safe_name.lower().endswith(".png"):
            safe_name += ".png"
        output = self.base_dir / safe_name

        with mss.mss() as sct:
            monitors = sct.monitors
            if len(monitors) <= monitor_index:
                monitor_index = 1
            shot = sct.grab(monitors[monitor_index])
            image = Image.frombytes("RGB", shot.size, shot.rgb)
            image.save(output)

        return {
            "ok": True,
            "path": str(output),
            "result": f"Captura de pantalla guardada en {output}",
        }

    def capture_frame_payload(self, monitor_index: int = 1, max_width: int = 900, image_format: str = "JPEG", quality: int = 55) -> dict:
        with mss.mss() as sct:
            monitors = sct.monitors
            if len(monitors) <= monitor_index:
                monitor_index = 1
            shot = sct.grab(monitors[monitor_index])
            image = Image.frombytes("RGB", shot.size, shot.rgb)

        if max_width and image.width > max_width:
            ratio = max_width / float(image.width)
            image = image.resize((int(image.width * ratio), int(image.height * ratio)))

        image_io = io.BytesIO()
        image.save(image_io, format=image_format, quality=quality, optimize=True)
        image_bytes = image_io.getvalue()

        latest_path = self.base_dir / "live_screen_latest.jpg"
        latest_path.write_bytes(image_bytes)

        return {
            "ok": True,
            "path": str(latest_path),
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("utf-8"),
            "width": image.width,
            "height": image.height,
            "captured_at": datetime.now().isoformat(),
            "result": "Frame de pantalla capturado.",
        }
