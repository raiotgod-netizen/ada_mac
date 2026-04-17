from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import cv2
import numpy as np

from ocr_engine import OCREngine


class VisionTargets:
    def __init__(self):
        self.ocr = OCREngine()

    def analyze(self, path: str | None) -> Dict[str, Any]:
        if not path:
            return {
                'available': False,
                'ocr_ready': False,
                'summary': 'Sin captura para analizar targets.',
                'text_regions': [],
                'ui_targets': [],
            }

        image = cv2.imread(str(Path(path)))
        if image is None:
            return {
                'available': False,
                'ocr_ready': False,
                'summary': 'No pude abrir la captura para analizar targets.',
                'text_regions': [],
                'ui_targets': [],
            }

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]

        text_regions = self._detect_text_regions(gray, width, height)
        ocr_snapshot = self.ocr.extract(path)
        ui_targets = self._detect_ui_targets(gray, width, height, ocr_snapshot.get('lines', []))

        return {
            'available': True,
            'ocr_ready': ocr_snapshot.get('ocr_ready', False),
            'ocr_available': ocr_snapshot.get('available', False),
            'ocr_summary': ocr_snapshot.get('summary'),
            'ocr_lines': ocr_snapshot.get('lines', []),
            'summary': f"Detecté {len(text_regions)} regiones candidatas de texto y {len(ui_targets)} objetivos UI probables.",
            'text_regions': text_regions[:12],
            'ui_targets': ui_targets[:12],
        }

    def _detect_text_regions(self, gray: np.ndarray, width: int, height: int) -> List[Dict[str, Any]]:
        grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        _, thresh = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        connected = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((3, 15), np.uint8))
        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        regions: List[Dict[str, Any]] = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if w < 60 or h < 12 or area < 1200:
                continue
            if w > int(width * 0.95) or h > int(height * 0.3):
                continue
            aspect = round(w / max(h, 1), 2)
            regions.append({
                'type': 'text_region',
                'x': int(x),
                'y': int(y),
                'w': int(w),
                'h': int(h),
                'cx': int(x + w / 2),
                'cy': int(y + h / 2),
                'area': int(area),
                'aspect_ratio': aspect,
                'confidence': round(min(0.9, 0.35 + (w / max(width, 1)) * 0.4 + (0.12 if aspect > 3 else 0)), 2),
                'reason': 'bloque con densidad de bordes horizontal compatible con texto',
            })

        regions.sort(key=lambda item: (item['confidence'], item['area']), reverse=True)
        return regions

    def _classify_semantic_role(self, x: int, y: int, w: int, h: int, width: int, height: int, nearby_text: str) -> tuple[str, float, str]:
        nearby = (nearby_text or '').strip().lower()
        aspect = w / max(h, 1)
        if any(term in nearby for term in ['search', 'buscar', 'google', 'url', 'address', 'dirección', 'https', 'http', 'www']):
            return 'search_bar', 0.86, 'texto cercano sugiere barra de búsqueda o dirección'
        if any(term in nearby for term in ['ok', 'aceptar', 'submit', 'send', 'enviar', 'save', 'guardar', 'apply', 'install', 'descargar', 'download', 'actualizar', 'update']):
            return 'confirm_button', 0.83, 'texto cercano sugiere acción de confirmación'
        if any(term in nearby for term in ['cancel', 'cerrar', 'close', 'x', 'minimize', 'minimizar', 'maximize', 'expand', 'restaurar']):
            return 'dismiss_button', 0.78, 'texto cercano sugiere cierre o descarte'
        if y < int(height * 0.14) and aspect > 2.4:
            return 'top_bar_control', 0.7, 'ubicación alta y forma horizontal compatible con barra o pestaña'
        if 2.8 <= aspect <= 14 and h <= 50:
            return 'input_field', 0.68, 'forma horizontal compatible con campo de entrada'
        if 1.2 <= aspect <= 5.5:
            return 'button', 0.64, 'rectángulo compacto compatible con botón'
        if y > int(height * 0.78):
            return 'bottom_action', 0.6, 'ubicación inferior compatible con acción persistente'
        return 'panel_control', 0.52, 'control rectangular genérico'

    def _detect_ui_targets(self, gray: np.ndarray, width: int, height: int, ocr_lines: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        targets: List[Dict[str, Any]] = []
        ocr_lines = ocr_lines or []
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
            x, y, w, h = cv2.boundingRect(approx)
            area = w * h
            if area < 900 or w < 24 or h < 18:
                continue
            if w > int(width * 0.6) or h > int(height * 0.25):
                continue
            rect_like = len(approx) in {4, 5, 6}
            if not rect_like:
                continue

            region = gray[y:y+h, x:x+w]
            mean_intensity = float(np.mean(region)) if region.size else 0.0
            confidence = 0.38
            if 40 <= mean_intensity <= 235:
                confidence += 0.18
            if 1.4 <= (w / max(h, 1)) <= 8:
                confidence += 0.2

            nearby_lines = []
            for line in ocr_lines:
                lx, ly, lw, lh = int(line.get('x', 0)), int(line.get('y', 0)), int(line.get('w', 0)), int(line.get('h', 0))
                overlap_x = not (lx + lw < x - 24 or lx > x + w + 24)
                overlap_y = not (ly + lh < y - 18 or ly > y + h + 18)
                if overlap_x and overlap_y:
                    nearby_lines.append(str(line.get('text', '')))
            nearby_text = ' '.join(nearby_lines[:4]).strip()
            semantic, semantic_confidence, semantic_reason = self._classify_semantic_role(x, y, w, h, width, height, nearby_text)
            confidence = min(0.94, confidence + semantic_confidence * 0.25)

            targets.append({
                'type': semantic,
                'semantic_role': semantic,
                'x': int(x),
                'y': int(y),
                'w': int(w),
                'h': int(h),
                'cx': int(x + w / 2),
                'cy': int(y + h / 2),
                'area': int(area),
                'nearby_text': nearby_text,
                'confidence': round(min(confidence, 0.92), 2),
                'reason': semantic_reason,
            })

        targets.sort(key=lambda item: (item['confidence'], item['area']), reverse=True)
        return targets
