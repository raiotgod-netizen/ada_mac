from datetime import datetime, timezone
from typing import Any, Dict


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RuntimeManager:
    def __init__(self):
        self._state: Dict[str, Any] = {
            "core": {
                "status": "booting",
                "updated_at": now_iso(),
            },
            "providers": {
                "gemini": {
                    "mode": "initializing",
                    "available": False,
                    "last_error": None,
                    "updated_at": now_iso(),
                }
            },
            "degraded": False,
            "degraded_reason": None,
            "local_only_reason": None,
        }

    def set_core_status(self, status: str):
        self._state["core"] = {
            "status": status,
            "updated_at": now_iso(),
        }

    def set_provider_state(self, provider: str, mode: str, available: bool, last_error: str | None = None):
        self._state.setdefault("providers", {})[provider] = {
            "mode": mode,
            "available": available,
            "last_error": last_error,
            "updated_at": now_iso(),
        }
        self._state["degraded"] = False
        self._state["degraded_reason"] = None

    def snapshot(self) -> Dict[str, Any]:
        return {
            "core": dict(self._state.get("core", {})),
            "providers": {
                name: dict(info)
                for name, info in self._state.get("providers", {}).items()
            },
            "degraded": self._state.get("degraded", False),
            "degraded_reason": self._state.get("degraded_reason"),
            "local_only_reason": self._state.get("local_only_reason"),
        }
