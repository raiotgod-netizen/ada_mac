from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


class VisualPlaybook:
    """
    Conocimiento específico por aplicación para resolución visual.
    Cada app tiene heurísticas de dónde buscar y qué	atrás de acción.
    """

    APP_PATTERNS = {
        'spotify': {
            'processes': ['spotify', 'spotil'],
            'search_region': {'top_pct': 0.0, 'bottom_pct': 0.18, 'left_pct': 0.25, 'right_pct': 0.75},
            'search_hotkey': 'ctrl+l',
            'playback_controls_region': {'top_pct': 0.88, 'bottom_pct': 1.0, 'left_pct': 0.35, 'right_pct': 0.65},
            'suggested_actions': ['play', 'pause', 'next', 'previous', 'shuffle', 'repeat', 'mute', 'volume'],
        },
        'msedge': {
            'processes': ['msedge', 'microsoft edge', 'edge'],
            'address_bar_region': {'top_pct': 0.0, 'bottom_pct': 0.1, 'left_pct': 0.08, 'right_pct': 0.92},
            'address_bar_heuristic': 'horizontal_bar_near_top_with_url_chars',
            'new_tab_region': {'top_pct': 0.0, 'bottom_pct': 0.1, 'left_pct': 0.85, 'right_pct': 0.99},
            'suggested_actions': ['new tab', 'refresh', 'back', 'forward', 'bookmarks', 'settings'],
        },
        'explorer': {
            'processes': ['explorer', 'dwm'],
            'address_bar_region': {'top_pct': 0.0, 'bottom_pct': 0.12, 'left_pct': 0.0, 'right_pct': 0.85},
            'search_box_region': {'top_pct': 0.0, 'bottom_pct': 0.12, 'left_pct': 0.65, 'right_pct': 0.95},
            'sidebar_region': {'top_pct': 0.12, 'bottom_pct': 0.85, 'left_pct': 0.0, 'right_pct': 0.22},
            'suggested_actions': ['new folder', 'rename', 'delete', 'copy', 'paste', 'properties'],
        },
        'settings': {
            'processes': ['systemsettings', 'windows settings'],
            'sidebar_region': {'top_pct': 0.0, 'bottom_pct': 1.0, 'left_pct': 0.0, 'right_pct': 0.28},
            'main_panel_region': {'top_pct': 0.0, 'bottom_pct': 1.0, 'left_pct': 0.28, 'right_pct': 1.0},
            'search_region': {'top_pct': 0.0, 'bottom_pct': 0.08, 'left_pct': 0.3, 'right_pct': 0.9},
            'suggested_actions': ['bluetooth', 'wifi', 'network', 'display', 'sound', 'power', 'apps', 'privacy'],
        },
        'discord': {
            'processes': ['discord'],
            'channel_list_region': {'top_pct': 0.1, 'bottom_pct': 0.75, 'left_pct': 0.0, 'right_pct': 0.22},
            'message_input_region': {'top_pct': 0.82, 'bottom_pct': 1.0, 'left_pct': 0.22, 'right_pct': 0.78},
            'member_list_region': {'top_pct': 0.1, 'bottom_pct': 1.0, 'left_pct': 0.78, 'right_pct': 1.0},
            'suggested_actions': ['send message', 'join channel', 'leave channel', 'mute', 'deafen'],
        },
        'powershell': {
            'processes': ['powershell', 'pwsh', 'windows terminal', 'terminal'],
            'prompt_region': {'top_pct': 0.0, 'bottom_pct': 1.0, 'left_pct': 0.0, 'right_pct': 1.0},
            'suggested_actions': ['run command', 'clear', 'copy output'],
        },
    }

    def __init__(self):
        pass

    def detect_app(self, observer_snapshot: Dict[str, Any] | None = None) -> str | None:
        if not observer_snapshot:
            return None
        active = (observer_snapshot.get('active_window') or {})
        process = str(active.get('process') or '').lower()
        title = str(active.get('title') or '').lower()
        combined = f"{process} {title}"
        for app_name, app_def in self.APP_PATTERNS.items():
            for pattern in app_def['processes']:
                if pattern in combined:
                    return app_name
        return None

    def get_search_hints(self, app: str, query: str) -> List[Dict[str, Any]]:
        if app not in self.APP_PATTERNS:
            return []
        hints = []
        query_l = query.lower().strip()
        app_def = self.APP_PATTERNS[app]
        for action in app_def.get('suggested_actions', []):
            if query_l in action or action in query_l:
                hints.append({
                    'strategy': 'suggested_action',
                    'action': action,
                    'app': app,
                    'reason': f'acción sugerida para {app}',
                })
        if app == 'spotify' and any(t in query_l for t in ['play', 'pause', 'song', 'music', 'pista']):
            hints.append({
                'strategy': 'hotkey',
                'action': 'ctrl+l',
                'target': 'search_box',
                'app': app,
                'reason': 'Spotify: usar hotkey para ir a búsqueda directamente',
            })
        if app == 'msedge' and not any(c in query_l for c in ['.', '/', 'http']):
            hints.append({
                'strategy': 'address_bar',
                'action': 'ctrl+l',
                'target': 'address_bar',
                'app': app,
                'reason': 'Edge: predecir que es una búsqueda, no URL directa',
            })
        return hints

    def get_region_filter(self, app: str, region_name: str) -> Dict[str, float] | None:
        if app not in self.APP_PATTERNS:
            return None
        regions = self.APP_PATTERNS[app]
        return regions.get(f'{region_name}_region')

    def apply_region_filter(self, items: List[Dict[str, Any]], region: Dict[str, float], width: int, height: int) -> List[Dict[str, Any]]:
        x0 = int(width * region['left_pct'])
        x1 = int(width * region['right_pct'])
        y0 = int(height * region['top_pct'])
        y1 = int(height * region['bottom_pct'])
        filtered = []
        for item in items:
            cx = item.get('x') or item.get('cx', 0)
            cy = item.get('y') or item.get('cy', 0)
            if x0 <= cx <= x1 and y0 <= cy <= y1:
                item = dict(item)
                item['_region_match'] = region_name
                filtered.append(item)
        return filtered

    def suggest_fallback(self, app: str | None, query: str, previous_result: Dict[str, Any]) -> Dict[str, Any]:
        if not previous_result.get('ok'):
            fallback = {'strategy': 'ask_user', 'query': query}
            if app == 'spotify':
                fallback = {
                    'strategy': 'spotify_hotkey',
                    'action': 'ctrl+l',
                    'reason': 'No encontré eso en Spotify, voy directo a la barra de búsqueda con ctrl+L',
                }
            elif app == 'msedge':
                fallback = {
                    'strategy': 'edge_address_bar',
                    'action': 'ctrl+l',
                    'reason': 'No encontré eso en Edge, voy directo a la barra de direcciones con ctrl+L',
                }
            elif app == 'settings':
                fallback = {
                    'strategy': 'settings_sidebar',
                    'reason': 'No encontré eso en Settings, puedo abrir el menú lateral o usar la barra de búsqueda',
                }
            return fallback
        return {'strategy': 'none'}
