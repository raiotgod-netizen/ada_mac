"""
Calendar Connector — Interface to system calendar (Windows).
Uses win32com for Outlook or simple file-based storage as fallback.
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


class CalendarConnector:
    """
    Simple calendar using JSON storage as local fallback.
    Can be extended to use win32com Outlook or other backends.
    """

    DEFAULT_STORAGE = None  # set via init

    def __init__(self, storage_path: str | Path | None = None):
        self.storage_path = Path(storage_path) if storage_path else Path(
            os.environ.get("LOCALAPPDATA", "C:\\Users\\raiot\\AppData\\Local")
        ) / "ADA" / "calendar_events.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                self._events = data.get("events", [])
            except Exception:
                self._events = []
        # Clean old events (past > 7 days)
        self._purge_old()

    def _save(self) -> None:
        try:
            self.storage_path.write_text(
                json.dumps({"events": self._events}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[CalendarConnector] Save error: {e}")

    def _purge_old(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        before = len(self._events)
        self._events = [
            e for e in self._events
            if datetime.fromisoformat(e["start"]).replace(tzinfo=timezone.utc) > cutoff
        ]
        if len(self._events) < before:
            self._save()

    def add_event(
        self,
        title: str,
        start_iso: str,
        end_iso: str | None = None,
        description: str = "",
        location: str = "",
        all_day: bool = False,
    ) -> Dict[str, Any]:
        if end_iso is None:
            start_dt = datetime.fromisoformat(start_iso)
            end_dt = start_dt + timedelta(hours=1)
            end_iso = end_dt.isoformat()

        event = {
            "id": f"evt-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "title": title,
            "start": start_iso,
            "end": end_iso,
            "description": description,
            "location": location,
            "all_day": all_day,
            "created_at": now_iso(),
        }
        self._events.append(event)
        self._save()
        return event

    def list_events(self, days: int = 7, include_past: bool = False) -> List[Dict[str, Any]]:
        self._purge_old()
        cutoff = datetime.now(timezone.utc) - timedelta(days=1) if not include_past else None
        upcoming = []
        for e in self._events:
            start = datetime.fromisoformat(e["start"]).replace(tzinfo=timezone.utc)
            if cutoff and start < cutoff:
                continue
            if start > datetime.now(timezone.utc) + timedelta(days=days):
                continue
            upcoming.append(e)
        return sorted(upcoming, key=lambda x: x["start"])

    def delete_event(self, event_id: str) -> bool:
        before = len(self._events)
        self._events = [e for e in self._events if e["id"] != event_id]
        if len(self._events) < before:
            self._save()
            return True
        return False

    def today_events(self) -> List[Dict[str, Any]]:
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        return [
            e for e in self._events
            if datetime.fromisoformat(e["start"]).replace(tzinfo=timezone.utc) >= today_start
            and datetime.fromisoformat(e["start"]).replace(tzinfo=timezone.utc) < today_end
        ]

    def snapshot(self) -> Dict[str, Any]:
        events = self.list_events(days=7)
        today = self.today_events()
        return {
            "total": len(self._events),
            "upcoming_count": len(events),
            "today_count": len(today),
            "today": today[:5],
            "upcoming": events[:10],
        }