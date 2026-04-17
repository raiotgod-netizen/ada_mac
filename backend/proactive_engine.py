"""
Proactive Engine for ADA v1.
Runs in background, monitors system and notifies user proactively.
"""
import asyncio
import queue
import threading
import time
from datetime import datetime, time as dtime
import pyperclip
import os
import re


class ProactiveEngine:
    def __init__(self, ada_loop, on_notification=None, event_loop=None):
        """
        ada_loop: reference to the Ada AudioLoop instance
        on_notification: callback(url, notification_text) to show notification to user
        event_loop: asyncio event loop for thread-safe async calls
        """
        self.ada = ada_loop
        self.on_notification = on_notification
        self._event_loop = event_loop

        self._running = False
        self._thread = None
        self._notification_queue = queue.Queue()

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
            {
                "id": "active_window",
                "check": self._check_active_window,
                "interval": 30,
                "enabled": True
            },
            {
                "id": "memory_alert",
                "check": self._check_memory_alerts,
                "interval": 300,  # 5 min
                "enabled": True
            },
            {
                "id": "learned_rules_review",
                "check": self._check_learned_rules,
                "interval": 600,  # 10 min
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

    def set_event_loop(self, loop):
        """Set the asyncio event loop for thread-safe async calls."""
        self._event_loop = loop

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
                            if notification:
                                self._dispatch_notification(notification)
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

    def _check_memory_alerts(self):
        """Check long-term memory for things that need attention."""
        try:
            ltm = getattr(self.ada, 'long_term_memory', None)
            if not ltm:
                return None

            # Check for items marked as important that haven't been accessed recently
            alerts = ltm.get_by_category("user_facts")
            for block in alerts:
                if block.importance >= 4 and time.time() - block.last_accessed > 86400 * 3:
                    # High-importance fact not accessed in 3+ days — surface it
                    return {
                        "type": "memory_refresh",
                        "text": f" recordatorio: {block.content[:100]}",
                        "action": "memory_refresh"
                    }
        except Exception as e:
            print(f"[PROACTIVE] memory_alerts error: {e}")
        return None

    def _check_learned_rules(self):
        """Review learned rules and confirm they are still relevant."""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
            import learning_manager as lm

            rules = lm.get_rules().get("rules", [])
            if rules and len(rules) <= 3:
                # Only a few rules — make sure user knows they're being applied
                recent_rule = rules[-1].get("text", "")
                if recent_rule:
                    return {
                        "type": "rules_active",
                        "text": f"Regla activa: {recent_rule[:100]}",
                        "action": "rules_review"
                    }
        except Exception as e:
            print(f"[PROACTIVE] learned_rules error: {e}")
        return None

    def _dispatch_notification(self, notification):
        """Dispatch notification thread-safely via event loop or queue."""
        if not notification:
            return
        if self._event_loop:
            try:
                # Schedule async callback in the event loop thread
                asyncio.run_coroutine_threadsafe(
                    self._async_notify(notification),
                    self._event_loop
                )
            except Exception as e:
                print(f"[PROACTIVE] run_coroutine_threadsafe error: {e}")
                self._notification_queue.put(notification)
        else:
            # Queue if no event loop available yet
            self._notification_queue.put(notification)

    async def _async_notify(self, notification):
        """Async version of notification dispatch."""
        try:
            if self.on_notification:
                self.on_notification(notification)
        except Exception as e:
            print(f"[PROACTIVE] async_notify error: {e}")

    def get_pending_notifications(self):
        """Return pending notifications queued while event loop wasn't available."""
        pending = []
        while True:
            try:
                n = self._notification_queue.get_nowait()
                pending.append(n)
            except queue.Empty:
                break
        return pending
