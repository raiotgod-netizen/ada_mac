"""
Proactive Engine for ADA v1.
Runs in background, monitors system and notifies user proactively.
"""
import asyncio
import threading
import time
from datetime import datetime, time as dtime
import pyperclip
import os
import re


class ProactiveEngine:
    def __init__(self, ada_loop, on_notification=None):
        """
        ada_loop: reference to the Ada AudioLoop instance
        on_notification: callback(url, notification_text) to show notification to user
        """
        self.ada = ada_loop
        self.on_notification = on_notification

        self._running = False
        self._thread = None

        # Clipboard monitoring
        self._last_clipboard = ""
        self._clipboard_check_interval = 5  # seconds

        # Active window monitoring
        self._last_active_window = ""
        self._window_check_interval = 2  # seconds

        # System state
        self._last_reminder_check = {}

        # Rules for proactive actions
        self._rules = [
            {
                "id": "clipboard_url",
                "check": self._check_clipboard_url,
                "interval": 5,
                "enabled": True
            },
            {
                "id": "clipboard_code",
                "check": self._check_clipboard_code,
                "interval": 5,
                "enabled": True
            },
            {
                "id": "time_reminder",
                "check": self._check_time_based,
                "interval": 60,
                "enabled": True
            },
        ]

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print("[PROACTIVE] Engine started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[PROACTIVE] Engine stopped.")

    def _run(self):
        """Main loop running all proactive checks."""
        next_run = {rule["id"]: 0 for rule in self._rules}

        while self._running:
            try:
                now = time.time()
                for rule in self._rules:
                    if not rule["enabled"]:
                        continue
                    if now - next_run[rule["id"]] >= rule["interval"]:
                        try:
                            notification = rule["check"]()
                            if notification and self.on_notification:
                                self.on_notification(notification)
                        except Exception as e:
                            print(f"[PROACTIVE] Rule {rule['id']} error: {e}")
                        next_run[rule["id"]] = now

            except Exception as e:
                print(f"[PROACTIVE] Main loop error: {e}")
            time.sleep(1)

    # ---- CHECK FUNCTIONS ----

    def _check_clipboard_url(self):
        """Detect URLs copied to clipboard."""
        try:
            current = pyperclip.paste()
            if current and current != self._last_clipboard:
                self._last_clipboard = current
                url_pattern = re.compile(
                    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                )
                if url_pattern.match(current.strip()):
                    return {
                        "type": "clipboard_url",
                        "text": f"Detecté una URL en el portapapeles: {current[:80]}",
                        "action": "open_url"
                    }
        except Exception as e:
            pass
        return None

    def _check_clipboard_code(self):
        """Detect code snippets copied to clipboard."""
        try:
            current = pyperclip.paste()
            if current and current != self._last_clipboard and len(current) > 20:
                self._last_clipboard = current
                # Simple heuristics: contains common code patterns
                code_indicators = ['def ', 'class ', 'import ', 'function', 'const ', 'let ',
                                   'var ', '=>', '->', 'print(', 'return ', 'if ', '#include']
                matches = sum(1 for ind in code_indicators if ind in current)
                if matches >= 2:
                    return {
                        "type": "clipboard_code",
                        "text": f"Detecté código en el portapapeles ({matches} indicadores). ¿Querés que lo guarde o ejecute?",
                        "action": "code_detected"
                    }
        except Exception as e:
            pass
        return None

    def _check_time_based(self):
        """Time-based reminders and notifications."""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # Morning reminder (8:00 AM)
        if hour == 8 and minute == 0 and self._last_reminder_check.get("morning") != now.date():
            self._last_reminder_check["morning"] = now.date()
            return {
                "type": "time",
                "text": "Buenos días, Jefe. Resumen del día: sin eventos pendientes.",
                "action": "greeting"
            }

        # End of work day (6:00 PM)
        if hour == 18 and minute == 0 and self._last_reminder_check.get("evening") != now.date():
            self._last_reminder_check["evening"] = now.date()
            return {
                "type": "time",
                "text": "Jefe, son las 6 PM. ¿Hay algo pendiente antes de cerrar?",
                "action": "end_day"
            }

        return None

    def _check_active_window(self):
        """Detect long focus on a single window (potential stuck state)."""
        try:
            import win32gui
            import win32process

            def get_foreground_window_info():
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                return title, pid

            title, pid = get_foreground_window_info()
            if title and title != self._last_active_window:
                self._last_active_window = title
                self._window_focus_start = time.time()
            elif title == self._last_active_window and title:
                # Same window for more than 2 hours
                if hasattr(self, '_window_focus_start'):
                    elapsed = time.time() - self._window_focus_start
                    if elapsed > 7200:  # 2 hours
                        self._window_focus_start = time.time()  # Reset to avoid spam
                        return {
                            "type": "window_stuck",
                            "text": f"Llevás más de 2 horas en '{title[:50]}'. ¿Todo bien?",
                            "action": "check_in"
                        }
        except Exception:
            pass
        return None
