from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    from rapidocr_onnxruntime import RapidOCR
except Exception:  # pragma: no cover
    RapidOCR = None


class OCREngine:
    def __init__(self):
        self._engine = None
        self._init_error = None
        if RapidOCR is None:
            self._init_error = 'rapidocr_onnxruntime no disponible'
            return
        try:
            self._engine = RapidOCR()
        except Exception as e:  # pragma: no cover
            self._init_error = str(e)

    @property
    def ready(self) -> bool:
        return self._engine is not None

    @property
    def init_error(self) -> str | None:
        return self._init_error

    def extract(self, path: str | None) -> Dict[str, Any]:
        if not path:
            return {
                'available': False,
                'ocr_ready': self.ready,
                'summary': 'Sin imagen para OCR.',
                'lines': [],
            }
        if not self.ready:
            return {
                'available': False,
                'ocr_ready': False,
                'summary': f"OCR no disponible: {self._init_error or 'motor no inicializado'}",
                'lines': [],
            }

        image_path = str(Path(path))
        try:
            result, _ = self._engine(image_path)
        except Exception as e:
            return {
                'available': False,
                'ocr_ready': True,
                'summary': f"OCR falló: {e}",
                'lines': [],
            }

        lines: List[Dict[str, Any]] = []
        for item in result or []:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            box = item[0] or []
            text = ''
            score = 0.0

            if len(item) >= 3 and isinstance(item[1], str):
                text = item[1]
                try:
                    score = float(item[2])
                except Exception:
                    score = 0.0
            else:
                text_info = item[1] or []
                text = text_info[0] if isinstance(text_info, (list, tuple)) and len(text_info) > 0 else ''
                try:
                    score = float(text_info[1]) if isinstance(text_info, (list, tuple)) and len(text_info) > 1 else 0.0
                except Exception:
                    score = 0.0

            if not text:
                continue
            xs = [int(point[0]) for point in box] if box else [0]
            ys = [int(point[1]) for point in box] if box else [0]
            lines.append({
                'text': str(text).strip(),
                'confidence': round(score, 3),
                'x': min(xs),
                'y': min(ys),
                'w': max(xs) - min(xs) if xs else 0,
                'h': max(ys) - min(ys) if ys else 0,
            })

        lines = [line for line in lines if line['text']]
        lines.sort(key=lambda line: (line['y'], line['x']))
        joined = ' | '.join(line['text'] for line in lines[:8])
        return {
            'available': True,
            'ocr_ready': True,
            'summary': f"OCR detectó {len(lines)} líneas." + (f" Primeras: {joined}" if joined else ''),
            'lines': lines[:24],
        }
