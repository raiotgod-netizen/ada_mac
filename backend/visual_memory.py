from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List


class VisualMemory:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.base_dir / 'visual_memory.json'

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {'contexts': {}}
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except Exception:
            return {'contexts': {}}

    def _save(self, data: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def remember_target(self, context_key: str, query: str, target: Dict[str, Any]) -> None:
        if not context_key or not query or not isinstance(target, dict):
            return
        data = self._load()
        contexts = data.setdefault('contexts', {})
        bucket = contexts.setdefault(context_key, {})
        bucket[query.strip().lower()] = {
            'query': query,
            'label': target.get('label'),
            'x': target.get('x'),
            'y': target.get('y'),
            'kind': target.get('kind'),
            'semantic_role': (target.get('source') or {}).get('semantic_role') if isinstance(target.get('source'), dict) else None,
            'reason': target.get('reason'),
        }
        self._save(data)

    def recall_target(self, context_key: str, query: str) -> Dict[str, Any] | None:
        if not context_key or not query:
            return None
        data = self._load()
        return (((data.get('contexts') or {}).get(context_key) or {}).get(query.strip().lower()))

    def snapshot(self) -> Dict[str, Any]:
        data = self._load()
        contexts = data.get('contexts') or {}
        sample: List[Dict[str, Any]] = []
        for ctx, items in list(contexts.items())[:6]:
            sample.append({'context': ctx, 'targets': list(items.values())[:4]})
        return {
            'contexts': len(contexts),
            'sample': sample,
        }

    def record_outcome(self, context_key: str, query: str, x: int, y: int, success: bool, app: str | None = None) -> None:
        if not context_key or not query:
            return
        data = self._load()
        outcomes = data.setdefault('action_outcomes', {})
        key = f"{context_key}|{query.strip().lower()}"
        entry = {
            'query': query,
            'x': x, 'y': y,
            'success': success,
            'app': app,
            'ts': time.time(),
        }
        history = outcomes.setdefault(key, [])
        history.insert(0, entry)
        outcomes[key] = history[:20]
        data['action_outcomes'] = outcomes
        self._save(data)

    def get_successful_coordinate(self, context_key: str, query: str) -> tuple[int, int] | None:
        data = self._load()
        outcomes: Dict = data.get('action_outcomes', {})
        key = f"{context_key}|{query.strip().lower()}"
        history: List = outcomes.get(key, [])
        for entry in history:
            if entry.get('success'):
                return entry.get('x'), entry.get('y')
        return None

    def get_outcome_stats(self, context_key: str, query: str) -> Dict[str, Any]:
        data = self._load()
        outcomes: Dict = data.get('action_outcomes', {})
        key = f"{context_key}|{query.strip().lower()}"
        history: List = outcomes.get(key, [])
        if not history:
            return {'attempts': 0, 'successes': 0, 'rate': 0.0}
        successes = sum(1 for e in history if e.get('success'))
        return {
            'attempts': len(history),
            'successes': successes,
            'rate': round(successes / len(history), 2),
            'last': history[0] if history else None,
        }

    # ── Per-app / per-window target memory ──────────────────────────────────

    def save_target_by_app(self, app: str, query: str, x: int, y: int, label: str = '', kind: str = '', window_title: str = '') -> None:
        """Persist a target memorised for a given app (and optionally window title)."""
        if not app or not query:
            return
        data = self._load()
        app_bucket = data.setdefault('app_memory', {})
        key = f"{app.lower()}::{window_title.strip().lower()[:80]}" if window_title else app.lower()
        bucket = app_bucket.setdefault(key, {})
        bucket[query.strip().lower()] = {
            'query': query,
            'label': label,
            'x': x,
            'y': y,
            'kind': kind,
            'app': app,
            'window_title': window_title,
            'ts': time.time(),
        }
        self._save(data)

    def get_target_for_app(self, app: str, query: str, window_title: str = '') -> Dict[str, Any] | None:
        """Recall a target for a specific app (and optionally window)."""
        if not app or not query:
            return None
        data = self._load()
        app_bucket = data.get('app_memory', {})
        if window_title:
            key = f"{app.lower()}::{window_title.strip().lower()[:80]}"
            found = ((app_bucket.get(key) or {}).get(query.strip().lower()))
            if found:
                return found
        found = ((app_bucket.get(app.lower()) or {}).get(query.strip().lower()))
        return found

    def get_all_targets_for_app(self, app: str) -> List[Dict[str, Any]]:
        """Return all memorised targets for an app across windows."""
        if not app:
            return []
        data = self._load()
        app_bucket = data.get('app_memory', {})
        results = []
        prefix = f"{app.lower()}::"
        for key, bucket in app_bucket.items():
            if not key.startswith(prefix):
                continue
            for entry in bucket.values():
                results.append(entry)
        return results

    def get_app_summary(self) -> Dict[str, Any]:
        """Return a summary of apps with memorised targets."""
        data = self._load()
        app_bucket = data.get('app_memory', {})
        summary = {}
        for key, bucket in app_bucket.items():
            app_name = key.split('::')[0] if '::' in key else key
            entries = list(bucket.values())
            if app_name not in summary:
                summary[app_name] = {'count': 0, 'windows': set(), 'queries': set()}
            summary[app_name]['count'] += len(entries)
            for e in entries:
                if e.get('window_title'):
                    summary[app_name]['windows'].add(e['window_title'])
                summary[app_name]['queries'].add(e.get('query', ''))
        for app_name in summary:
            summary[app_name]['windows'] = list(summary[app_name]['windows'])
            summary[app_name]['queries'] = list(summary[app_name]['queries'])
        return summary
