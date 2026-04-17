from __future__ import annotations

from typing import Any, Dict


class ActionDispatcher:
    def __init__(self, system_observer, desktop_automation, global_memory, routine_manager=None, vision_provider=None, security_audit=None, bluetooth_manager=None):
        self.system_observer = system_observer
        self.desktop_automation = desktop_automation
        self.global_memory = global_memory
        self.routine_manager = routine_manager
        self.vision_provider = vision_provider
        self.security_audit = security_audit
        self.bluetooth_manager = bluetooth_manager

    def dispatch(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        intent = plan.get("intent")
        goal = (plan.get("goal") or "").lower()
        tools = plan.get("tools", []) or []

        if intent == "system_observation" or "observe_system_state" in tools:
            result = self.system_observer.snapshot()
            return {"ok": True, "mode": "direct", "result": f"{result['windows']['count']} ventanas, {result['processes']['count']} procesos", "data": result}

        if intent == "desktop_macro" and "list_saved_macros" in tools and any(token in goal for token in ["lista", "muestra", "ver macros"]):
            macros = self.global_memory.list_macros()
            return {"ok": True, "mode": "direct", "result": f"Macros disponibles: {len(macros)}", "data": macros}

        if intent == "desktop_macro" and "run_saved_macro" in tools:
            for macro in self.global_memory.list_macros():
                name = str(macro.get("name", "")).lower()
                if name and name in goal:
                    result = self.desktop_automation.run_sequence(macro.get("steps", []))
                    return {"ok": result.get("ok", False), "mode": "direct", "result": result.get("result"), "data": result}

        if intent == "background_job" and self.routine_manager and any(token in goal for token in ["rutina", "routine", "recordatorio", "seguimiento"]):
            interval_seconds = 300
            if any(token in goal for token in ["cada hora", "cada 1 hora"]):
                interval_seconds = 3600
            elif any(token in goal for token in ["cada 10 minutos", "cada diez minutos"]):
                interval_seconds = 600
            elif any(token in goal for token in ["cada 5 minutos", "cada cinco minutos"]):
                interval_seconds = 300
            routine = self.routine_manager.create_routine(
                name=plan.get("goal", "rutina")[:48],
                goal=plan.get("goal", ""),
                interval_seconds=interval_seconds,
                metadata={"intent": intent, "tools": tools, "source": "dispatcher"},
                schedule_type="interval",
            )
            return {"ok": True, "mode": "direct", "result": f"Rutina creada: {routine['id']}", "data": routine}

        if intent == "security_audit" and self.security_audit and any(token in goal for token in ["audita", "audit", "inventario", "estado del sistema", "diagnóstico"]):
            snapshot = self.security_audit.host_inventory()
            network = self.security_audit.network_snapshot()
            startup = self.security_audit.startup_snapshot()
            disk = self.security_audit.disk_snapshot()
            return {"ok": True, "mode": "direct", "result": "Auditoría defensiva completada.", "data": {"host": snapshot, "network": network, "startup": startup, "disk": disk}}

        if self.bluetooth_manager and any(token in goal for token in ["bluetooth", "bluetooths", "dispositivo bluetooth", "audífono", "mouse bluetooth", "teclado bluetooth"]):
            if any(token in goal for token in ["conectados", "connected"]):
                data = self.bluetooth_manager.connected_devices()
                return {"ok": True, "mode": "direct", "result": f"Dispositivos Bluetooth conectados: {len(data)}", "data": data}
            if any(token in goal for token in ["emparejados", "paired", "vinculados"]):
                data = self.bluetooth_manager.paired_devices()
                return {"ok": True, "mode": "direct", "result": f"Dispositivos Bluetooth emparejados: {len(data)}", "data": data}
            if any(token in goal for token in ["adaptador", "radio", "estado bluetooth"]):
                data = self.bluetooth_manager.adapter_status()
                return {"ok": True, "mode": "direct", "result": "Estado del adaptador Bluetooth obtenido.", "data": data}
            if any(token in goal for token in ["inventario", "lista", "mostrar bluetooth"]):
                data = self.bluetooth_manager.inventory()
                return {"ok": True, "mode": "direct", "result": "Inventario Bluetooth actualizado.", "data": data}

        if intent == "desktop_control" and self.vision_provider and any(token in goal for token in ["centrar mouse", "mueve el mouse al centro", "lleva el mouse al centro"]):
            vision = self.vision_provider() or {}
            screen = vision.get("screen") or {}
            width = int(screen.get("width") or 0)
            height = int(screen.get("height") or 0)
            if width > 0 and height > 0:
                result = self.desktop_automation.move_mouse(width // 2, height // 2)
                return {"ok": result.get("ok", False), "mode": "direct", "result": result.get("result"), "data": {"vision": vision, "action": "move_mouse_center"}}

        if self.vision_provider and any(token in goal for token in ["mueve al buscador", "mueve al primer resultado", "guíate por la pantalla", "usa visión", "apunta al video"]):
            vision = self.vision_provider() or {}
            targets = ((vision.get("screen") or {}).get("suggested_targets") or [])
            target = None
            if any(token in goal for token in ["buscador", "barra"]):
                target = next((t for t in targets if t.get("name") == "top_search_bar"), None)
            elif any(token in goal for token in ["primer resultado", "resultado"]):
                target = next((t for t in targets if t.get("name") == "upper_results"), None)
            elif any(token in goal for token in ["video", "contenido"]):
                target = next((t for t in targets if t.get("name") == "center_content"), None)
            if target:
                result = self.desktop_automation.move_mouse(target.get("x", 0), target.get("y", 0), 0.2)
                return {"ok": result.get("ok", False), "mode": "direct", "result": f"Mouse guiado por visión a {target.get('name')}", "data": {"vision": vision, "target": target, "action": "vision_guided_mouse_move", "next_action": {"action": "vision_guided_click", "target": target, "confirm": False}}}

        if intent == "browser_navigation" and "open_url" in tools:
            url = None
            for token in goal.split():
                if token.startswith("http://") or token.startswith("https://"):
                    url = token
                    break
            if not url and "google" in goal:
                url = "https://google.com"
            if not url and "youtube" in goal:
                url = "https://youtube.com"
            if url:
                result = self.desktop_automation.open_url(url)
                return {"ok": result.get("ok", False), "mode": "direct", "result": result.get("result"), "data": result}

        if any(token in goal for token in ["buscar en youtube", "video en youtube", "abrir primer video", "primer video de youtube"]):
            browser_context = self.system_observer.browser_context()
            query = plan.get("goal", "").lower().replace("buscar en youtube", "").replace("video en youtube", "").replace("abrir primer video", "").strip(' :,-')
            result = self.desktop_automation.search_and_open_first_youtube_video(query or "video")
            return {
                "ok": result.get("ok", False),
                "mode": "direct",
                "result": result.get("result"),
                "data": {"browser_context": browser_context, "query": query or "video", "action": "search_and_open_first_youtube_video"}
            }

        if any(token in goal for token in ["buscar en google", "abre el primer resultado", "primer resultado de google"]):
            browser_context = self.system_observer.browser_context()
            query = plan.get("goal", "").lower().replace("buscar en google", "").replace("abre el primer resultado", "").strip(' :,-')
            result = self.desktop_automation.search_and_open_first_google_result(query or "búsqueda")
            return {
                "ok": result.get("ok", False),
                "mode": "direct",
                "result": result.get("result"),
                "data": {"browser_context": browser_context, "query": query or "búsqueda", "action": "search_and_open_first_google_result"}
            }

        if self.routine_manager and any(token in goal for token in ["buscar web", "selecciona video", "abrir resultado"]):
            browser_context = self.system_observer.browser_context()
            return {
                "ok": True,
                "mode": "direct",
                "result": "Control web local preparado para navegador activo.",
                "data": {
                    "browser_context": browser_context,
                    "suggested_actions": [
                        "focus_window",
                        "open_google_search",
                        "open_youtube_search",
                        "search_in_browser",
                        "open_first_result_with_keyboard",
                        "run_saved_macro"
                    ]
                }
            }

        return {"ok": False, "mode": "defer_to_model", "result": "No direct dispatch match."}
