from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List


POWERSHELL = "powershell"


class BluetoothManager:
    def __init__(self, workspace_root: str | Path):
        self.workspace_root = Path(workspace_root)
        self.shared_dir = self.workspace_root / "shared_state"
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.shared_dir / "bluetooth_devices.json"
        if not self.registry_path.exists():
            self._save_registry({"known_devices": []})

    def _run_powershell(self, script: str, timeout: int = 10) -> str:
        try:
            completed = subprocess.run(
                [POWERSHELL, "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if completed.returncode != 0:
                return ""
            return (completed.stdout or "").strip()
        except Exception:
            return ""

    def _run_json(self, script: str, timeout: int = 10):
        raw = self._run_powershell(script, timeout=timeout)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def _load_registry(self) -> Dict[str, Any]:
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {"known_devices": []}

    def _save_registry(self, data: Dict[str, Any]):
        self.registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def adapter_status(self) -> Dict[str, Any]:
        script = r'''
$service = Get-Service bthserv -ErrorAction SilentlyContinue | Select-Object Name,Status,StartType
$devices = Get-PnpDevice | Where-Object {
    ($_.Class -match 'Bluetooth') -or
    ($_.FriendlyName -match 'Bluetooth|Intel\(R\) Wireless Bluetooth|Realtek Bluetooth|Generic Bluetooth')
} | Select-Object Status,Class,FriendlyName,InstanceId
[pscustomobject]@{
    service = $service
    adapters = @($devices)
} | ConvertTo-Json -Depth 5 -Compress
'''
        data = self._run_json(script) or {}
        adapters = data.get("adapters", []) if isinstance(data, dict) else []
        if isinstance(adapters, dict):
            adapters = [adapters]
        return {
            "service": (data or {}).get("service") or {},
            "adapters": adapters,
            "available": bool(adapters or (data or {}).get("service")),
        }

    def paired_devices(self) -> List[Dict[str, Any]]:
        script = r'''
$items = Get-PnpDevice | Where-Object {
    $_.FriendlyName -match 'Bluetooth' -and
    $_.Class -notmatch 'Bluetooth'
} | Select-Object Status,Class,FriendlyName,InstanceId
@($items) | ConvertTo-Json -Depth 4 -Compress
'''
        data = self._run_json(script) or []
        if isinstance(data, dict):
            data = [data]
        normalized = []
        for item in data:
            name = str(item.get("FriendlyName") or item.get("friendlyName") or "").strip()
            if not name:
                continue
            normalized.append({
                "name": name,
                "status": item.get("Status") or item.get("status"),
                "class": item.get("Class") or item.get("class"),
                "instance_id": item.get("InstanceId") or item.get("instanceId"),
            })
        return normalized[:50]

    def connected_devices(self) -> List[Dict[str, Any]]:
        paired = self.paired_devices()
        connected = []
        for item in paired:
            status = str(item.get("status") or "").lower()
            if status in {"ok", "error", "unknown"}:
                connected.append({**item, "connected": status == "ok"})
        return connected[:50]

    def inventory(self) -> Dict[str, Any]:
        adapter = self.adapter_status()
        paired = self.paired_devices()
        connected = [item for item in self.connected_devices() if item.get("connected")]
        self.remember_devices(paired)
        return {
            "available": adapter.get("available", False),
            "adapter": adapter,
            "paired": paired,
            "connected": connected,
            "known": self.known_devices(),
        }

    def known_devices(self) -> List[Dict[str, Any]]:
        return self._load_registry().get("known_devices", [])[:100]

    def remember_devices(self, devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        registry = self._load_registry()
        known = registry.get("known_devices", [])
        existing = {str(item.get("instance_id") or item.get("name") or "").lower(): item for item in known}
        for item in devices or []:
            key = str(item.get("instance_id") or item.get("name") or "").lower()
            if not key:
                continue
            existing[key] = item
        merged = list(existing.values())
        registry["known_devices"] = merged[:100]
        self._save_registry(registry)
        return {"ok": True, "count": len(registry["known_devices"]), "devices": registry["known_devices"]}

    def toggle_service(self, enabled: bool) -> Dict[str, Any]:
        script = "Start-Service bthserv -ErrorAction SilentlyContinue; 'ok'" if enabled else "Stop-Service bthserv -ErrorAction SilentlyContinue; 'ok'"
        raw = self._run_powershell(script, timeout=12)
        return {"ok": raw.strip().lower() == "ok", "result": "Servicio Bluetooth actualizado." if raw else "No pude cambiar el servicio Bluetooth."}

    def open_settings(self) -> Dict[str, Any]:
        try:
            os.startfile('ms-settings:bluetooth')
            return {"ok": True, "result": "Abrí la configuración de Bluetooth."}
        except Exception as e:
            return {"ok": False, "result": f"No pude abrir Bluetooth Settings: {e}"}

    def connect_device(self, name: str) -> Dict[str, Any]:
        target = (name or "").strip().lower()
        if not target:
            return {"ok": False, "result": "Falta nombre del dispositivo Bluetooth."}
        known = self.known_devices()
        match = next((item for item in known if target in str(item.get("name", "")).lower()), None)
        if not match:
            return {"ok": False, "result": "No encontré ese dispositivo en memoria Bluetooth."}
        return {
            "ok": False,
            "result": "La conexión Bluetooth directa en Windows depende del perfil y stack del dispositivo. Dejé inventario y control base listos, pero esta acción requiere implementación específica por tipo de dispositivo o automatización de Settings.",
            "device": match,
            "requires_confirmation": True,
        }

    def disconnect_device(self, name: str) -> Dict[str, Any]:
        target = (name or "").strip().lower()
        if not target:
            return {"ok": False, "result": "Falta nombre del dispositivo Bluetooth."}
        known = self.known_devices()
        match = next((item for item in known if target in str(item.get("name", "")).lower()), None)
        if not match:
            return {"ok": False, "result": "No encontré ese dispositivo en memoria Bluetooth."}
        return {
            "ok": False,
            "result": "La desconexión Bluetooth directa en Windows también depende del tipo de dispositivo. La base quedó preparada para soportarlo por perfil más adelante.",
            "device": match,
            "requires_confirmation": True,
        }

    def snapshot(self) -> Dict[str, Any]:
        data = self.inventory()
        return {
            "available": data.get("available", False),
            "adapters": (data.get("adapter") or {}).get("adapters", []),
            "service": (data.get("adapter") or {}).get("service", {}),
            "paired_count": len(data.get("paired", [])),
            "connected_count": len(data.get("connected", [])),
            "paired": data.get("paired", [])[:20],
            "connected": data.get("connected", [])[:20],
            "known": data.get("known", [])[:20],
        }
