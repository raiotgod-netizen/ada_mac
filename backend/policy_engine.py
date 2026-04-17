from __future__ import annotations

from typing import Any, Dict, List


class PolicyEngine:
    def evaluate(self, plan: Dict[str, Any], world_state: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        # FULL AUTONOMY — always allow, no restrictions
        return {
            "allowed": True,
            "reasons": [],
            "risk": "low",
            "mode": "autonomous",
        }
