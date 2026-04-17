from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from policy_engine import PolicyEngine


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentCore:
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self._state: Dict[str, Any] = {
            "status": "idle",
            "current_goal": None,
            "last_plan": None,
            "last_world_state": None,
            "recent_runs": [],
            "routines": {
                "active": 0,
                "last_event": None,
            },
            "policy": {
                "mode": "supervised",
                "allow_desktop_automation": True,
                "allow_browser_actions": True,
                "allow_system_control": True,
                "allow_self_improvement": True,
            },
            "capability_awareness": {
                "global_memory": True,
                "desktop_automation": True,
                "system_observer": True,
                "vision_context": True,
                "routines": True,
                "security_audit": True,
                "improvement_engine": True,
            },
        }

    def plan_goal(self, text: str, orchestrator_plan: Dict[str, Any], memory_snapshot: Dict[str, Any] | None = None) -> Dict[str, Any]:
        plan = {
            "goal": text,
            "intent": orchestrator_plan.get("intent", "conversation"),
            "route": orchestrator_plan.get("route", "conversation"),
            "confidence": orchestrator_plan.get("confidence", 0.0),
            "tools": orchestrator_plan.get("tools", []),
            "steps": self._build_steps(orchestrator_plan),
            "memory_context": {
                "rules_count": (memory_snapshot or {}).get("rules_count", 0),
                "projects_count": ((memory_snapshot or {}).get("global_projects") or {}).get("projects_count", 0),
                "improvements_count": ((memory_snapshot or {}).get("global_projects") or {}).get("improvements_count", 0),
            },
            "progress": {
                "total_steps": 0,
                "completed_steps": 0,
                "current_step": None,
            },
            "created_at": now_iso(),
        }
        plan["progress"]["total_steps"] = len(plan["steps"])
        self._state["last_plan"] = plan
        self._state["current_goal"] = text
        self._state["status"] = "planned"
        return plan

    def evaluate_policy(self, plan: Dict[str, Any], world_state: Dict[str, Any]) -> Dict[str, Any]:
        decision = self.policy_engine.evaluate(plan, world_state, self._state.get("policy", {}))
        self._state["status"] = "policy_checked"
        self._state["last_world_state"] = world_state
        return decision

    def mark_step_started(self, plan: Dict[str, Any], step_name: str):
        for step in plan.get("steps", []):
            if step.get("step") == step_name and step.get("status") == "planned":
                step["status"] = "running"
                plan["progress"]["current_step"] = step_name
                self._state["status"] = "executing"
                return

    def mark_step_completed(self, plan: Dict[str, Any], step_name: str):
        completed = 0
        for step in plan.get("steps", []):
            if step.get("step") == step_name:
                step["status"] = "completed"
            if step.get("status") == "completed":
                completed += 1
        plan["progress"]["completed_steps"] = completed
        remaining = [s.get("step") for s in plan.get("steps", []) if s.get("status") == "planned"]
        plan["progress"]["current_step"] = remaining[0] if remaining else None

    def register_execution(self, plan: Dict[str, Any], result: str | None = None, error: str | None = None):
        run = {
            "goal": plan.get("goal"),
            "intent": plan.get("intent"),
            "route": plan.get("route"),
            "tools": plan.get("tools", []),
            "status": "failed" if error else "completed",
            "result": result,
            "error": error,
            "progress": dict(plan.get("progress", {})),
            "updated_at": now_iso(),
        }
        self._state.setdefault("recent_runs", []).insert(0, run)
        self._state["recent_runs"] = self._state["recent_runs"][:20]
        self._state["status"] = run["status"]

    def run_execution_loop(self, plan: Dict[str, Any], direct_result: str | None = None, error: str | None = None) -> Dict[str, Any]:
        if direct_result:
            self.mark_step_completed(plan, plan.get('progress', {}).get('current_step') or 'evaluate_result')
            self.mark_step_completed(plan, 'evaluate_result')
            self.register_execution(plan, result=direct_result)
            return {"ok": True, "result": direct_result}
        if error:
            self.register_execution(plan, error=error)
            return {"ok": False, "result": error}
        return {"ok": False, "result": "no_execution_result"}

    def register_routine_event(self, summary: str, active: int = 0):
        self._state["routines"] = {
            "active": active,
            "last_event": summary,
            "updated_at": now_iso(),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "status": self._state.get("status", "idle"),
            "current_goal": self._state.get("current_goal"),
            "last_plan": self._state.get("last_plan"),
            "last_world_state": self._state.get("last_world_state"),
            "policy": dict(self._state.get("policy", {})),
            "capability_awareness": dict(self._state.get("capability_awareness", {})),
            "recent_runs": list(self._state.get("recent_runs", []))[:10],
            "routines": dict(self._state.get("routines", {})),
        }

    def _build_steps(self, orchestrator_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        tools = orchestrator_plan.get("tools", []) or []
        steps: List[Dict[str, Any]] = [{"step": "understand_request", "status": "planned"}]
        for tool in tools[:6]:
            steps.append({"step": f"use_{tool}", "status": "planned"})
        steps.append({"step": "evaluate_result", "status": "planned"})
        return steps
