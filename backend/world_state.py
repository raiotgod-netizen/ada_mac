from __future__ import annotations

from typing import Any, Dict


class WorldState:
    def build(
        self,
        runtime: Dict[str, Any],
        project: Dict[str, Any],
        memory: Dict[str, Any],
        system_observer: Dict[str, Any],
        global_memory: Dict[str, Any],
        queue: Dict[str, Any],
        vision: Dict[str, Any] | None = None,
        runtime_memory: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "runtime_mode": runtime.get("mode", "idle"),
            "project": {
                "current": project.get("current"),
                "documents": project.get("documents_count", 0),
                "screenshots": project.get("screenshots_count", 0),
                "improvements": project.get("improvements_count", 0),
            },
            "memory": {
                "rules": memory.get("rules_count", 0),
                "journal_events": len(memory.get("recent_journal", [])),
                "projects_known": global_memory.get("projects_count", 0),
                "improvements_known": global_memory.get("improvements_count", 0),
                "macros_known": len(global_memory.get("automation_macros", [])),
                "runtime_capabilities": len((runtime_memory or {}).get("capabilities", [])),
                "runtime_improvements": len((runtime_memory or {}).get("improvements", [])),
            },
            "desktop": {
                "active_window": (system_observer.get("active_window") or {}).get("title"),
                "windows": (system_observer.get("windows") or {}).get("count", 0),
                "browser_windows": (system_observer.get("browser_windows") or {}).get("count", 0),
                "processes": (system_observer.get("processes") or {}).get("count", 0),
            },
            "queue": {
                "running": (queue.get("counts") or {}).get("running", 0),
                "queued": (queue.get("counts") or {}).get("queued", 0),
                "failed": (queue.get("counts") or {}).get("failed", 0),
            },
            "vision": vision or {
                "available": False,
                "summary": "Sin contexto visual aún.",
            },
        }
