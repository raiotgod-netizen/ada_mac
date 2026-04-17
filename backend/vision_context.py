from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageStat

from vision_targets import VisionTargets


class VisionContext:
    def __init__(self):
        self.targets = VisionTargets()

    def summarize_snapshot(self, path: str | None, system_observer: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if not path:
            return {
                "available": False,
                "summary": "Sin captura disponible.",
                "screen": {
                    "ocr_ready": getattr(self.targets.ocr, 'ready', False),
                    "ocr_available": False,
                    "ocr_summary": "Sin captura para OCR todavía.",
                    "ocr_lines": [],
                    "text_regions": [],
                    "ui_targets": [],
                    "target_summary": "Sin captura para analizar targets.",
                },
            }

        try:
            img = Image.open(Path(path)).convert("RGB")
            width, height = img.size
            bands = img.resize((1, 1)).getpixel((0, 0))
            stat = ImageStat.Stat(img)
            brightness = round(sum(stat.mean) / 3, 2)

            top_left = img.crop((0, 0, max(1, width // 2), max(1, height // 2))).resize((1, 1)).getpixel((0, 0))
            top_right = img.crop((max(0, width // 2), 0, width, max(1, height // 2))).resize((1, 1)).getpixel((0, 0))
            bottom_left = img.crop((0, max(0, height // 2), max(1, width // 2), height)).resize((1, 1)).getpixel((0, 0))
            bottom_right = img.crop((max(0, width // 2), max(0, height // 2), width, height)).resize((1, 1)).getpixel((0, 0))

            active_window = ((system_observer or {}).get("active_window") or {}).get("title")
            active_process = ((system_observer or {}).get("active_window") or {}).get("process")
            browser_count = ((system_observer or {}).get("browser_windows") or {}).get("count", 0)
            windows_count = ((system_observer or {}).get("windows") or {}).get("count", 0)

            dominant_hint = "pantalla equilibrada"
            if brightness < 55:
                dominant_hint = "pantalla oscura"
            elif brightness > 200:
                dominant_hint = "pantalla muy clara"

            region_summary = {
                "top_left": top_left,
                "top_right": top_right,
                "bottom_left": bottom_left,
                "bottom_right": bottom_right,
            }

            target_snapshot = self.targets.analyze(path)

            action_hints = []
            suggested_targets = []
            if active_window:
                action_hints.append(f"contexto activo en '{active_window}'")
            if browser_count > 0:
                action_hints.append("hay navegador disponible para navegación guiada")
            if windows_count <= 1:
                action_hints.append("pocas ventanas abiertas, menor ambigüedad para automatizar")
            if brightness < 40:
                action_hints.append("la pantalla parece muy oscura, conviene verificar foco antes de hacer click")

            if browser_count > 0:
                suggested_targets.extend([
                    {"name": "top_search_bar", "x": width // 2, "y": max(40, height // 12), "reason": "zona habitual de barra de navegación/búsqueda"},
                    {"name": "center_content", "x": width // 2, "y": height // 2, "reason": "zona media útil para resultados o reproducción"},
                    {"name": "upper_results", "x": width // 2, "y": max(120, height // 4), "reason": "zona probable de primeros resultados"}
                ])
            suggested_targets.extend([
                {
                    "name": item.get("type", "ui_target"),
                    "x": item.get("cx"),
                    "y": item.get("cy"),
                    "reason": item.get("reason"),
                    "confidence": item.get("confidence"),
                }
                for item in target_snapshot.get("ui_targets", [])[:8]
            ])

            return {
                "available": True,
                "summary": f"Pantalla {width}x{height}, brillo {brightness}, color medio RGB {bands}, ventana activa: {active_window or 'desconocida'}, proceso activo: {active_process or 'desconocido'}, navegadores visibles: {browser_count}, lectura general: {dominant_hint}.",
                "screen": {
                    "path": path,
                    "width": width,
                    "height": height,
                    "average_rgb": bands,
                    "brightness": brightness,
                    "active_window": active_window,
                    "active_process": active_process,
                    "browser_windows": browser_count,
                    "windows_count": windows_count,
                    "regions": region_summary,
                    "action_hints": action_hints,
                    "suggested_targets": suggested_targets,
                    "ocr_ready": target_snapshot.get("ocr_ready", False),
                    "ocr_available": target_snapshot.get("ocr_available", False),
                    "ocr_summary": target_snapshot.get("ocr_summary"),
                    "ocr_lines": target_snapshot.get("ocr_lines", []),
                    "text_regions": target_snapshot.get("text_regions", []),
                    "ui_targets": target_snapshot.get("ui_targets", []),
                    "target_summary": target_snapshot.get("summary"),
                },
            }
        except Exception as e:
            return {
                "available": False,
                "summary": f"No pude resumir la captura: {e}",
                "screen": {"path": path},
            }
