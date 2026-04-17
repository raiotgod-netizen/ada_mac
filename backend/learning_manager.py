import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = ROOT_DIR / 'shared_state'
PREFERENCES_PATH = SHARED_DIR / 'preferences.json'
RULES_PATH = SHARED_DIR / 'learned_rules.json'
JOURNAL_PATH = SHARED_DIR / 'journal.jsonl'
FEEDBACK_PATH = SHARED_DIR / 'feedback.json'


def _now():
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default):
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return json.loads(json.dumps(default))


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_preferences():
    return _read_json(PREFERENCES_PATH, {
        'language': 'es',
        'address_user_as': 'se?or',
        'response_style': 'concisa, humana, técnica cuando haga falta',
        'automation_level': 'assistive'
    })


def update_preferences(prefs: Dict[str, Any]):
    current = get_preferences()
    current.update(prefs or {})
    _write_json(PREFERENCES_PATH, current)
    append_journal('preferences_update', {'updated': prefs or {}})
    return current


def get_rules():
    return _read_json(RULES_PATH, {'rules': []})


def add_rule(rule_text: str, source: str = 'user'):
    data = get_rules()
    rules = data.setdefault('rules', [])
    entry = {
        'text': rule_text,
        'source': source,
        'created_at': _now()
    }
    rules.append(entry)
    _write_json(RULES_PATH, data)
    append_journal('rule_added', entry)
    return entry


def append_journal(event_type: str, payload: Dict[str, Any]):
    JOURNAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'timestamp': _now(),
        'event_type': event_type,
        'payload': payload
    }
    with open(JOURNAL_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def get_recent_journal(limit: int = 50) -> List[Dict[str, Any]]:
    if not JOURNAL_PATH.exists():
        return []
    lines = JOURNAL_PATH.read_text(encoding='utf-8', errors='ignore').splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def consolidate_memory():
    prefs = get_preferences()
    rules = get_rules().get('rules', [])
    recent = get_recent_journal(20)
    summary = {
        'preferences': prefs,
        'rules_count': len(rules),
        'recent_events': recent,
        'generated_at': _now()
    }
    append_journal('memory_consolidated', {'rules_count': len(rules), 'recent_events': len(recent)})
    return summary


# =============================================================================
# FEEDBACK & CONTINUOUS LEARNING
# =============================================================================

def _load_feedback() -> Dict[str, Any]:
    try:
        if FEEDBACK_PATH.exists():
            return json.loads(FEEDBACK_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {'entries': [], 'stats': {'good': 0, 'bad': 0, 'total': 0, 'by_category': {}}}


def _save_feedback(data: Dict[str, Any]):
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FEEDBACK_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def log_feedback(rating: str, category: str = 'general', note: str = '') -> Dict[str, Any]:
    """
    Registra feedback del usuario sobre una interacción.
    rating: 'good' | 'bad' | 'ok'
    category: categoría de la interacción (e.g. 'respuesta', 'tool', 'sugerencia', 'proactive')
    note: comentario opcional del usuario
    """
    data = _load_feedback()
    entry = {
        'rating': rating,
        'category': category,
        'note': note,
        'timestamp': _now()
    }
    data['entries'].append(entry)

    # Update stats
    data['stats']['total'] = len(data['entries'])
    data['stats'][rating] = data['stats'].get(rating, 0) + 1
    cat_stats = data['stats'].setdefault('by_category', {})
    cat_entry = cat_stats.setdefault(category, {'good': 0, 'bad': 0, 'ok': 0, 'total': 0})
    cat_entry[rating] = cat_entry.get(rating, 0) + 1
    cat_entry['total'] += 1

    _save_feedback(data)
    append_journal('feedback', entry)

    # Derive improvement rules from bad feedback
    if rating == 'bad' and note:
        _derive_rule_from_feedback(note)

    return {'ok': True, 'entry': entry, 'stats': data['stats']}


def _derive_rule_from_feedback(note: str):
    """If user gives negative feedback with a note, store it as a learned rule."""
    if len(note) < 5 or len(note) > 300:
        return
    # Check it's not already a rule
    rules = get_rules().get('rules', [])
    for r in rules:
        if note.lower() in r.get('text', '').lower():
            return
    add_rule(f"EVITAR: {note.strip()}", source='negative_feedback')


def get_feedback_stats() -> Dict[str, Any]:
    """Devuelve estadísticas de feedback acumulado."""
    data = _load_feedback()
    stats = data.get('stats', {})
    total = stats.get('total', 0)
    if total == 0:
        return {'total': 0, 'good_rate': 0, 'bad_rate': 0, 'by_category': {}}

    good = stats.get('good', 0)
    bad = stats.get('bad', 0)
    by_cat = stats.get('by_category', {})

    # Find worst categories
    worst = []
    for cat, cat_stats in by_cat.items():
        cat_total = cat_stats.get('total', 0)
        if cat_total >= 2:
            cat_bad = cat_stats.get('bad', 0)
            cat_bad_rate = cat_bad / cat_total
            if cat_bad_rate > 0.3:  # >30% bad = needs attention
                worst.append({'category': cat, 'bad_rate': cat_bad_rate, 'total': cat_total})

    return {
        'total': total,
        'good': good,
        'bad': bad,
        'good_rate': round(good / total * 100, 1),
        'bad_rate': round(bad / total * 100, 1),
        'by_category': by_cat,
        'attention_needed': sorted(worst, key=lambda x: x['bad_rate'], reverse=True)
    }


def get_improvement_suggestions(top_k: int = 3) -> List[Dict[str, Any]]:
    """Based on feedback patterns, suggest what to improve."""
    suggestions = []
    stats = get_feedback_stats()

    # From bad feedback categories
    for item in stats.get('attention_needed', []):
        suggestions.append({
            'type': 'feedback_pattern',
            'priority': 'high',
            'suggestion': f"Categoría '{item['category']}' tiene {round(item['bad_rate']*100,0)}% de feedback negativo.",
            'reason': 'Comportamiento frecuente con baja aceptación'
        })

    # From learned rules (avoid patterns)
    rules = get_rules().get('rules', [])
    avoid_rules = [r for r in rules if r.get('source') == 'negative_feedback']
    for r in avoid_rules[-3:]:
        suggestions.append({
            'type': 'avoid_rule',
            'priority': 'medium',
            'suggestion': f"Regla aprendida: {r.get('text', '')[:100]}",
            'reason': 'Regla derivada de feedback negativo'
        })

    return suggestions[:top_k]
