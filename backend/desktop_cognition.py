from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


PRODUCTIVITY_PROCESSES = {
    'code', 'cursor', 'devenv', 'pycharm64', 'notepad++', 'sublime_text', 'idea64', 'webstorm64', 'clion64', 'cmd', 'powershell', 'windowsterminal'
}
MEDIA_PROCESSES = {'spotify', 'vlc', 'music', 'foobar2000'}
BROWSER_PROCESSES = {'chrome', 'msedge', 'firefox', 'brave', 'opera'}
COMMUNICATION_PROCESSES = {'discord', 'slack', 'telegram', 'whatsapp', 'teams'}
CREATIVE_PROCESSES = {'photoshop', 'illustrator', 'blender', 'obs64', 'premierepro'}


@dataclass
class DesktopCognition:
    def infer(self, observer_snapshot: Dict[str, Any] | None = None, vision_snapshot: Dict[str, Any] | None = None, bluetooth_snapshot: Dict[str, Any] | None = None) -> Dict[str, Any]:
        observer_snapshot = observer_snapshot or {}
        vision_snapshot = vision_snapshot or {}
        bluetooth_snapshot = bluetooth_snapshot or {}

        active_window = observer_snapshot.get('active_window') or {}
        process_name = str(active_window.get('process') or '').lower()
        title = str(active_window.get('title') or '')
        windows_count = ((observer_snapshot.get('windows') or {}).get('count')) or 0
        browser_count = ((observer_snapshot.get('browser_windows') or {}).get('count')) or 0
        processes = ((observer_snapshot.get('processes') or {}).get('items')) or []
        known_devices = bluetooth_snapshot.get('known') or []
        connected_count = bluetooth_snapshot.get('connected_count') or 0
        brightness = (((vision_snapshot.get('screen') or {}).get('brightness')) if isinstance(vision_snapshot, dict) else None)
        action_hints = ((vision_snapshot.get('screen') or {}).get('action_hints')) or []
        text_regions = ((vision_snapshot.get('screen') or {}).get('text_regions')) or []
        ui_targets = ((vision_snapshot.get('screen') or {}).get('ui_targets')) or []
        ocr_ready = bool((vision_snapshot.get('screen') or {}).get('ocr_ready'))
        ocr_lines = ((vision_snapshot.get('screen') or {}).get('ocr_lines')) or []

        process_counter = Counter(str(item.get('Name') or item.get('name') or '').lower() for item in processes)
        categories = {
            'productivity': sum(process_counter.get(name, 0) for name in PRODUCTIVITY_PROCESSES),
            'media': sum(process_counter.get(name, 0) for name in MEDIA_PROCESSES),
            'browser': sum(process_counter.get(name, 0) for name in BROWSER_PROCESSES),
            'communication': sum(process_counter.get(name, 0) for name in COMMUNICATION_PROCESSES),
            'creative': sum(process_counter.get(name, 0) for name in CREATIVE_PROCESSES),
        }

        mode = 'general'
        confidence = 0.42
        if process_name in PRODUCTIVITY_PROCESSES:
            mode, confidence = 'productivity', 0.76
        elif process_name in MEDIA_PROCESSES:
            mode, confidence = 'media', 0.78
        elif process_name in BROWSER_PROCESSES:
            mode, confidence = 'web_navigation', 0.72
        elif process_name in COMMUNICATION_PROCESSES:
            mode, confidence = 'communication', 0.74
        elif process_name in CREATIVE_PROCESSES:
            mode, confidence = 'creative', 0.73
        elif browser_count > 0:
            mode, confidence = 'browser_assist', 0.58

        intents: List[str] = []
        lower_title = title.lower()
        if any(term in lower_title for term in ['youtube', 'spotify', 'playlist', 'music']):
            intents.append('consumo o control multimedia')
        if any(term in lower_title for term in ['visual studio', 'cursor', 'github', 'terminal', 'powershell', 'code']):
            intents.append('trabajo técnico o programación')
        if any(term in lower_title for term in ['mail', 'gmail', 'outlook', 'discord', 'slack', 'telegram']):
            intents.append('comunicación o revisión de mensajes')
        if any(term in lower_title for term in ['cad', 'fusion', 'blender', 'printer', 'slicer']):
            intents.append('diseño, impresión o fabricación')
        if not intents:
            intents.append('actividad general de escritorio')

        risks: List[str] = []
        if brightness is not None and brightness < 40:
            risks.append('pantalla oscura, posible riesgo de clicks ciegos')
        if windows_count > 12:
            risks.append('muchas ventanas abiertas, posible ambigüedad operacional')
        if connected_count > 0:
            risks.append('hay dispositivos Bluetooth conectados, evitar interrumpir audio o periféricos sin confirmar')

        recommendations: List[str] = []
        if mode in {'web_navigation', 'browser_assist'}:
            recommendations.append('usar navegación guiada con foco explícito en la ventana activa')
        if mode == 'productivity':
            recommendations.append('priorizar lectura de errores, terminales y archivos antes de automatizar')
        if mode == 'media':
            recommendations.append('usar controles multimedia y confirmar dispositivo de salida')
        if process_name == 'spotify' or 'spotify' in lower_title:
            recommendations.append('permitir comandos de reproducción, búsqueda y cambio de pista')
        if known_devices:
            recommendations.append('usar memoria de dispositivos conocidos para acciones Bluetooth más rápidas')
        if action_hints:
            recommendations.append('aprovechar pistas visuales de pantalla antes de mover el cursor')
        if text_regions:
            recommendations.append('hay regiones de texto detectadas, buen punto para OCR o lectura contextual')
        if ocr_lines:
            recommendations.append('hay texto real extraído de la pantalla, usarlo para navegar o diagnosticar con más precisión')
        if ui_targets:
            recommendations.append('hay controles UI detectados, se puede automatizar con menos ambigüedad')

        suggested_automations: List[Dict[str, Any]] = []
        if mode in {'media', 'web_navigation', 'browser_assist'}:
            suggested_automations.append({
                'id': 'media_assist',
                'title': 'Asistencia multimedia contextual',
                'description': 'Controlar reproducción, buscar contenido o enfocar la app activa de media/web.',
                'safe': True,
            })
        if mode == 'productivity':
            suggested_automations.append({
                'id': 'workspace_scan',
                'title': 'Escaneo del workspace activo',
                'description': 'Leer terminal, ventana activa y estado del proyecto antes de proponer acciones.',
                'safe': True,
            })
        if connected_count or known_devices:
            suggested_automations.append({
                'id': 'bluetooth_routine',
                'title': 'Rutina de dispositivos cercanos',
                'description': 'Revisar inventario Bluetooth, detectar periféricos conocidos y sugerir acciones seguras.',
                'safe': True,
            })

        return {
            'available': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'perception': {
                'ocr_ready': ocr_ready,
                'text_regions_count': len(text_regions),
                'ui_targets_count': len(ui_targets),
                'ocr_lines_count': len(ocr_lines),
            },
            'mode': mode,
            'confidence': round(confidence, 2),
            'focus': {
                'window_title': title or None,
                'process': process_name or None,
                'windows_count': windows_count,
                'browser_count': browser_count,
            },
            'activity': {
                'dominant_categories': categories,
                'likely_intents': intents,
            },
            'risk_flags': risks,
            'recommendations': recommendations,
            'suggested_automations': suggested_automations,
            'summary': f"Modo inferido: {mode}. Ventana activa: {title or 'desconocida'}. Intención probable: {intents[0]}. Riesgos: {len(risks)}."
        }
