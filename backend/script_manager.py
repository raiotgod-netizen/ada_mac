import json
import subprocess
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "custom_scripts"
REGISTRY_PATH = SCRIPTS_DIR / "scripts_registry.json"


def ensure_registry():
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        REGISTRY_PATH.write_text(json.dumps({"scripts": []}, indent=2, ensure_ascii=False), encoding='utf-8')


def load_registry() -> Dict[str, Any]:
    ensure_registry()
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {"scripts": []}


def save_registry(data: Dict[str, Any]):
    ensure_registry()
    REGISTRY_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sanitize_name(name: str) -> str:
    safe = ''.join(c for c in name if c.isalnum() or c in ('-', '_', ' ')).strip().replace(' ', '_')
    return safe or 'script'


def create_script(name: str, description: str, content: str, language: str = 'python', args_schema=None, permission_level: str = 'normal'):
    ensure_registry()
    safe_name = sanitize_name(name)
    ext = '.py' if language.lower() == 'python' else '.txt'
    script_path = SCRIPTS_DIR / f"{safe_name}{ext}"
    script_path.write_text(content, encoding='utf-8')

    registry = load_registry()
    scripts = registry.setdefault('scripts', [])
    scripts = [s for s in scripts if s.get('name') != name]
    scripts.append({
        'name': name,
        'safe_name': safe_name,
        'description': description,
        'language': language,
        'path': str(script_path),
        'args_schema': args_schema or [],
        'permission_level': permission_level
    })
    registry['scripts'] = scripts
    save_registry(registry)
    return {"ok": True, "result": f"Script '{name}' creado en {script_path}"}


def list_scripts():
    registry = load_registry()
    scripts = registry.get('scripts', [])
    if not scripts:
        return {"ok": True, "result": "No hay scripts registrados."}
    summary = '\n'.join([f"- {s['name']}: {s.get('description', '')}" for s in scripts])
    return {"ok": True, "result": summary}


def run_script(name: str, args=None):
    registry = load_registry()
    scripts = registry.get('scripts', [])
    match = next((s for s in scripts if s.get('name') == name or s.get('safe_name') == name), None)
    if not match:
        return {"ok": False, "result": f"No existe script con nombre '{name}'"}

    path = Path(match['path'])
    if not path.exists():
        return {"ok": False, "result": f"El archivo del script no existe: {path}"}

    if match.get('language', 'python').lower() != 'python':
        return {"ok": False, "result": "Solo se soporta ejecución de scripts Python por ahora."}

    try:
        argv = ['python', str(path)] + list(args or [])
        proc = subprocess.run(
            argv,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=60
        )
        output = (proc.stdout or '') + ('\n' + proc.stderr if proc.stderr else '')
        output = output.strip()[:12000]
        return {"ok": proc.returncode == 0, "result": output or f"Script ejecutado con código {proc.returncode}"}
    except Exception as e:
        return {"ok": False, "result": f"Error ejecutando script: {e}"}


def get_scripts_registry():
    registry = load_registry()
    return registry.get('scripts', [])
