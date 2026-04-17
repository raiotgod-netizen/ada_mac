from datetime import datetime, timezone
from typing import Any, Dict, List
import uuid


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskQueue:
    def __init__(self):
        self._tasks: List[Dict[str, Any]] = []

    def create_task(self, kind: str, title: str, payload: Dict[str, Any] | None = None, source: str = "user"):
        task = {
            "id": f"task-{uuid.uuid4().hex[:8]}",
            "kind": kind,
            "title": title,
            "source": source,
            "payload": payload or {},
            "status": "queued",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "result": None,
            "error": None,
        }
        self._tasks.insert(0, task)
        self._tasks = self._tasks[:100]
        return task

    def update_task(self, task_id: str, status: str, result: Any = None, error: str | None = None):
        for task in self._tasks:
            if task["id"] == task_id:
                task["status"] = status
                task["updated_at"] = now_iso()
                if result is not None:
                    task["result"] = result
                if error is not None:
                    task["error"] = error
                return task
        return None

    def snapshot(self):
        counts = {
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }
        for task in self._tasks:
            if task["status"] in counts:
                counts[task["status"]] += 1
        return {
            "counts": counts,
            "recent": [dict(task) for task in self._tasks[:15]],
        }
