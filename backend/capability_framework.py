from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from skill_registry import SkillRegistry
from tool_registry import ToolRegistry


DEFAULT_CAPABILITIES = {
    "skills": [],
    "tools": []
}


class CapabilityFramework:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.shared_dir / "capability_framework.json"
        self.skill_registry = SkillRegistry(self.workspace_root)
        self.tool_registry = ToolRegistry(self.workspace_root)
        if not self.path.exists():
            self._save(DEFAULT_CAPABILITIES)

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return json.loads(json.dumps(DEFAULT_CAPABILITIES))

    def _save(self, data: Dict[str, Any]):
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def ensure_defaults(self) -> Dict[str, Any]:
        data = self._load()
        skills = self.skill_registry.snapshot().get("skills", [])
        tools = self.tool_registry.snapshot().get("tools", [])
        data["skills"] = skills
        data["tools"] = tools
        self._save(data)
        return data

    def skill_tool_map(self) -> Dict[str, List[str]]:
        return {
            "memory": ["learn_preference", "learn_rule", "consolidate_memory"],
            "desktop": ["move_mouse", "click_mouse", "type_text", "press_hotkey", "focus_window", "close_window", "open_url", "open_local_file", "reveal_local_file", "run_desktop_sequence"],
            "vision": ["capture_screen_snapshot", "observe_system_state"],
            "email": ["send_email", "prepare_email_attachments", "suggest_recent_attachments"],
            "improvement": ["propose_self_improvement", "create_custom_script", "run_custom_script", "write_file"],
        }

    def snapshot(self) -> Dict[str, Any]:
        data = self.ensure_defaults()
        skills = data.get("skills", [])
        tools = data.get("tools", [])
        return {
            "skills": skills,
            "tools": tools,
            "skill_tool_map": self.skill_tool_map(),
            "skills_enabled": len([s for s in skills if s.get("enabled")]),
            "tools_enabled": len([t for t in tools if t.get("enabled")]),
        }
