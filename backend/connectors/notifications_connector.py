"""
Notifications Connector — System notifications, reminders, and toasts.
Uses Windows Toast notifications via PowerShell or a file-based queue as fallback.
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NotificationsConnector:
    """
    Local notification system. Uses Windows PowerShell for toast notifications.
    Stores notification history in JSON for recall.
    """

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else Path(
            os.environ.get("LOCALAPPDATA", "C:\\Users\\raiot\\AppData\\Local")
        ) / "ADA" / "notifications.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._notifications: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._notifications = data.get("notifications", [])
            except Exception:
                self._notifications = []
        self._purge_old()

    def _save(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps({"notifications": self._notifications}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[NotificationsConnector] Save error: {e}")

    def _purge_old(self) -> None:
        # Keep last 200 notifications
        if len(self._notifications) > 200:
            self._notifications = sorted(
                self._notifications, key=lambda x: x.get("created_at", ""), reverse=True
            )[:200]

    def _is_windows(self) -> bool:
        return os.name == "nt"

    def _send_toast_ps(self, title: str, message: str) -> bool:
        """Send Windows toast via PowerShell BurntToast or fallback."""
        try:
            # Try using Windows.UI.Notifications or BurntToast if available
            script = f'''
            try {{
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $textNodes = $template.GetElementsByTagName("text")
                $textNodes.Item(0).AppendChild($template.CreateTextNode("{title.replace('"', '\\\"')}")) | Out-Null
                $textNodes.Item(1).AppendChild($template.CreateTextNode("{message.replace('"', '\\\"')}")) | Out-Null
                $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ADA").Show($toast)
            }} catch {{
                # Fallback: echo to console
                Write-Host "[ADA NOTIFICATION] {title}: {message}"
            }}
            '''
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",  # low, normal, high, critical
        tag: str = "",
        expires_in_minutes: int | None = None,
    ) -> Dict[str, Any]:
        notification = {
            "id": f"notif-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "title": title,
            "message": message,
            "urgency": urgency,
            "tag": tag,
            "read": False,
            "created_at": now_iso(),
            "expires_at": (
                (datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)).isoformat()
                if expires_in_minutes else None
            ),
        }
        self._notifications.insert(0, notification)
        self._save()

        # Send system toast
        if self._is_windows():
            self._send_toast_ps(title, message)

        return notification

    def list_notifications(
        self,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        self._purge_old()
        notifs = self._notifications
        if unread_only:
            notifs = [n for n in notifs if not n.get("read")]
        return notifs[:limit]

    def mark_read(self, notification_id: str) -> bool:
        for n in self._notifications:
            if n["id"] == notification_id:
                n["read"] = True
                self._save()
                return True
        return False

    def mark_all_read(self) -> None:
        for n in self._notifications:
            n["read"] = True
        self._save()

    def delete(self, notification_id: str) -> bool:
        before = len(self._notifications)
        self._notifications = [n for n in self._notifications if n["id"] != notification_id]
        if len(self._notifications) < before:
            self._save()
            return True
        return False

    def unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n.get("read"))

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total": len(self._notifications),
            "unread": self.unread_count(),
            "recent": self._notifications[:10],
        }

    def remind(
        self,
        title: str,
        message: str,
        in_minutes: int = 30,
        reminder_id: str | None = None,
    ) -> Dict[str, Any]:
        """Schedule a reminder notification."""
        rid = reminder_id or f"rem-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        reminder = {
            "id": rid,
            "type": "reminder",
            "title": title,
            "message": message,
            "fire_at": (datetime.now(timezone.utc) + timedelta(minutes=in_minutes)).isoformat(),
            "created_at": now_iso(),
            "fired": False,
        }
        # Store in a separate reminders file
        rem_path = self.storage_path.parent / "reminders.json"
        try:
            existing = []
            if rem_path.exists():
                existing = json.loads(rem_path.read_text(encoding="utf-8"))
            existing.append(reminder)
            rem_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[NotificationsConnector] Reminder save error: {e}")

        return {
            "id": rid,
            "fire_at": reminder["fire_at"],
            "message": f"Recordatorio en {in_minutes} minutos: {title}",
        }