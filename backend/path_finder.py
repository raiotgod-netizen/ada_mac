"""
PathFinder — ADA File Path Intelligence
========================================
Helps ADA locate files and resolve paths accurately on Windows.
"""

import os
import glob as glob_mod
from typing import Optional


DIEGO_LOCATIONS = [
    "C:\\Users\\raiot\\OneDrive\\Escritorio",
    "C:\\Users\\raiot\\OneDrive\\Documentos",
    "C:\\Users\\raiot\\Downloads",
    "C:\\Users\\raiot\\OneDrive",
    "C:\\Users\\raiot",
]

PROJECT_LOCATIONS = [
    "C:\\Users\\raiot\\OneDrive\\Escritorio\\ADA",
    "C:\\Users\\raiot\\OneDrive\\Escritorio\\ADA3.0",
    "C:\\Users\\raiot\\OneDrive\\Escritorio\\L.A.U.R.A",
    "C:\\Users\\raiot\\OneDrive\\Escritorio\\L.A.U.R.A\\l.a.u.r.a",
]

ALL_SEARCH_ROOTS = DIEGO_LOCATIONS + PROJECT_LOCATIONS

_file_index: dict = {}
_index_built = False


def _build_index():
    global _file_index, _index_built
    if _index_built:
        return
    _file_index.clear()
    for root in ALL_SEARCH_ROOTS:
        if not os.path.exists(root):
            continue
        try:
            for entry in os.listdir(root):
                full = os.path.join(root, entry)
                key = entry.lower()
                if key not in _file_index:
                    _file_index[key] = []
                if full not in _file_index[key]:
                    _file_index[key].append(full)
                if os.path.isdir(full):
                    try:
                        for sub in os.listdir(full)[:20]:
                            sub_full = os.path.join(full, sub)
                            sub_key = sub.lower()
                            if sub_key not in _file_index:
                                _file_index[sub_key] = []
                            if sub_full not in _file_index[sub_key]:
                                _file_index[sub_key].append(sub_full)
                    except PermissionError:
                        pass
        except PermissionError:
            pass
    _index_built = True


def find_file(name: str) -> dict:
    _build_index()
    name_lower = name.lower().strip()
    if not name_lower:
        return {"ok": False, "result": "No filename provided"}

    results = []
    if name_lower in _file_index:
        for p in _file_index[name_lower]:
            results.append({"path": p, "type": "dir" if os.path.isdir(p) else "file", "dir": os.path.dirname(p), "match": "exact"})
    for fname, paths in _file_index.items():
        if name_lower in fname and fname != name_lower:
            for p in paths:
                if not any(m["path"] == p for m in results):
                    results.append({"path": p, "type": "dir" if os.path.isdir(p) else "file", "dir": os.path.dirname(p), "match": "partial"})
    for root in ALL_SEARCH_ROOTS:
        if not os.path.exists(root):
            continue
        pattern = f"**/*{name_lower}*" if "\\" in root else f"*{name_lower}*"
        try:
            for p in glob_mod.iglob(os.path.join(root, pattern), recursive=True):
                if not any(m["path"] == p for m in results):
                    try:
                        results.append({"path": p, "type": "dir" if os.path.isdir(p) else "file", "dir": os.path.dirname(p), "match": "glob"})
                    except OSError:
                        pass
        except Exception:
            pass

    def sort_key(r):
        order = {"exact": 0, "partial": 1, "glob": 2}
        type_order = {"file": 0, "dir": 1}
        return (order.get(r["match"], 3), type_order.get(r["type"], 2), r["path"])

    results.sort(key=sort_key)
    results = results[:20]

    if not results:
        return {"ok": True, "matches": [], "result": f"No file or folder found matching '{name}'"}
    return {"ok": True, "matches": results, "count": len(results), "result": f"Found {len(results)} match(es) for '{name}'"}


def resolve_path(path: str) -> dict:
    if not path or not path.strip():
        return {"ok": False, "result": "No path provided"}
    path = path.strip()
    original = path
    if path.startswith("~"):
        path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    if not os.path.isabs(path):
        for base in [os.getcwd()] + ALL_SEARCH_ROOTS:
            candidate = os.path.normpath(os.path.join(base, path))
            if os.path.exists(candidate):
                path = candidate
                break
        else:
            path = os.path.abspath(path)
    path = os.path.normpath(path)
    exists = os.path.exists(path)
    path_type = "not_found"
    if exists:
        path_type = "dir" if os.path.isdir(path) else "file"
    return {"ok": True, "original": original, "resolved": path, "exists": exists, "type": path_type, "result": path if exists else f"Path not found: {path}"}


def list_dir(path: str = None) -> dict:
    if path:
        resolved = resolve_path(path)
        if not resolved.get("exists"):
            return {"ok": False, "result": f"Directory not found: {path}"}
        if resolved["type"] != "dir":
            return {"ok": False, "result": f"Not a directory: {path}"}
        target = resolved["resolved"]
    else:
        return {"ok": True, "path": "common_locations", "entries": [{"name": p, "type": "dir"} for p in ALL_SEARCH_ROOTS], "result": f"{len(ALL_SEARCH_ROOTS)} known locations"}
    try:
        entries = []
        for name in sorted(os.listdir(target)):
            full = os.path.join(target, name)
            try:
                entries.append({"name": name, "type": "dir" if os.path.isdir(full) else "file", "size": os.path.getsize(full) if os.path.isfile(full) else None})
            except OSError:
                entries.append({"name": name, "type": "file", "size": None})
        return {"ok": True, "path": target, "entries": entries, "count": len(entries), "result": f"{len(entries)} entries in {target}"}
    except PermissionError:
        return {"ok": False, "result": f"Permission denied: {target}"}
    except Exception as e:
        return {"ok": False, "result": f"Error listing {target}: {e}"}
