from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_SKILL_MANIFESTS = [
    {
        "id": "memory",
        "name": "Memoria persistente",
        "description": "Gestiona memoria global, runtime memory y contexto persistente.",
        "scope": "core",
        "enabled": True,
    },
    {
        "id": "desktop",
        "name": "Control de escritorio",
        "description": "Automatización local de mouse, teclado, ventanas y archivos.",
        "scope": "local",
        "enabled": True,
    },
    {
        "id": "vision",
        "name": "Visión contextual",
        "description": "Resumen visual, pistas de acción y guía heurística de pantalla.",
        "scope": "local",
        "enabled": True,
    },
    {
        "id": "email",
        "name": "Correo Gmail",
        "description": "Envío de correo, adjuntos y preparación de archivos recientes.",
        "scope": "local",
        "enabled": True,
    },
    {
        "id": "improvement",
        "name": "Auto-mejora supervisada",
        "description": "Análisis, propuesta, validación y aplicación local de mejoras.",
        "scope": "core",
        "enabled": True,
    }
]


class SkillRegistry:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.shared_dir / "skill_registry.json"
        if not self.path.exists():
            self._save({"skills": DEFAULT_SKILL_MANIFESTS})

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"skills": list(DEFAULT_SKILL_MANIFESTS)}

    def _save(self, data: Dict[str, Any]):
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def ensure_defaults(self) -> Dict[str, Any]:
        data = self._load()
        skills = data.get("skills", []) if isinstance(data.get("skills"), list) else []
        existing = {item.get("id") for item in skills}
        changed = False
        for skill in DEFAULT_SKILL_MANIFESTS:
            if skill.get("id") not in existing:
                skills.append(skill)
                changed = True
        data["skills"] = skills
        if changed:
            self._save(data)
        return data

    def set_enabled(self, skill_id: str, enabled: bool) -> Dict[str, Any]:
        data = self.ensure_defaults()
        for item in data.get("skills", []):
            if item.get("id") == skill_id:
                item["enabled"] = bool(enabled)
                self._save(data)
                return {"ok": True, "result": f"Skill {skill_id} actualizada.", "skill": item}
        return {"ok": False, "result": f"No existe la skill {skill_id}."}

    def is_enabled(self, skill_id: str) -> bool:
        data = self.ensure_defaults()
        for item in data.get("skills", []):
            if item.get("id") == skill_id:
                return bool(item.get("enabled", False))
        return False

    def register_skill(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        data = self.ensure_defaults()
        skills = data.get("skills", [])
        skill_id = str(manifest.get("id") or "").strip()
        if not skill_id:
            return {"ok": False, "result": "La skill necesita id."}
        if any(item.get("id") == skill_id for item in skills):
            return {"ok": False, "result": f"La skill {skill_id} ya existe."}
        record = {
            "id": skill_id,
            "name": manifest.get("name") or skill_id,
            "description": manifest.get("description") or "Skill dinámica registrada desde ADA.",
            "scope": manifest.get("scope") or "custom",
            "enabled": bool(manifest.get("enabled", True)),
            "tools": manifest.get("tools") or [],
            "source": manifest.get("source") or "dynamic",
        }
        skills.append(record)
        data["skills"] = skills
        self._save(data)
        return {"ok": True, "skill": record, "result": f"Skill {skill_id} registrada."}

    def snapshot(self) -> Dict[str, Any]:
        data = self.ensure_defaults()
        skills = data.get("skills", [])
        return {
            "skills": skills,
            "enabled": len([item for item in skills if item.get("enabled")]),
        }
