from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from improvement_engine import ImprovementEngine


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SelfModificationRunner:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.engine = ImprovementEngine(self.workspace_root)
        self.log_path = self.workspace_root / "shared_state" / "self_modification_runs.json"
        if not self.log_path.exists():
            self.log_path.write_text(json.dumps({"items": []}, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_runs(self) -> Dict[str, Any]:
        try:
            return json.loads(self.log_path.read_text(encoding="utf-8"))
        except Exception:
            return {"items": []}

    def _save_runs(self, data: Dict[str, Any]):
        self.log_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _is_allowed_path(self, relative_path: str) -> bool:
        rel = relative_path.replace('\\', '/').lstrip('/')
        registry = self.engine.registry()
        if rel in set(registry.get('protected_files', [])):
            return False
        return any(rel == area or rel.startswith(f"{area}/") for area in registry.get('editable_areas', []))

    def _backup_file(self, file_path: Path) -> Path:
        backup_dir = self.workspace_root / 'shared_state' / 'self_mod_backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{file_path.name}.{int(datetime.now().timestamp())}.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def apply_text_replacements(self, title: str, changes: List[Dict[str, str]], validate: bool = True) -> Dict[str, Any]:
        applied = []
        backups = []
        errors = []

        for change in changes or []:
            relative_path = str(change.get('path') or '').replace('\\', '/')
            if not relative_path:
                errors.append('Cambio sin path.')
                continue
            if not self._is_allowed_path(relative_path):
                errors.append(f'Ruta protegida o no editable: {relative_path}')
                continue
            file_path = (self.workspace_root / relative_path).resolve()
            if not file_path.exists() or not file_path.is_file():
                errors.append(f'No existe el archivo: {relative_path}')
                continue
            old_text = change.get('old_text', '')
            new_text = change.get('new_text', '')
            if not old_text:
                errors.append(f'Falta old_text en {relative_path}')
                continue
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if old_text not in content:
                errors.append(f'No encontré el bloque a reemplazar en {relative_path}')
                continue
            backup_path = self._backup_file(file_path)
            backups.append({'path': relative_path, 'backup_path': str(backup_path)})
            updated = content.replace(old_text, new_text, 1)
            file_path.write_text(updated, encoding='utf-8')
            applied.append(relative_path)

        validation = self.engine.validate_project() if validate and applied else {"ok": True, "results": []}
        if applied and validate and not validation.get('ok', False):
            for item in backups:
                target = self.workspace_root / item['path']
                backup = Path(item['backup_path'])
                if backup.exists():
                    shutil.copy2(backup, target)
        ok = len(errors) == 0 and validation.get('ok', False if validate and applied else True)
        summary = f"Cambios aplicados: {len(applied)}" if applied else "Sin cambios aplicados"
        record = {
            'id': f"run-{int(datetime.now().timestamp())}",
            'title': title or 'auto_modification',
            'applied_files': applied,
            'errors': errors,
            'backups': backups,
            'validation': validation,
            'ok': ok,
            'created_at': now_iso(),
        }
        runs = self._load_runs()
        runs.setdefault('items', []).insert(0, record)
        self._save_runs(runs)
        if ok and applied:
            self.engine.record_applied_improvement(title or 'auto_modification', summary, applied)
        return {
            'ok': ok,
            'applied_files': applied,
            'errors': errors,
            'backups': backups,
            'validation': validation,
            'result': summary if ok else 'La auto-modificación no terminó limpia y se intentó rollback si hubo backups.',
        }

    def snapshot(self) -> Dict[str, Any]:
        runs = self._load_runs().get('items', [])
        return {
            'count': len(runs),
            'recent': runs[:10],
            'mode': self.engine.registry().get('policies', {}).get('mode', 'supervised'),
        }
