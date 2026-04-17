from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from vision_context import VisionContext
from visual_memory import VisualMemory
from visual_playbook import VisualPlaybook


# ── Condition types ──────────────────────────────────────────────────────────
CONDITION_TRIGGERS = {
    'si_ves': 'visual_match',       # if you see X
    'si_detectas': 'visual_match',  # if you detect X
    'cuando_ves': 'visual_match',   # when you see X
    'al_ver': 'visual_match',       # upon seeing X
    'si_aparece': 'visual_match',  # if X appears
    'si_está': 'visual_match',     # if X is present
    'si_no_ves': 'visual_miss',    # if you don't see X
    'si_no_detectas': 'visual_miss',
}

# ── Action tokens ────────────────────────────────────────────────────────────────
ACTION_ALIASES = {
    'click': 'click',
    'haz_click': 'click',
    'clic': 'click',
    'clicken': 'click',
    'presiona': 'click',
    'apriet': 'click',
    'type': 'type',
    'escribir': 'type',
    'escribe': 'type',
    'escribí': 'type',
    'ingresar': 'type',
    'enter': 'type',
    'enter text': 'type',
    'scroll': 'scroll',
    'desplazar': 'scroll',
    'bajar': 'scroll',
    'subir': 'scroll',
    'scroll_up': 'scroll_up',
    'scroll_down': 'scroll_down',
    'scroll_left': 'scroll_left',
    'scroll_right': 'scroll_right',
}


class VisualActionResolver:
    SEMANTIC_ALIASES = {
        'buscar': ['search_bar', 'input_field', 'top_bar_control'],
        'search': ['search_bar', 'input_field', 'top_bar_control'],
        'barra': ['search_bar', 'input_field', 'top_bar_control'],
        'input': ['input_field', 'search_bar'],
        'campo': ['input_field', 'search_bar'],
        'boton': ['button', 'confirm_button', 'dismiss_button'],
        'botón': ['button', 'confirm_button', 'dismiss_button'],
        'guardar': ['confirm_button', 'button'],
        'cerrar': ['dismiss_button', 'button'],
        'close': ['dismiss_button', 'button'],
        'ok': ['confirm_button', 'button'],
    }

    def __init__(self, vision_dir: str | Path):
        self.vision_dir = Path(vision_dir)
        self.vision = VisionContext()
        self.memory = VisualMemory(self.vision_dir)
        self.playbook = VisualPlaybook()
        self.MIN_CONFIDENCE = 0.10

    def _latest_vision_path(self) -> str | None:
        if not self.vision_dir.exists():
            return None
        candidates = [p for p in self.vision_dir.glob('*') if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}]
        if not candidates:
            return None
        return str(max(candidates, key=lambda p: p.stat().st_mtime))

    def _semantic_preferences(self, query_l: str) -> List[str]:
        prefs: List[str] = []
        for token in query_l.split():
            prefs.extend(self.SEMANTIC_ALIASES.get(token, []))
        return list(dict.fromkeys(prefs))

    def _context_key(self, observer_snapshot: Dict[str, Any] | None = None) -> str:
        active = ((observer_snapshot or {}).get('active_window') or {})
        process = str(active.get('process') or 'unknown').lower()
        title = str(active.get('title') or '').strip().lower()[:80]
        return f"{process}::{title}" if title else process

    def resolve(self, query: str, observer_snapshot: Dict[str, Any] | None = None, confidence_threshold: float = 0.52) -> Dict[str, Any]:
        query_l = (query or '').strip().lower()
        if not query_l:
            return {'ok': False, 'result': 'Falta texto o intención para resolver un objetivo visual.'}

        observer_snapshot = observer_snapshot or {}
        context_key = self._context_key(observer_snapshot)
        app = self.playbook.detect_app(observer_snapshot)
        vision_snapshot = self.vision.summarize_snapshot(self._latest_vision_path(), observer_snapshot)
        screen = vision_snapshot.get('screen') or {}
        width = screen.get('width', 1920)
        height = screen.get('height', 1080)
        matches: List[Dict[str, Any]] = []
        semantic_preferences = self._semantic_preferences(query_l)

        prior_coord = self.memory.get_successful_coordinate(context_key, query)
        if prior_coord:
            matches.append({
                'kind': 'action_history',
                'label': f'historial: {query}',
                'x': prior_coord[0],
                'y': prior_coord[1],
                'confidence': 0.82,
                'source': {'type': 'action_history'},
                'reason': 'coordenada validada por acción anterior exitosa',
            })

        # ── Per-app memory (app-aware recall, checked before generic OCR/UI) ──
        if app:
            app_recalled = self.memory.get_target_for_app(app, query_l)
            if app_recalled:
                matches.append({
                    'kind': 'app_memory',
                    'label': app_recalled.get('label') or query_l,
                    'x': app_recalled.get('x', 0),
                    'y': app_recalled.get('y', 0),
                    'confidence': 0.78,
                    'source': app_recalled,
                    'reason': f'target recordado para {app}',
                })

        recalled = self.memory.recall_target(context_key, query)
        if recalled:
            matches.append({
                'kind': 'visual_memory',
                'label': recalled.get('label') or query,
                'x': recalled.get('x', 0),
                'y': recalled.get('y', 0),
                'confidence': 0.61,
                'source': recalled,
                'reason': 'target recordado en este contexto visual',
            })

        playbook_hints = self.playbook.get_search_hints(app, query) if app else []

        for line in screen.get('ocr_lines', []) or []:
            text = str(line.get('text') or '')
            text_l = text.lower()
            if query_l in text_l or text_l in query_l:
                confidence = min(0.98, float(line.get('confidence', 0.5)) + 0.12)
                match = {
                    'kind': 'ocr_line',
                    'label': text,
                    'x': line.get('x', 0) + max(1, line.get('w', 0)) // 2,
                    'y': line.get('y', 0) + max(1, line.get('h', 0)) // 2,
                    'confidence': confidence,
                    'source': line,
                    'reason': 'coincidencia textual OCR',
                }
                if app:
                    region_name = self._best_region_for_line(line, app, width, height)
                    if region_name:
                        match['_app_region'] = region_name
                        match['confidence'] = min(0.97, confidence + 0.08)
                        match['reason'] = f'coincidencia OCR en región {region_name} de {app}'
                matches.append(match)

        for target in screen.get('ui_targets', []) or []:
            target_type = str(target.get('type') or '')
            nearby_text = str(target.get('nearby_text') or '')
            joined = f"{target_type} {nearby_text}".lower()
            confidence = float(target.get('confidence', 0.4))
            semantic_bonus = 0.0
            if semantic_preferences and target.get('semantic_role') in semantic_preferences:
                semantic_bonus += 0.2
            if query_l in joined or any(token in joined for token in query_l.split() if len(token) > 2):
                match = {
                    'kind': 'ui_target',
                    'label': nearby_text or target_type,
                    'x': target.get('cx', 0),
                    'y': target.get('cy', 0),
                    'confidence': min(0.97, confidence + semantic_bonus),
                    'source': target,
                    'reason': 'coincidencia por semántica de control y texto cercano',
                }
                if app and playbook_hints:
                    match['confidence'] = min(0.97, match['confidence'] + 0.07)
                    match['reason'] += f' (playbook: {app})'
                matches.append(match)

        if not matches and screen.get('suggested_targets'):
            for item in screen.get('suggested_targets', []):
                name = str(item.get('name') or '')
                reason = str(item.get('reason') or '')
                joined = f'{name} {reason}'.lower()
                if query_l in joined or any(token in joined for token in query_l.split() if len(token) > 2):
                    matches.append({
                        'kind': 'suggested_target',
                        'label': name,
                        'x': item.get('x', 0),
                        'y': item.get('y', 0),
                        'confidence': float(item.get('confidence', 0.45) or 0.45),
                        'source': item,
                        'reason': reason or 'coincidencia con target sugerido',
                    })

        matches.sort(key=lambda item: item.get('confidence', 0), reverse=True)
        best = matches[0] if matches else None
        threshold = max(confidence_threshold, self.MIN_CONFIDENCE)
        needs_confirmation = best and best.get('confidence', 0) < threshold
        if not best or needs_confirmation:
            fallback = self.playbook.suggest_fallback(app, query, {'ok': bool(best)})
            top_ocr = [l.get('text', '') for l in screen.get('ocr_lines', [])[:5]]
            return {
                'ok': False,
                'result': best.get('result') if best else f"No encontré un objetivo visual claro para '{query}'. Texto visible: {' | '.join(top_ocr)}",
                'confidence': best.get('confidence') if best else None,
                'needs_confirmation': needs_confirmation,
                'fallback_hint': fallback if not best else None,
                'playbook_app': app,
                'playbook_hints': playbook_hints,
                'vision': vision_snapshot,
                'matches': matches[:8],
            }

        self.memory.remember_target(context_key, query, best)
        # Also persist per-app memory for app-aware fast recall
        if app:
            self.memory.save_target_by_app(app, query_l, int(best.get('x', 0)), int(best.get('y', 0)), label=best.get('label', ''), kind=best.get('kind', ''))
        return {
            'ok': True,
            'result': f"Objetivo visual resuelto: {best.get('label')} en ({best.get('x')}, {best.get('y')}).",
            'target': best,
            'matches': matches[:8],
            'vision': vision_snapshot,
            'memory_context': context_key,
            'visual_memory': self.memory.snapshot(),
            'playbook_app': app,
            'playbook_hints': playbook_hints,
        }

    def _best_region_for_line(self, line: Dict[str, Any], app: str, width: int, height: int) -> str | None:
        lx = line.get('x', 0)
        ly = line.get('y', 0)
        region_names = ['search', 'address', 'sidebar', 'main', 'playback', 'message', 'prompt']
        for region_name in region_names:
            region = self.playbook.get_region_filter(app, region_name)
            if not region:
                continue
            x0 = int(width * region['left_pct'])
            x1 = int(width * region['right_pct'])
            y0 = int(height * region['top_pct'])
            y1 = int(height * region['bottom_pct'])
            if x0 <= lx <= x1 and y0 <= ly <= y1:
                return region_name
        return None

    # ── Compound / conditional action parser ──────────────────────────────────

    def parse_compound(self, query: str) -> Dict[str, Any] | None:
        """
        Detecta patrones tipo:
          "si ves [condición], hacé click en [target]"
          "si no ves [algo], ve a [target]"
          "cuando veas [cosa], [acción]"
        Devuelve None si no es compuesto (solo acción directa).
        """
        query_l = (query or '').strip().lower()

        # 1) Detect condition trigger
        condition_type = None
        condition_target = ''
        for token, ctype in CONDITION_TRIGGERS.items():
            if token in query_l:
                condition_type = ctype
                parts = query_l.split(token, 1)
                condition_target = parts[1].strip() if len(parts) > 1 else ''
                break

        if not condition_type:
            return None  # Not a compound pattern

        # 2) Split condition_target into condition_part and action_part
        rest = condition_target
        action_part = rest
        for sep in [', ', ' y ', ' entonces ', ' después ']:
            idx = rest.find(sep)
            if idx != -1:
                action_part = rest[idx + len(sep):]
                break
        else:
            # No simple separator — look for action verb
            for alias in ACTION_ALIASES:
                idx = rest.rfind(alias)
                if idx > 2:
                    action_part = rest[idx:]
                    break

        # 3) Identify action type from action_part
        action_l = action_part.strip().lower()
        action_type = None
        action_target = None
        for alias, atype in ACTION_ALIASES.items():
            if alias in action_l:
                action_type = atype
                for sep in [alias, ' en ', ' sobre ', ' la ', ' el ']:
                    idx = action_l.find(sep)
                    if idx != -1:
                        action_target = action_l[idx + len(sep):].strip().strip('.').strip()
                        break
                if not action_target:
                    action_target = action_part.replace(alias, '').strip().strip(',').strip()
                break

        if not action_type or not action_target:
            return None

        return {
            'is_compound': True,
            'condition_type': condition_type,
            'condition_target': condition_target.strip().strip('?').strip(),
            'action_type': action_type,
            'action_target': action_target,
            'original_query': query,
        }

    def _evaluate_condition(
        self,
        condition_type: str,
        condition_target: str,
        observer_snapshot: Dict[str, Any] | None = None,
    ) -> bool:
        """
        Evalúa si la condición visual se cumple con la pantalla actual.
        Para 'visual_match': verifica si encuentra condition_target en OCR/UI.
        Para 'visual_miss': verifica que NO esté presente.
        """
        observer_snapshot = observer_snapshot or {}
        context_key = self._context_key(observer_snapshot)
        vision_snapshot = self.vision.summarize_snapshot(self._latest_vision_path(), observer_snapshot)
        screen = vision_snapshot.get('screen') or {}
        target_l = (condition_target or '').strip().lower()

        found = False

        for line in screen.get('ocr_lines', []) or []:
            text = str(line.get('text') or '').lower()
            if target_l in text or text in target_l:
                found = True
                break

        if not found:
            for t in screen.get('ui_targets', []) or []:
                joined = f"{t.get('type', '')} {t.get('nearby_text', '')}".lower()
                if target_l in joined or any(token in joined for token in target_l.split() if len(token) > 2):
                    found = True
                    break

        if not found:
            recalled = self.memory.recall_target(context_key, target_l)
            if recalled:
                found = True

        if condition_type == 'visual_match':
            return found
        elif condition_type == 'visual_miss':
            return not found
        return False

    def execute_compound(
        self,
        query: str,
        observer_snapshot: Dict[str, Any] | None = None,
        dispatcher=None,
    ) -> Dict[str, Any]:
        """
        Parses and executes a compound/conditional visual action.
        dispatcher must expose: click_visual_target(target),
        type_into_visual_target(target, text), move_mouse(x, y), scroll(amount).
        Returns execution result dict.
        """
        parsed = self.parse_compound(query)
        if not parsed:
            return {'ok': False, 'result': f"No pude interpretar: '{query}"}

        condition_met = self._evaluate_condition(
            parsed['condition_type'],
            parsed['condition_target'],
            observer_snapshot,
        )

        if not condition_met:
            return {
                'ok': False,
                'result': f"Condición no cumplida: '{parsed['condition_target']}' no está visible.",
                'condition': parsed['condition_type'],
                'condition_target': parsed['condition_target'],
                'action_taken': False,
                'query': query,
            }

        # Condition passed — resolve and execute the action
        action_type = parsed['action_type']
        action_target = parsed['action_target']

        resolved = self.resolve(action_target, observer_snapshot or {})
        if not resolved.get('ok'):
            return {
                'ok': False,
                'result': f"Condición OK pero no pude resolver el objetivo: '{action_target}'",
                'condition': parsed['condition_type'],
                'condition_target': parsed['condition_target'],
                'action_taken': False,
                'query': query,
            }

        target = resolved.get('target', {})

        if dispatcher is None:
            return {
                'ok': True,
                'result': f"Condición cumplida. Acción '{action_type}' lista sobre '{action_target}' en ({target.get('x')}, {target.get('y')}).",
                'condition': parsed['condition_type'],
                'condition_target': parsed['condition_target'],
                'action_type': action_type,
                'target': target,
                'action_taken': True,
                'query': query,
            }

        try:
            if action_type == 'click':
                result = dispatcher.click_visual_target(target)
            elif action_type == 'type':
                result = dispatcher.type_into_visual_target(target, action_target)
            elif action_type == 'move':
                result = dispatcher.move_mouse(int(target.get('x', 0)), int(target.get('y', 0)))
            elif action_type == 'scroll':
                result = dispatcher.scroll(-450)
            elif action_type == 'scroll_up':
                result = dispatcher.scroll_up(450)
            elif action_type == 'scroll_down':
                result = dispatcher.scroll_down(450)
            elif action_type == 'scroll_left':
                result = dispatcher.scroll_left(450)
            elif action_type == 'scroll_right':
                result = dispatcher.scroll_right(450)
            else:
                result = {'ok': False, 'result': f"Acción '{action_type}' no soportada."}

            result['condition'] = parsed['condition_type']
            result['condition_target'] = parsed['condition_target']
            result['action_taken'] = True
            result['query'] = query
            return result
        except Exception as e:
            return {
                'ok': False,
                'result': f"Error ejecutando acción: {e}",
                'condition': parsed['condition_type'],
                'condition_target': parsed['condition_target'],
                'action_taken': False,
                'query': query,
            }

    # ── Public entry point (called from server.py) ────────────────────────────

    async def execute(self, query: str, observer_snapshot: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Entry point for server.py run_vision_action socket event.
        Supports both direct actions and compound/conditional ones.
        Tries execute_compound first, then falls back to resolve → click.
        """
        from desktop_automation import DesktopAutomation

        observer_snapshot = observer_snapshot or {}

        # Try compound / conditional first
        compound = self.parse_compound(query)
        if compound:
            dispatcher = DesktopAutomation()
            return self.execute_compound(query, observer_snapshot, dispatcher)

        # Direct resolve → click
        resolved = self.resolve(query, observer_snapshot or {})
        if not resolved.get('ok'):
            return resolved

        target = resolved.get('target', {})
        dispatcher = DesktopAutomation()
        click_result = dispatcher.click_visual_target(target)
        resolved['click_result'] = click_result
        return resolved
