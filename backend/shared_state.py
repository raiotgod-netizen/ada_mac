import json
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = ROOT_DIR / "shared_state"
IDENTITY_PATH = SHARED_DIR / "identity.json"
MEMORY_PATH = SHARED_DIR / "memory.json"
PREFERENCES_PATH = SHARED_DIR / "preferences.json"
RULES_PATH = SHARED_DIR / "learned_rules.json"
JOURNAL_PATH = SHARED_DIR / "journal.jsonl"

DEFAULTS = {
    IDENTITY_PATH: {
        "name": "A.D.A.",
        "acronym": "Advanced Digital Assistant",
        "language": "es"
    },
    MEMORY_PATH: {
        "assistant_name": "A.D.A.",
        "summary": [],
        "preferences": {},
        "todos": []
    },
    PREFERENCES_PATH: {
        "language": "es",
        "address_user_as": "se?or",
        "response_style": "concisa, humana, técnica cuando haga falta",
        "automation_level": "assistive"
    },
    RULES_PATH: {
        "rules": []
    }
}


def ensure_shared_state():
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    for path, default in DEFAULTS.items():
        if not path.exists():
            write_json(path, default)
    if not JOURNAL_PATH.exists():
        JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        JOURNAL_PATH.write_text("", encoding='utf-8')


def read_json(path: Path, default: Dict[str, Any]):
    ensure_shared_state()
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return json.loads(json.dumps(default))


def write_json(path: Path, data: Dict[str, Any]):
    ensure_shared_state()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_identity():
    return read_json(IDENTITY_PATH, DEFAULTS[IDENTITY_PATH])


def get_memory():
    return read_json(MEMORY_PATH, DEFAULTS[MEMORY_PATH])
