from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_AUTOMATION_MACROS = [
    {
        "name": "buscar_en_google",
        "description": "Enfoca la barra del navegador activo, escribe una búsqueda y la ejecuta.",
        "steps": [
            {"action": "press_hotkey", "keys": ["ctrl", "l"]},
            {"action": "type_text", "text": "", "press_enter": True}
        ]
    },
    {
        "name": "abrir_youtube_busqueda",
        "description": "Abre YouTube en el navegador predeterminado.",
        "steps": [
            {"action": "open_url", "url": "https://www.youtube.com"}
        ]
    },
    {
        "name": "buscar_en_youtube_navegador_activo",
        "description": "Enfoca la barra o caja de búsqueda y lanza una búsqueda en YouTube usando el navegador activo.",
        "steps": [
            {"action": "press_hotkey", "keys": ["ctrl", "l"]},
            {"action": "type_text", "text": "https://www.youtube.com/results?search_query=", "press_enter": False}
        ]
    },
    {
        "name": "abrir_primer_resultado",
        "description": "Navega con teclado al primer resultado visible y lo abre.",
        "steps": [
            {"action": "press_hotkey", "keys": ["tab"]},
            {"action": "press_hotkey", "keys": ["tab"]},
            {"action": "press_hotkey", "keys": ["enter"]}
        ]
    },
    {
        "name": "buscar_y_abrir_primer_video_youtube",
        "description": "Abre YouTube, busca y deja lista la apertura del primer video con navegación básica.",
        "steps": [
            {"action": "open_url", "url": "https://www.youtube.com"},
            {"action": "wait", "seconds": 1.5},
            {"action": "press_hotkey", "keys": ["/"]},
            {"action": "type_text", "text": "", "press_enter": True},
            {"action": "wait", "seconds": 1.5},
            {"action": "press_hotkey", "keys": ["tab"]},
            {"action": "press_hotkey", "keys": ["enter"]}
        ]
    }
]


class GlobalProjectMemory:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.projects_dir = self.workspace_root / "projects"
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.shared_dir / "global_project_memory.json"
        if not self.registry_path.exists():
            self._save({"projects": [], "improvements": [], "automation_macros": []})
            self._seed_default_macros()

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {"projects": [], "improvements": [], "automation_macros": []}

    def _save(self, data: Dict[str, Any]):
        self.registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def rebuild(self) -> Dict[str, Any]:
        projects: List[Dict[str, Any]] = []
        improvements: List[Dict[str, Any]] = []

        if self.projects_dir.exists():
            for project_dir in sorted([p for p in self.projects_dir.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
                item = {
                    "name": project_dir.name,
                    "path": str(project_dir),
                    "documents": len(list((project_dir / "documents").glob("*"))) if (project_dir / "documents").exists() else 0,
                    "screenshots": len(list((project_dir / "screenshots").glob("*"))) if (project_dir / "screenshots").exists() else 0,
                    "cad": len(list((project_dir / "cad").glob("*"))) if (project_dir / "cad").exists() else 0,
                    "improvements": 0,
                }

                improvements_file = project_dir / "improvements" / "improvements.json"
                if improvements_file.exists():
                    try:
                        data = json.loads(improvements_file.read_text(encoding="utf-8"))
                        local_items = data.get("items", [])
                        item["improvements"] = len(local_items)
                        for imp in local_items[:50]:
                            improvements.append({
                                "project": project_dir.name,
                                "id": imp.get("id"),
                                "title": imp.get("title"),
                                "status": imp.get("status"),
                                "goal": imp.get("goal", ""),
                                "updated_at": imp.get("updated_at"),
                            })
                    except Exception:
                        pass

                projects.append(item)

        registry = self._load()
        updated = {
            "projects": projects,
            "improvements": improvements[:200],
            "automation_macros": registry.get("automation_macros", []),
        }
        self._save(updated)
        return updated

    def snapshot(self) -> Dict[str, Any]:
        data = self.rebuild()
        return {
            "projects_count": len(data.get("projects", [])),
            "recent_projects": data.get("projects", [])[:10],
            "improvements_count": len(data.get("improvements", [])),
            "recent_improvements": data.get("improvements", [])[:10],
            "automation_macros": data.get("automation_macros", [])[:20],
        }

    def save_macro(self, name: str, steps: List[Dict[str, Any]], description: str = "") -> Dict[str, Any]:
        data = self._load()
        macros = [m for m in data.get("automation_macros", []) if m.get("name") != name]
        macro = {
            "name": (name or "macro").strip(),
            "description": (description or "").strip(),
            "steps": steps,
        }
        macros.insert(0, macro)
        data["automation_macros"] = macros[:100]
        self._save(data)
        return {"ok": True, "result": f"Macro guardada: {macro['name']}", "macro": macro}

    def get_macro(self, name: str) -> Dict[str, Any] | None:
        data = self._load()
        target = (name or "").strip().lower()
        for macro in data.get("automation_macros", []):
            if str(macro.get("name", "")).strip().lower() == target:
                return macro
        return None

    def _seed_default_macros(self):
        data = self._load()
        if data.get("automation_macros"):
            return
        data["automation_macros"] = list(DEFAULT_AUTOMATION_MACROS)
        self._save(data)

    def ensure_default_macros(self) -> Dict[str, Any]:
        data = self._load()
        existing = {str(item.get("name", "")).strip().lower() for item in data.get("automation_macros", [])}
        added = []
        for macro in DEFAULT_AUTOMATION_MACROS:
            if macro["name"].strip().lower() not in existing:
                data.setdefault("automation_macros", []).append(macro)
                added.append(macro["name"])
        if added:
            self._save(data)
        return {"ok": True, "result": f"Macros base verificadas. Añadidas: {', '.join(added) if added else 'ninguna'}", "added": added}

    def list_macros(self) -> List[Dict[str, Any]]:
        return self._load().get("automation_macros", [])
