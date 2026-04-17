from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class AutomationRule:
    def __init__(
        self,
        id: str,
        name: str,
        trigger: str,  # event type: window_changed, clipboard_changed, time, voice_command
        trigger_config: Dict[str, Any],
        action: str,   # action type: hotkey, type_text, open_url, notify, log
        action_config: Dict[str, Any],
        enabled: bool = True,
        cooldown_sec: float = 30.0,
        description: str = "",
    ):
        self.id = id
        self.name = name
        self.trigger = trigger
        self.trigger_config = trigger_config or {}
        self.action = action
        self.action_config = action_config or {}
        self.enabled = enabled
        self.cooldown_sec = cooldown_sec
        self.description = description
        self._last_fired: float = 0.0

    def matches(self, event: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        if event.get("type") != self.trigger:
            return False
        # Check cooldown
        now = time.time()
        if now - self._last_fired < self.cooldown_sec:
            return False
        # Match trigger config
        tc = self.trigger_config
        if self.trigger == "window_changed":
            process = str(event.get("process") or "").lower()
            title = str(event.get("title") or "").lower()
            if tc.get("process") and tc["process"].lower() not in process:
                return False
            if tc.get("title_contains"):
                if tc["title_contains"].lower() not in title:
                    return False
            return True
        if self.trigger == "clipboard_changed":
            text = str(event.get("text") or "").lower()
            if tc.get("contains"):
                return tc["contains"].lower() in text
            return True
        if self.trigger == "time":
            from datetime import datetime
            now_dt = datetime.now()
            hour = tc.get("hour")
            minute = tc.get("minute")
            if hour is not None and now_dt.hour != hour:
                return False
            if minute is not None and now_dt.minute != minute:
                return False
            return True
        return True

    def fire(self) -> None:
        self._last_fired = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "trigger": self.trigger,
            "trigger_config": self.trigger_config,
            "action": self.action,
            "action_config": self.action_config,
            "enabled": self.enabled,
            "cooldown_sec": self.cooldown_sec,
            "description": self.description,
            "last_fired": self._last_fired,
        }


class RulesEngine:
    DEFAULT_RULES: List[Dict[str, Any]] = [
        {
            "id": "clipboard_url",
            "name": "Abrir URL del portapapeles",
            "trigger": "clipboard_changed",
            "trigger_config": {"contains": "http"},
            "action": "notify",
            "action_config": {"message": "Detecté una URL en el portapapeles. ¿Abro?"},
            "cooldown_sec": 60.0,
            "description": "Cuando se copia una URL, sugiere abrirla.",
        },
        {
            "id": "spotify_title",
            "name": "Notificar cambio de canción",
            "trigger": "window_changed",
            "trigger_config": {"process": "spotify"},
            "action": "notify",
            "action_config": {"message": "Spotify cambió de ventana."},
            "cooldown_sec": 5.0,
            "description": "Avisa cuando Spotify está activa.",
        },
        {
            "id": "browser_github",
            "name": "Detectar GitHub en navegador",
            "trigger": "window_changed",
            "trigger_config": {"title_contains": "github"},
            "action": "log",
            "action_config": {"message": "Navegador en GitHub detectado."},
            "cooldown_sec": 30.0,
            "description": "Log cuando se detecta GitHub abierto.",
        },
    ]

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._rules: Dict[str, AutomationRule] = {}
        self._action_handlers: Dict[str, Callable[[AutomationRule, Dict], None]] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for rd in data.get("rules", []):
                    try:
                        r = AutomationRule(
                            id=rd["id"],
                            name=rd["name"],
                            trigger=rd["trigger"],
                            trigger_config=rd.get("trigger_config", {}),
                            action=rd.get("action", "log"),
                            action_config=rd.get("action_config", {}),
                            enabled=rd.get("enabled", True),
                            cooldown_sec=rd.get("cooldown_sec", 30.0),
                            description=rd.get("description", ""),
                        )
                        self._rules[r.id] = r
                    except Exception:
                        pass
            except Exception:
                pass
        if not self._rules:
            for rd in self.DEFAULT_RULES:
                self._rules[rd["id"]] = AutomationRule(**rd)
            self._save()

    def _save(self) -> None:
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps({"rules": [r.to_dict() for r in self._rules.values()]}, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def register_action_handler(self, action_type: str, handler: Callable[[AutomationRule, Dict], None]) -> None:
        self._action_handlers[action_type] = handler

    def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        fired = []
        for rule in list(self._rules.values()):
            if rule.matches(event):
                rule.fire()
                handler = self._action_handlers.get(rule.action)
                action_result = None
                if handler:
                    try:
                        action_result = handler(rule, event)
                    except Exception as e:
                        action_result = {"error": str(e)}
                fired.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "trigger": rule.trigger,
                    "action": rule.action,
                    "action_result": action_result,
                    "event": event,
                })
        if fired:
            self._save()
        return fired

    def add_rule(self, rule_data: Dict[str, Any]) -> AutomationRule:
        rule = AutomationRule(
            id=rule_data.get("id", f"rule_{int(time.time())}"),
            name=rule_data.get("name", "Nueva regla"),
            trigger=rule_data.get("trigger", "window_changed"),
            trigger_config=rule_data.get("trigger_config", {}),
            action=rule_data.get("action", "log"),
            action_config=rule_data.get("action_config", {}),
            enabled=rule_data.get("enabled", True),
            cooldown_sec=rule_data.get("cooldown_sec", 30.0),
            description=rule_data.get("description", ""),
        )
        self._rules[rule.id] = rule
        self._save()
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            self._save()
            return True
        return False

    def set_rule_enabled(self, rule_id: str, enabled: bool) -> bool:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = enabled
            self._save()
            return True
        return False

    def list_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._rules.values()]

    def snapshot(self) -> Dict[str, Any]:
        rules = self.list_rules()
        return {
            "count": len(rules),
            "enabled": sum(1 for r in rules if r.get("enabled")),
            "rules": rules,
        }
