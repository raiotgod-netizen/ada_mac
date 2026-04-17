from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ImprovementManager:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.base_dir / "improvements.json"
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps({"items": []}, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {"items": []}

    def _save(self, data: Dict[str, Any]):
        self.registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def create_proposal(self, title: str, goal: str, implementation_notes: str = "", requested_by: str = "user") -> dict:
        data = self._load()
        item = {
            "id": f"imp-{len(data.get('items', [])) + 1:04d}",
            "title": title.strip() or "Mejora sin título",
            "goal": goal.strip(),
            "implementation_notes": implementation_notes.strip(),
            "status": "proposed",
            "requested_by": requested_by,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        data.setdefault("items", []).insert(0, item)
        self._save(data)
        self._write_markdown(item)
        return {"ok": True, "item": item, "result": f"Mejora registrada: {item['id']} - {item['title']}"}

    def mark_status(self, improvement_id: str, status: str, notes: str = "") -> dict:
        data = self._load()
        for item in data.get("items", []):
            if item.get("id") == improvement_id:
                item["status"] = status
                item["updated_at"] = now_iso()
                if notes:
                    item["implementation_notes"] = (item.get("implementation_notes", "") + "\n" + notes).strip()
                self._save(data)
                self._write_markdown(item)
                return {"ok": True, "item": item, "result": f"Mejora {improvement_id} actualizada a {status}"}
        return {"ok": False, "result": f"No existe la mejora {improvement_id}"}

    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._load().get("items", [])[:limit]

    def _write_markdown(self, item: Dict[str, Any]):
        md_path = self.base_dir / f"{item['id']}_{self._slug(item['title'])}.md"
        content = [
            f"# {item['title']}",
            "",
            f"- ID: {item['id']}",
            f"- Estado: {item['status']}",
            f"- Solicitado por: {item['requested_by']}",
            f"- Creado: {item['created_at']}",
            f"- Actualizado: {item['updated_at']}",
            "",
            "## Objetivo",
            item.get("goal", ""),
            "",
            "## Notas de implementación",
            item.get("implementation_notes", "") or "(sin notas)",
            "",
        ]
        md_path.write_text("\n".join(content), encoding="utf-8")

    def _slug(self, text: str) -> str:
        return "".join(c for c in text if c.isalnum() or c in ("-", "_", " ")).strip().replace(" ", "_")[:50] or "mejora"
