from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from runtime_memory import RuntimeMemory


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_REGISTRY = {
    "editable_areas": [
        "backend",
        "src",
        "electron",
        "shared_state"
    ],
    "protected_files": [],  # FULL AUTONOMY — no files are protected
    "validation_commands": [
        "python -m py_compile backend\\server.py backend\\ada.py",
        "npm run build"
    ],
    "policies": {
        "mode": "autonomous",
        "require_confirmation_for": []
    }
}


class ImprovementEngine:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.shared_dir / "improvement_registry.json"
        self.history_path = self.shared_dir / "improvement_engine_history.json"
        self.runtime_memory = RuntimeMemory(self.workspace_root)
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps(DEFAULT_REGISTRY, indent=2, ensure_ascii=False), encoding="utf-8")
        if not self.history_path.exists():
            self.history_path.write_text(json.dumps({"items": []}, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return default

    def _save_json(self, path: Path, data: Dict[str, Any]):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def registry(self) -> Dict[str, Any]:
        return self._load_json(self.registry_path, DEFAULT_REGISTRY)

    def analyze_target(self, goal: str) -> Dict[str, Any]:
        text = (goal or "").lower()
        areas = []
        if any(token in text for token in ["correo", "gmail", "email", "adjunto"]):
            areas.extend(["backend/email_agent.py", "backend/file_agent.py", "backend/server.py"])
        if any(token in text for token in ["pantalla", "screen", "visión", "vision", "mouse", "click"]):
            areas.extend(["backend/desktop_automation.py", "backend/vision_context.py", "src/components/SystemWindow.jsx"])
        if any(token in text for token in ["memoria", "mejora", "self", "auto"]):
            areas.extend(["backend/runtime_memory.py", "backend/agent_core.py", "backend/policy_engine.py"])
        risk = "medium" if any(token in text for token in ["policy", "seguridad", "autonom", "permiso"]) else "low"
        return {
            "ok": True,
            "goal": goal,
            "suggested_files": list(dict.fromkeys(areas))[:12],
            "risk": risk,
            "mode": self.registry().get("policies", {}).get("mode", "supervised"),
            "result": f"Análisis de mejora listo con {len(list(dict.fromkeys(areas)))} archivos sugeridos."
        }

    def propose_change(self, title: str, goal: str, files: List[str] | None = None) -> Dict[str, Any]:
        item = {
            "id": f"eng-{int(datetime.now().timestamp())}",
            "title": (title or "Mejora propuesta").strip(),
            "goal": (goal or "").strip(),
            "files": files or [],
            "status": "proposed",
            "created_at": now_iso(),
        }
        history = self._load_json(self.history_path, {"items": []})
        history.setdefault("items", []).insert(0, item)
        self._save_json(self.history_path, history)
        return {"ok": True, "item": item, "result": f"Propuesta de mejora creada: {item['id']}"}

    def validate_project(self) -> Dict[str, Any]:
        commands = self.registry().get("validation_commands", [])
        results = []
        overall_ok = True
        for cmd in commands:
            try:
                completed = subprocess.run(cmd, cwd=str(self.workspace_root), shell=True, capture_output=True, text=True, timeout=240)
                output = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()[:4000]
                ok = completed.returncode == 0
                overall_ok = overall_ok and ok
                results.append({"command": cmd, "ok": ok, "output": output})
            except Exception as e:
                overall_ok = False
                results.append({"command": cmd, "ok": False, "output": str(e)})
        return {"ok": overall_ok, "results": results, "result": "Validación completada."}

    def record_applied_improvement(self, title: str, summary: str, files: List[str] | None = None) -> Dict[str, Any]:
        history = self._load_json(self.history_path, {"items": []})
        item = {
            "id": f"applied-{int(datetime.now().timestamp())}",
            "title": title,
            "summary": summary,
            "files": files or [],
            "status": "applied",
            "created_at": now_iso(),
        }
        history.setdefault("items", []).insert(0, item)
        self._save_json(self.history_path, history)
        runtime = self.runtime_memory.ensure_defaults()
        improvements = list(runtime.get("improvements", []))
        if title not in improvements:
            improvements.append(title)
            runtime["improvements"] = improvements[:50]
            self.runtime_memory._save(runtime)
        return {"ok": True, "item": item, "result": f"Mejora aplicada registrada: {title}"}

    def snapshot(self) -> Dict[str, Any]:
        history = self._load_json(self.history_path, {"items": []})
        registry = self.registry()
        return {
            "mode": registry.get("policies", {}).get("mode", "supervised"),
            "editable_areas": registry.get("editable_areas", []),
            "protected_files": registry.get("protected_files", []),
            "validation_commands": registry.get("validation_commands", []),
            "recent": history.get("items", [])[:10],
        }
