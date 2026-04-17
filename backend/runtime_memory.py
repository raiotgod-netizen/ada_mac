from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_RUNTIME_MEMORY = {
    "capabilities": [
        "memoria global persistente",
        "agent core supervisado",
        "observación del sistema",
        "automatización de escritorio",
        "routines con scheduling",
        "auditoría defensiva",
        "visión contextual",
        "control web local guiado",
        "correo Gmail integrado",
        "observación y memoria Bluetooth local",
        "motor de auto-mejora supervisada",
        "runner de auto-modificación local supervisada"
    ],
    "improvements": [
        "arranque estable con puertos dinámicos",
        "modo local_only en vez de degraded",
        "lazy loading de módulos pesados",
        "desacople de CadViewport3D",
        "web agent view ya no interfiere automáticamente",
        "envío de correo no bloquea el loop principal",
        "macros web base para Google y YouTube",
        "clic guiado por visión con confirmación",
        "inventario Bluetooth con memoria de dispositivos conocidos",
        "pipeline de auto-mejora con validación y registro persistente",
        "aplicación controlada de parches locales con validación"
    ],
    "known_issues": [
        "CadViewport3D sigue siendo un chunk pesado aislado",
        "la visión guiada actual es heurística, no detección semántica completa"
    ],
    "policies": [
        "acciones sensibles requieren supervisión o confirmación",
        "no ejecutar automatización ciega de alto riesgo",
        "preferir control local defensivo sobre acciones ofensivas"
    ],
    "recommended_flows": [
        "usar macros web para búsquedas repetitivas",
        "usar visión guiada antes de clics en web",
        "usar routines para tareas periódicas supervisadas",
        "usar system observer para enfocar la ventana correcta antes de automatizar",
        "usar improvement engine para proponer, validar y registrar mejoras antes de consolidarlas"
    ]
}


class RuntimeMemory:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.shared_dir / "ada_runtime_memory.json"
        if not self.path.exists():
            self._save(dict(DEFAULT_RUNTIME_MEMORY))

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return dict(DEFAULT_RUNTIME_MEMORY)

    def _save(self, data: Dict[str, Any]):
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def ensure_defaults(self) -> Dict[str, Any]:
        data = self._load()
        changed = False
        for key, values in DEFAULT_RUNTIME_MEMORY.items():
            existing = list(data.get(key, [])) if isinstance(data.get(key), list) else []
            for item in values:
                if item not in existing:
                    existing.append(item)
                    changed = True
            data[key] = existing
        if changed:
            self._save(data)
        return data

    def snapshot(self) -> Dict[str, Any]:
        data = self.ensure_defaults()
        return {
            "capabilities": data.get("capabilities", [])[:20],
            "improvements": data.get("improvements", [])[:30],
            "known_issues": data.get("known_issues", [])[:20],
            "policies": data.get("policies", [])[:20],
            "recommended_flows": data.get("recommended_flows", [])[:20],
        }
