from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
from pathlib import Path
import json
import uuid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RoutineManager:
    def __init__(self, workspace_root: str | Path | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else None
        self._path = None
        if self.workspace_root:
            shared_dir = self.workspace_root / 'shared_state'
            shared_dir.mkdir(parents=True, exist_ok=True)
            self._path = shared_dir / 'routine_registry.json'
        self._routines: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self._path or not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding='utf-8'))
            items = data.get('items', [])
            return items if isinstance(items, list) else []
        except Exception:
            return []

    def _save(self):
        if not self._path:
            return
        self._path.write_text(json.dumps({'items': self._routines}, indent=2, ensure_ascii=False), encoding='utf-8')

    def _compute_next_run_at(self, interval_seconds: int, from_dt: datetime | None = None) -> str:
        base = from_dt or datetime.now(timezone.utc)
        return (base + timedelta(seconds=max(10, int(interval_seconds or 300)))).isoformat()

    def create_routine(self, name: str, goal: str, interval_seconds: int = 300, enabled: bool = True, metadata: Dict[str, Any] | None = None, schedule_type: str = "interval"):
        normalized_interval = max(10, int(interval_seconds or 300))
        routine = {
            "id": f"routine-{uuid.uuid4().hex[:8]}",
            "name": name,
            "goal": goal,
            "schedule_type": schedule_type,
            "interval_seconds": normalized_interval,
            "enabled": enabled,
            "metadata": metadata or {},
            "status": "scheduled" if enabled else "disabled",
            "last_run_at": None,
            "next_run_at": self._compute_next_run_at(normalized_interval) if enabled else None,
            "last_result": None,
            "last_error": None,
            "run_count": 0,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        self._routines.insert(0, routine)
        self._routines = self._routines[:50]
        self._save()
        return routine

    def update_routine(self, routine_id: str, **changes):
        for routine in self._routines:
            if routine["id"] == routine_id:
                routine.update({k: v for k, v in changes.items() if v is not None})
                routine["status"] = "scheduled" if routine.get("enabled") else "disabled"
                if routine.get("enabled") and not routine.get("next_run_at"):
                    routine["next_run_at"] = self._compute_next_run_at(routine.get("interval_seconds", 300))
                if not routine.get("enabled"):
                    routine["next_run_at"] = None
                routine["updated_at"] = now_iso()
                self._save()
                return routine
        return None

    def record_run(self, routine_id: str, result: str | None = None, error: str | None = None):
        for routine in self._routines:
            if routine["id"] == routine_id:
                now = datetime.now(timezone.utc)
                routine["last_run_at"] = now.isoformat()
                routine["updated_at"] = now_iso()
                routine["run_count"] = int(routine.get("run_count", 0)) + 1
                routine["status"] = "error" if error else "scheduled"
                routine["next_run_at"] = self._compute_next_run_at(routine.get("interval_seconds", 300), now) if routine.get("enabled") else None
                if result is not None:
                    routine["last_result"] = result
                    routine["last_error"] = None
                if error is not None:
                    routine["last_error"] = error
                self._save()
                return routine
        return None

    def get_due_routines(self) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        due = []
        for routine in self._routines:
            if not routine.get("enabled"):
                continue
            next_run_at = routine.get("next_run_at")
            if not next_run_at:
                continue
            try:
                next_dt = datetime.fromisoformat(next_run_at)
                if next_dt <= now:
                    due.append(dict(routine))
            except Exception:
                continue
        return due

    def list_routines(self):
        return [dict(item) for item in self._routines]

    def mark_running(self, routine_id: str):
        for routine in self._routines:
            if routine['id'] == routine_id:
                routine['status'] = 'running'
                routine['updated_at'] = now_iso()
                self._save()
                return routine
        return None

    def snapshot(self) -> Dict[str, Any]:
        due = self.get_due_routines()
        return {
            "count": len(self._routines),
            "enabled": len([r for r in self._routines if r.get("enabled")]),
            "due": len(due),
            "items": [dict(item) for item in self._routines[:15]],
        }
