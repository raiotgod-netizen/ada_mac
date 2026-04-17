"""
Device Registry — Trusted devices, microphones, speakers, cameras, printers, smart home.
Tracks health, availability, and metadata for all connected devices.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeviceInfo:
    id: str
    type: str  # mic, speaker, camera, printer, smart_device, bluetooth, display
    name: str
    vendor: str = ""
    model: str = ""
    connection: str = "unknown"  # usb, bluetooth, wifi, builtin
    status: str = "unknown"  # online, offline, degraded, error
    health_score: float = 1.0  # 0.0-1.0
    last_seen: str = ""
    capabilities: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DeviceRegistry:
    DEFAULT_DEVICES: List[Dict[str, Any]] = [
        {
            "id": "builtin_mic",
            "type": "mic",
            "name": "Micrófono integrado",
            "vendor": "builtin",
            "connection": "builtin",
            "status": "unknown",
            "capabilities": ["voice", "ambient"],
            "metadata": {"default_input": True},
        },
        {
            "id": "builtin_speaker",
            "type": "speaker",
            "name": "Altavoces integrados",
            "vendor": "builtin",
            "connection": "builtin",
            "status": "unknown",
            "capabilities": ["audio_output"],
            "metadata": {"default_output": True},
        },
        {
            "id": "builtin_camera",
            "type": "camera",
            "name": "Cámara web integrada",
            "vendor": "builtin",
            "connection": "builtin",
            "status": "unknown",
            "capabilities": ["video", "video_call"],
        },
    ]

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._devices: Dict[str, DeviceInfo] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for d in data.get("devices", []):
                    try:
                        dev = DeviceInfo(**d)
                        self._devices[dev.id] = dev
                    except Exception:
                        pass
            except Exception:
                pass
        if not self._devices:
            for d in self.DEFAULT_DEVICES:
                dev = DeviceInfo(**d)
                self._devices[dev.id] = dev
            self._save()

    def _save(self) -> None:
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(
                json.dumps(
                    {"devices": [d.to_dict() for d in self._devices.values()]},
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[DeviceRegistry] Save error: {e}")

    def register(self, device: DeviceInfo) -> bool:
        self._devices[device.id] = device
        self._save()
        return True

    def unregister(self, device_id: str) -> bool:
        if device_id in self._devices:
            del self._devices[device_id]
            self._save()
            return True
        return False

    def get(self, device_id: str) -> Optional[DeviceInfo]:
        return self._devices.get(device_id)

    def by_type(self, device_type: str) -> List[DeviceInfo]:
        return [d for d in self._devices.values() if d.type == device_type]

    def online(self) -> List[DeviceInfo]:
        return [d for d in self._devices.values() if d.status == "online"]

    def update_status(self, device_id: str, status: str, health_score: float | None = None) -> bool:
        dev = self._devices.get(device_id)
        if not dev:
            return False
        dev.status = status
        dev.last_seen = now_iso()
        if health_score is not None:
            dev.health_score = max(0.0, min(1.0, health_score))
        self._save()
        return True

    def snapshot(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        for dev in self._devices.values():
            by_type[dev.type] = by_type.get(dev.type, 0) + 1
            by_status[dev.status] = by_status.get(dev.status, 0) + 1
        return {
            "total": len(self._devices),
            "by_type": by_type,
            "by_status": by_status,
            "devices": [d.to_dict() for d in self._devices.values()],
        }

    def health_summary(self) -> Dict[str, Any]:
        online = self.online()
        total = len(self._devices)
        avg_health = sum(d.health_score for d in self._devices.values()) / total if total else 0.0
        return {
            "total": total,
            "online": len(online),
            "degraded": sum(1 for d in self._devices.values() if d.status == "degraded"),
            "offline": sum(1 for d in self._devices.values() if d.status == "offline"),
            "avg_health": round(avg_health, 3),
            "critical": [d.id for d in self._devices.values() if d.health_score < 0.3],
        }