from __future__ import annotations

import json
import os
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from bluetooth_manager import BluetoothManager


def _get_clipboard_text() -> str:
    """Lee el portapapeles de Windows (solo funciona en Windows)."""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard(0)
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT) or ""
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass
    return ""


POWERSHELL = "powershell"
BROWSER_NAMES = {"chrome", "msedge", "firefox", "brave", "opera"}


class SystemObserver:
    def __init__(self, workspace_root: str | Path | None = None):
        root = workspace_root or Path(__file__).resolve().parent.parent
        self.bluetooth_manager = BluetoothManager(root)

    def _run_powershell(self, script: str, timeout: int = 8) -> str:
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

    def _run_powershell_json(self, script: str) -> List[Dict[str, Any]]:
        raw = self._run_powershell(script)
        if not raw:
            return []
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except Exception:
            return []
        return []

    def _window_script(self) -> str:
        return r"""
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class Win32 {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maxCount);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
}
"@
"""

    def get_open_windows(self, limit: int = 25) -> List[Dict[str, Any]]:
        script = self._window_script() + r"""
$items = New-Object System.Collections.Generic.List[Object]
$callback = [Win32+EnumWindowsProc]{
    param($hWnd, $lParam)
    if (-not [Win32]::IsWindowVisible($hWnd)) { return $true }
    $sb = New-Object System.Text.StringBuilder 1024
    [void][Win32]::GetWindowText($hWnd, $sb, $sb.Capacity)
    $title = $sb.ToString().Trim()
    if ([string]::IsNullOrWhiteSpace($title)) { return $true }
    $pid = 0
    [void][Win32]::GetWindowThreadProcessId($hWnd, [ref]$pid)
    $processName = ""
    try { $processName = (Get-Process -Id $pid -ErrorAction Stop).ProcessName } catch {}
    $items.Add([pscustomobject]@{ title = $title; process = $processName; pid = $pid; handle = $hWnd.ToInt64() }) | Out-Null
    return $true
}
[void][Win32]::EnumWindows($callback, [IntPtr]::Zero)
$items | Sort-Object title -Unique | Select-Object -First 50 | ConvertTo-Json -Depth 3 -Compress
"""
        return self._run_powershell_json(script)[:limit]

    def get_active_window(self) -> Dict[str, Any] | None:
        script = self._window_script() + r"""
$hWnd = [Win32]::GetForegroundWindow()
if ($hWnd -eq [IntPtr]::Zero) { return }
$sb = New-Object System.Text.StringBuilder 1024
[void][Win32]::GetWindowText($hWnd, $sb, $sb.Capacity)
$title = $sb.ToString().Trim()
$pid = 0
[void][Win32]::GetWindowThreadProcessId($hWnd, [ref]$pid)
$processName = ""
try { $processName = (Get-Process -Id $pid -ErrorAction Stop).ProcessName } catch {}
[pscustomobject]@{ title = $title; process = $processName; pid = $pid; handle = $hWnd.ToInt64() } | ConvertTo-Json -Depth 3 -Compress
"""
        items = self._run_powershell_json(script)
        return items[0] if items else None

    def get_processes(self, limit: int = 25) -> List[Dict[str, Any]]:
        script = (
            "Get-Process | Sort-Object CPU -Descending | Select-Object -First 50 "
            "Name,Id,@{Name='CPU';Expression={[math]::Round($_.CPU,2)}},"
            "@{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet64 / 1MB,1)}} "
            "| ConvertTo-Json -Depth 3 -Compress"
        )
        return self._run_powershell_json(script)[:limit]

    def get_browser_windows(self, windows: List[Dict[str, Any]] | None = None) -> List[Dict[str, Any]]:
        windows = windows if windows is not None else self.get_open_windows(limit=100)
        return [w for w in windows if str(w.get("process", "")).lower() in BROWSER_NAMES]

    def focus_window(self, title: str | None = None, process: str | None = None, pid: int | None = None) -> Dict[str, Any]:
        windows = self.get_open_windows(limit=100)
        target = None
        title_l = (title or "").strip().lower()
        process_l = (process or "").strip().lower()

        for item in windows:
            if pid and int(item.get("pid") or 0) == int(pid):
                target = item
                break
            if title_l and title_l in str(item.get("title", "")).lower():
                target = item
                break
            if process_l and process_l == str(item.get("process", "")).lower():
                target = item
                break

        if not target:
            return {"ok": False, "result": "No encontré una ventana coincidente."}

        handle = int(target.get("handle") or 0)
        script = self._window_script() + f"""
$hWnd = [IntPtr]{handle}
[Win32]::ShowWindowAsync($hWnd, 9) | Out-Null
$ok = [Win32]::SetForegroundWindow($hWnd)
[pscustomobject]@{{ ok = $ok; title = '{str(target.get('title', '')).replace("'", "''")}'; process = '{str(target.get('process', '')).replace("'", "''")}'; pid = {int(target.get('pid') or 0)} }} | ConvertTo-Json -Depth 3 -Compress
"""
        items = self._run_powershell_json(script)
        if not items:
            return {"ok": False, "result": "No pude enfocar la ventana."}
        result = items[0]
        if result.get("ok"):
            return {"ok": True, "result": f"Ventana enfocada: {result.get('title')}"}
        return {"ok": False, "result": f"No pude enfocar la ventana: {result.get('title')}"}

    def close_window(self, title: str | None = None, process: str | None = None, pid: int | None = None) -> Dict[str, Any]:
        if pid:
            script = f"try {{ Stop-Process -Id {int(pid)} -Force -ErrorAction Stop; 'ok' }} catch {{ '' }}"
        elif process:
            process_name = str(process).replace("'", "''")
            script = f"try {{ Get-Process -Name '{process_name}' -ErrorAction Stop | Stop-Process -Force -ErrorAction Stop; 'ok' }} catch {{ '' }}"
        elif title:
            title_l = title.strip().lower()
            windows = self.get_open_windows(limit=100)
            match = next((w for w in windows if title_l in str(w.get("title", "")).lower()), None)
            if not match:
                return {"ok": False, "result": "No encontré la ventana a cerrar."}
            return self.close_window(pid=int(match.get("pid") or 0))
        else:
            return {"ok": False, "result": "Falta título, proceso o pid para cerrar ventana."}

        output = self._run_powershell(script)
        if output.strip().lower() == "ok":
            return {"ok": True, "result": "Ventana o proceso cerrado."}
        return {"ok": False, "result": "No pude cerrar la ventana o proceso."}

    def browser_context(self) -> Dict[str, Any]:
        windows = self.get_open_windows(limit=100)
        browsers = self.get_browser_windows(windows)
        active = self.get_active_window()
        active_is_browser = str((active or {}).get("process", "")).lower() in BROWSER_NAMES if active else False
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
            "user": os.environ.get("USERNAME") or os.environ.get("USER") or "unknown",
            "cwd": str(Path.cwd()),
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
            "bluetooth": self.bluetooth_manager.snapshot(),
            "clipboard_text": _get_clipboard_text(),
        }
