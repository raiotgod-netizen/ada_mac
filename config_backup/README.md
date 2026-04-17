# ADA V2 — Config Audit / Inventory

**Date:** 2026-04-14
**Source:** C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2
**Backup:** config_backup/ (copias de las configs con todas las tools)

---

## Archivos restored to EDITH (audio/voz base)

| Archivo | Estado |
|---------|--------|
| `backend/ada.py` | ⚠️ Copiado de EDITH — solo 14 tools base (CAD/Kasa/Printer/Web) |
| `backend/server.py` | ⚠️ Copiado de EDITH — sin Ollama fallback |

### Fixes aplicados al copy-from-EDITH:
1. Removido `from tool_executor import ToolExecutor` (no existe en ADA)
2. Removido `self.tool_executor = ToolExecutor({})` (no existe)
3. `turn = await self.session.receive()` — await ADDED en línea 644

---

## Archivos en config_backup/

| Archivo | Descripción |
|---------|-------------|
| `settings.json` | Permissions, tool config |
| `tools.py` | Las 29 tools definitions completas |
| `ada.py_with_all_29_tools` | Version con los 29 tool handlers y implementations (LA BUENA) |
| `desktop_automation.py` | Implementaciones de 26 tools adicionales |

---

## Las 29 Tools en tools.py

### ✅ Ya activas (14) — via agentes / sin implementar extra
```
generate_cad          → CadAgent.iterate_prototype()
run_web_agent         → WebAgent.run()
write_file            → project_manager
read_directory       → project_manager
read_file            → project_manager
create_project       → project_manager
switch_project       → project_manager
list_projects        → project_manager
list_smart_devices   → KasaAgent
control_light        → KasaAgent
discover_printers     → PrinterAgent
print_stl            → PrinterAgent
get_print_status     → PrinterAgent
iterate_cad          → CadAgent
```

### ⏳ Pendientes (15) — en tools.py pero desconectadas en ada.py

```
spotify_control      → desktop_automation.py.spotify_control()           [sync]
screen_live          → desktop_automation.py._get_screen_frame()          [sync]
set_volume           → desktop_automation.py.set_volume()                [sync]
read_system_clipboard→ desktop_automation.py.read_clipboard()             [sync]
analyze_document     → desktop_automation.py.analyze_document()           [sync]
create_excel          → desktop_automation.py.create_excel()             [sync]
create_word           → desktop_automation.py.create_word()               [sync]
create_powerpoint     → desktop_automation.py.create_powerpoint()        [sync]
edit_document        → desktop_automation.py.edit_document()              [sync]
shutdown_pc          → desktop_automation.py.shutdown_pc()                [sync]
get_system_info      → desktop_automation.py.get_system_info()          [sync]
remind_me            → desktop_automation.py.remind_me()                 [sync]
send_email           → desktop_automation.py.send_email()                [sync]
read_document        → desktop_automation.py.read_document()           [sync]
set_verbosity        → desktop_automation.py.set_verbosity()            [sync]
```

### ❌ Pendientes sin implementación (10) — en tools.py, ni en ada.py ni desktop_automation.py

```
read_inbox           → NI ada.py NI desktop_automation.py
search_inbox         → NI ada.py NI desktop_automation.py
close_window         → NI ada.py NI desktop_automation.py
focus_window         → NI ada.py NI desktop_automation.py
run_command          → NI ada.py NI desktop_automation.py
run_python          → NI ada.py NI desktop_automation.py
screen_action       → NI ada.py NI desktop_automation.py
observe_system_state→ NI ada.py NI desktop_automation.py
generate_cad_prototype → desktop_automation.py (stub check needed)
```

---

## Patrón para reconectar una tool

1. Agregar el nombre de la tool al filter `if fc.name in [...]` en ada.py línea 723
2. Agregar un `elif fc.name == "toolname":` handler en ada.py
3. Llamar al método en desktop_automation.py (que es sync → wrap con asyncio.to_thread si es necesario en ada.py)
4. Opcionalmente agregar `on_*` callback para feedback al frontend

---

## Para restaurar la versión completa (29 tools)

Copiar desde `config_backup/ada.py_with_all_29_tools` a `backend/ada.py`, luego:
1. Agregar `await` en línea 644: `turn = await self.session.receive()`
2. Remover `from tool_executor import ToolExecutor` y `self.tool_executor = ToolExecutor({})`

