from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import json
import os
import platform
import socket
import subprocess


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SecurityAudit:
    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def _push(self, kind: str, result: Dict[str, Any]):
        event = {"kind": kind, "result": result, "timestamp": now_iso()}
        self._events.insert(0, event)
        self._events = self._events[:50]
        return event

    def host_inventory(self) -> Dict[str, Any]:
        info = {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "user": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
            "cwd": str(Path.cwd()),
            "timestamp": now_iso(),
        }
        return self._push("host_inventory", {"ok": True, "result": info})

    def network_snapshot(self) -> Dict[str, Any]:
        try:
            proc = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=8)
            text = (proc.stdout or proc.stderr or "")[:12000]
            return self._push("network_snapshot", {"ok": proc.returncode == 0, "result": text})
        except Exception as e:
            return self._push("network_snapshot", {"ok": False, "result": str(e)})

    def startup_snapshot(self) -> Dict[str, Any]:
        try:
            proc = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=8)
            text = (proc.stdout or proc.stderr or "")[:12000]
            return self._push("startup_snapshot", {"ok": proc.returncode == 0, "result": text})
        except Exception as e:
            return self._push("startup_snapshot", {"ok": False, "result": str(e)})

    def disk_snapshot(self) -> Dict[str, Any]:
        try:
            root = Path.cwd()
            items = [p.name for p in root.iterdir()][:100]
            return self._push("disk_snapshot", {"ok": True, "result": {"cwd": str(root), "items": items}})
        except Exception as e:
            return self._push("disk_snapshot", {"ok": False, "result": str(e)})

    def report(self) -> Dict[str, Any]:
        return {"count": len(self._events), "recent": list(self._events[:10])}
