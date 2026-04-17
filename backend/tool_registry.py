from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from tools import tools_list


def infer_risk(name: str) -> str:
    lowered = (name or '').lower()
    if any(token in lowered for token in ['shutdown', 'click', 'self_modification', 'close_window']):
        return 'high'
    if any(token in lowered for token in ['move_mouse', 'open_', 'send_email', 'upload', 'focus_window', 'type_text']):
        return 'medium'
    return 'low'


class ToolRegistry:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)

    def snapshot(self) -> Dict[str, Any]:
        declarations: List[Dict[str, Any]] = []
        for block in tools_list:
            declarations.extend(block.get('function_declarations', []))
        items = []
        seen = set()
        for item in declarations:
            name = item.get('name')
            if not name or name in seen:
                continue
            seen.add(name)
            items.append({
                'name': name,
                'description': item.get('description', ''),
                'risk': infer_risk(name),
                'enabled': True,
                'parameters': list((item.get('parameters') or {}).get('properties', {}).keys()),
            })
        return {
            'tools': items,
            'enabled': len([item for item in items if item.get('enabled')]),
        }
