from __future__ import annotations

import asyncio
import ctypes
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class SystemMonitor:
    """
    Monitor de eventos del sistema para Windows.
    Detecta cambios de ventana activa, portapapeles y notificaciones.
    """

    def __init__(self, poll_interval: float = 1.0):
        self.poll_interval = poll_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_window: Dict[str, Any] | None = None
        self._last_clipboard: str = ""
        self._events: deque = deque(maxlen=200)
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self._lock = threading.Lock()

        # Win32 imports
        try:
            self._user32 = ctypes.windll.user32
            self._kernel32 = ctypes.windll.kernel32
            self._win_available = True
        except Exception:
            self._win_available = False

    def _win_get_foreground_window(self) -> tuple[int, str, str]:
        """Devuelve (handle, title, process) de la ventana activa."""
        if not self._win_available:
            return 0, "", ""
        try:
            hwnd = self._user32.GetForegroundWindow()
            if hwnd == 0:
                return 0, "", ""
            pid = ctypes.DWORD()
            self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            length = self._user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return int(hwnd), "", ""
            buf = ctypes.create_unicode_buffer(length + 1)
            self._user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            process = ""
            try:
                import psutil
                process = psutil.Process(pid.value).name() if pid.value else ""
            except Exception:
                pass
            return int(hwnd), str(title), str(process)
        except Exception:
            return 0, "", ""

    def _win_get_clipboard_text(self) -> str:
        """Lee el portapapeles de Windows."""
        if not self._win_available:
            return ""
        try:
            import win32clipboard
            win32clipboard.OpenClipboard(0)
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    return text or ""
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass
        return ""

    def subscribe(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        with self._lock:
            self._subscribers.append(callback)

    def _emit(self, event: Dict[str, Any]) -> None:
        with self._lock:
            self._events.append(event)
            for cb in list(self._subscribers):
                try:
                    cb(event)
                except Exception:
                    pass

    def _poll(self) -> None:
        last_window = None
        last_clipboard = ""
        while self._running:
            try:
                # Poll foreground window
                hwnd, title, process = self._win_get_foreground_window()
                window_key = f"{hwnd}|{title}|{process}"
                if window_key != last_window and last_window is not None:
                    self._emit({
                        "type": "window_changed",
                        "handle": hwnd,
                        "title": title,
                        "process": process,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    })
                    last_window = window_key
                elif last_window is None:
                    last_window = window_key

                # Poll clipboard
                try:
                    clipboard_text = self._win_get_clipboard_text()
                    if clipboard_text and clipboard_text != last_clipboard:
                        self._emit({
                            "type": "clipboard_changed",
                            "text": clipboard_text[:500],
                            "length": len(clipboard_text),
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                        })
                        last_clipboard = clipboard_text
                except Exception:
                    pass

            except Exception:
                pass
            time.sleep(self.poll_interval)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events)[-limit:]

    def snapshot(self) -> Dict[str, Any]:
        hwnd, title, process = self._win_get_foreground_window()
        clipboard = self._win_get_clipboard_text()
        return {
            "monitor_running": self._running,
            "active_window": {"handle": hwnd, "title": title, "process": process},
            "clipboard_text": clipboard[:200] if clipboard else "",
            "recent_events_count": len(self._events),
        }
