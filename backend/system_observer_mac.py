"""
system_observer_mac.py — SystemObserver for macOS (Darwin)

Cross-platform replacement using osascript/NSAppleScript for window management.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


BROWSER_NAMES = {"chrome", "safari", "firefox", "brave", "opera", "microsoft edge"}


def _run_osascript(script: str, timeout: int = 8) -> str:
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout
        )
        return (result.stdout or "").strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _get_clipboard_text() -> str:
    """Read clipboard on macOS via pbpaste."""
    try:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=3)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _get_process_list() -> List[Dict[str, Any]]:
    """Get running processes via ps."""
    try:
        r = subprocess.run(
            ["ps", "-eo", "pid,pcpu,rss,comm"],
            capture_output=True, text=True, timeout=5
        )
        processes = []
        for line in r.stdout.split("\n")[1:50]:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    processes.append({
                        "pid": int(parts[0]),
                        "cpu": float(parts[1]),
                        "rss_kb": int(parts[2]),
                        "name": parts[3]
                    })
                except Exception:
                    pass
        return processes
    except Exception:
        return []


class SystemObserver:
    def __init__(self, workspace_root: str | Path | None = None):
        root = workspace_root or Path(__file__).resolve().parent.parent
        self.workspace_root = Path(root)

    def get_open_windows(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get open windows via osascript."""
        script = '''
        tell application "System Events"
            set windowList to {}
            set processList to every application process whose visible is true
            repeat with theApp in processList
                set appName to name of theApp
                try
                    set winList to every window of theApp
                    repeat with theWin in winList
                        set winName to name of theWin
                        if winName is not "" then
                            set end of windowList to {title:winName, process:appName}
                        end if
                    end repeat
                end try
            end repeat
        end tell
        '''
        r = _run_osascript(script)
        if not r:
            return []
        try:
            # Parse AppleScript list output
            windows = []
            for line in r.split(", "):
                line = line.strip()
                if " : " in line:
                    parts = line.split(" : ", 1)
                    windows.append({"title": parts[0].strip(), "process": parts[1].strip()})
            return windows[:limit]
        except Exception:
            return []

    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get the frontmost active window."""
        script = '''
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            set appName to name of frontApp
            try
                set winList to every window of frontApp
                if (count of winList) > 0 then
                    set winName to name of first window of frontApp
                    return appName & " : " & winName
                end if
            end try
            return appName & " : (no window)"
        end tell
        '''
        r = _run_osascript(script)
        if not r:
            return None
        if " : " in r:
            parts = r.split(" : ", 1)
            return {"process": parts[0].strip(), "title": parts[1].strip()}
        return {"process": r.strip(), "title": "(no window)"}

    def get_processes(self, limit: int = 25) -> List[Dict[str, Any]]:
        processes = _get_process_list()
        # Get window count per app
        windows = self.get_open_windows(limit=100)
        window_count_by_app = {}
        for w in windows:
            app = w.get("process", "")
            window_count_by_app[app] = window_count_by_app.get(app, 0) + 1

        result = []
        for p in processes[:limit]:
            name = p.get("name", "")
            app = name.replace(".app", "")
            win_count = window_count_by_app.get(app, 0)
            result.append({
                "name": name,
                "pid": p.get("pid"),
                "cpu": p.get("cpu"),
                "memory_mb": round(p.get("rss_kb", 0) / 1024, 1),
                "windows": win_count,
            })
        return result

    def get_browser_windows(self, windows: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        windows = windows if windows is not None else self.get_open_windows(limit=100)
        return [w for w in windows if str(w.get("process", "")).lower() in BROWSER_NAMES]

    def focus_window(self, title: str | None = None, process: str | None = None, pid: int | None = None) -> Dict[str, Any]:
        """Focus a window by title, process name, or PID."""
        if pid:
            # Find process name by PID
            r = _run_osascript(f'''
            tell application "System Events"
                set targetApp to first application process whose unix id is {pid}
                set frontmost of targetApp to true
            end tell
            ''')
            if r:
                return {"ok": True, "result": f"App with PID {pid} focused"}
            return {"ok": False, "result": f"Could not focus PID {pid}"}

        if process:
            r = _run_osascript(f'''
            tell application "System Events"
                set targetApp to first application process whose name contains "{process}"
                set frontmost of targetApp to true
            end tell
            ''')
            if r:
                return {"ok": True, "result": f"App '{process}' focused"}
            return {"ok": False, "result": f"Could not focus app: {process}"}

        if title:
            windows = self.get_open_windows(limit=100)
            for w in windows:
                if title.lower() in w.get("title", "").lower():
                    app = w.get("process", "")
                    r = _run_osascript(f'''
                    tell application "System Events"
                        set targetApp to first application process whose name contains "{app}"
                        set frontmost of targetApp to true
                    end tell
                    ''')
                    if r:
                        return {"ok": True, "result": f"Window '{w.get('title')}' focused"}
            return {"ok": False, "result": f"No window matching: {title}"}

        return {"ok": False, "result": "Need title, process, or pid to focus window"}

    def close_window(self, title: str | None = None, process: str | None = None, pid: int | None = None) -> Dict[str, Any]:
        """Close a window or quit an app."""
        if pid:
            r = subprocess.run(["kill", str(pid)], capture_output=True)
            return {"ok": r.returncode == 0, "result": f"Killed PID {pid}"}

        if process:
            r = _run_osascript(f'''
            tell application "{process}"
                quit
            end tell
            ''')
            if r is not None:
                return {"ok": True, "result": f"Quit app: {process}"}
            # Fallback: pkill
            r2 = subprocess.run(["pkill", "-f", process], capture_output=True)
            return {"ok": r2.returncode == 0, "result": f"pkill {process}"}

        if title:
            windows = self.get_open_windows(limit=100)
            for w in windows:
                if title.lower() in w.get("title", "").lower():
                    app = w.get("process", "")
                    return self.close_window(process=app)
            return {"ok": False, "result": f"No window matching: {title}"}

        return {"ok": False, "result": "Need title, process, or pid to close"}

    def browser_context(self) -> Dict[str, Any]:
        windows = self.get_open_windows(limit=100)
        browsers = self.get_browser_windows(windows)
        active = self.get_active_window()
        active_is_browser = any(
            str(active.get("process", "")).lower() in b.lower()
            for b in BROWSER_NAMES
        ) if active else False
        return {
            "active_is_browser": active_is_browser,
            "active_window": active,
            "browser_windows": browsers,
            "browser_count": len(browsers),
        }

    def snapshot(self) -> Dict[str, Any]:
        windows = self.get_open_windows()
        browser_windows = self.get_browser_windows(windows)
        processes = self.get_processes()
        active_window = self.get_active_window()

        return {
            "host": socket.gethostname(),
            "user": os.environ.get("USER") or "unknown",
            "cwd": str(Path.cwd()),
            "platform": "macOS",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "active_window": active_window,
            "windows": {
                "count": len(windows),
                "items": windows,
            },
            "browser_windows": {
                "count": len(browser_windows),
                "items": browser_windows,
            },
            "browser_context": self.browser_context(),
            "processes": {
                "count": len(processes),
                "items": processes,
            },
            "clipboard_text": _get_clipboard_text(),
        }
