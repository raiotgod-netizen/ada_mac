from typing import Dict, Any

from capability_framework import CapabilityFramework
from skill_registry import SkillRegistry


class Orchestrator:
    def __init__(self, workspace_root: str | None = None):
        root = workspace_root or __import__('pathlib').Path(__file__).resolve().parent.parent
        self.capability_framework = CapabilityFramework(root)
        self.skill_registry = SkillRegistry(root)
        self.last_plan: Dict[str, Any] = {
            "intent": "idle",
            "route": "conversation",
            "confidence": 0.0,
            "tools": [],
        }

    def analyze_text(self, text: str) -> Dict[str, Any]:
        t = (text or "").strip().lower()
        plan = {
            "intent": "conversation",
            "route": "conversation",
            "confidence": 0.55,
            "tools": [],
        }

        if any(token in t for token in ["archivo", "carpeta", "lee ", "escribe ", "guardar"]):
            plan = {
                "intent": "filesystem",
                "route": "tooling",
                "confidence": 0.7,
                "tools": ["read_file", "write_file", "read_directory"],
            }
        elif any(token in t for token in ["navega", "busca", "abre la web", "browser", "web"]):
            plan = {
                "intent": "web_task",
                "route": "tooling",
                "confidence": 0.78,
                "tools": ["run_web_agent"],
            }
        elif any(token in t for token in ["cad", "stl", "modelo 3d", "imprime", "printer"]):
            plan = {
                "intent": "fabrication",
                "route": "tooling",
                "confidence": 0.8,
                "tools": ["generate_cad", "iterate_cad", "print_stl"],
            }
        elif any(token in t for token in ["luz", "kasa", "enchufe", "smart home"]):
            plan = {
                "intent": "smart_home",
                "route": "tooling",
                "confidence": 0.82,
                "tools": ["list_smart_devices", "control_light"],
            }
        elif any(token in t for token in ["descarga", "descargar", "download", "baja este archivo"]):
            plan = {
                "intent": "download",
                "route": "web_transfer",
                "confidence": 0.87,
                "tools": ["download_file"],
            }
        elif any(token in t for token in ["sube este archivo", "subir archivo", "upload", "cargar archivo a internet"]):
            plan = {
                "intent": "upload",
                "route": "web_transfer",
                "confidence": 0.87,
                "tools": ["upload_file_to_web"],
            }
        elif any(token in t for token in ["correo", "mail", "gmail", "email", "manda un correo", "enviar correo"]):
            plan = {
                "intent": "email",
                "route": "communications",
                "confidence": 0.86,
                "tools": ["send_email"],
            }
        elif any(token in t for token in ["word", "excel", "powerpoint", "ppt", "docx", "xlsx", "documento", "presentación"]):
            plan = {
                "intent": "office_productivity",
                "route": "tooling",
                "confidence": 0.84,
                "tools": ["create_word_document", "create_excel_workbook", "create_powerpoint_presentation"],
            }
        elif any(token in t for token in ["apaga el pc", "apagar mi pc", "apaga mi pc", "shutdown", "apagar el computador", "apagar el ordenador"]):
            plan = {
                "intent": "power_control",
                "route": "system_control",
                "confidence": 0.95,
                "tools": ["shutdown_pc"],
            }
        elif any(token in t for token in ["guarda esta macro", "guarda esta secuencia", "macro guardada", "ejecuta la macro", "lista macros"]):
            plan = {
                "intent": "desktop_macro",
                "route": "system_control",
                "confidence": 0.96,
                "tools": ["save_desktop_macro", "run_saved_macro", "list_saved_macros"],
            }
        elif any(token in t for token in ["haz esta secuencia", "ejecuta esta secuencia", "macro", "automatiza esta serie", "haz estos pasos", "secuencia de escritorio"]):
            plan = {
                "intent": "desktop_sequence",
                "route": "system_control",
                "confidence": 0.95,
                "tools": ["run_desktop_sequence", "focus_window", "open_url"],
            }
        elif any(token in t for token in ["mueve el mouse", "mueve el cursor", "haz click", "clic", "escribe en", "teclea", "pulsa", "presiona la tecla", "atajo", "hotkey", "scroll", "desplaza"]):
            plan = {
                "intent": "desktop_automation",
                "route": "system_control",
                "confidence": 0.94,
                "tools": ["move_mouse", "click_mouse", "type_text", "press_hotkey", "scroll_desktop", "focus_window"],
            }
        elif any(token in t for token in ["abre esta url", "abre la pagina", "abre el sitio", "ve a https", "ve a http", "abre youtube", "abre google"]):
            plan = {
                "intent": "browser_navigation",
                "route": "system_control",
                "confidence": 0.91,
                "tools": ["open_url", "focus_window"],
            }
        elif any(token in t for token in ["enfoca la ventana", "cambia a la ventana", "trae al frente", "pon en primer plano"]):
            plan = {
                "intent": "window_focus",
                "route": "system_control",
                "confidence": 0.92,
                "tools": ["focus_window", "observe_system_state"],
            }
        elif any(token in t for token in ["cierra la ventana", "cierra ese programa", "cierra chrome", "cierra edge", "cierra visual studio", "cierra vscode"]):
            plan = {
                "intent": "window_close",
                "route": "system_control",
                "confidence": 0.92,
                "tools": ["close_window", "observe_system_state"],
            }
        elif any(token in t for token in ["ventanas abiertas", "programas abiertos", "procesos", "estado del pc", "estado de mi pc", "chrome abierto", "google abierto", "que ventanas", "qué ventanas", "ventana activa", "programa activo"]):
            plan = {
                "intent": "system_observation",
                "route": "system_control",
                "confidence": 0.9,
                "tools": ["observe_system_state"],
            }
        elif any(token in t for token in ["pantalla", "screen", "captura", "lo que veo", "tiempo real"]):
            plan = {
                "intent": "screen_context",
                "route": "vision",
                "confidence": 0.8,
                "tools": ["capture_screen_snapshot", "observe_system_state"],
            }
        elif any(token in t for token in ["mejora", "mejorate", "auto implement", "auto-mejora", "perfecciona", "jarvis"]):
            plan = {
                "intent": "self_improvement",
                "route": "supervised_evolution",
                "confidence": 0.88,
                "tools": ["propose_self_improvement", "create_custom_script", "write_file"],
            }
        elif any(token in t for token in ["script", "automatiza", "ejecuta"]):
            plan = {
                "intent": "automation",
                "route": "tooling",
                "confidence": 0.74,
                "tools": ["run_custom_script", "create_custom_script"],
            }

        plan["tools"] = self._filter_tools(plan.get("tools", []))
        if not plan["tools"] and plan.get("route") != "conversation":
            plan = {
                "intent": "conversation",
                "route": "conversation",
                "confidence": 0.4,
                "tools": [],
                "reason": "capability_filtered"
            }
        self.last_plan = plan
        return plan

    def _filter_tools(self, tools):
        snapshot = self.capability_framework.snapshot()
        enabled_tools = {item.get("name") for item in snapshot.get("tools", []) if item.get("enabled")}
        enabled_skills = {item.get("id") for item in snapshot.get("skills", []) if item.get("enabled")}
        filtered = []
        for tool in tools or []:
            if tool not in enabled_tools:
                continue
            if tool in {"send_email"} and "email" not in enabled_skills:
                continue
            if tool in {"move_mouse", "click_mouse", "type_text", "press_hotkey", "focus_window", "open_url", "run_desktop_sequence"} and "desktop" not in enabled_skills:
                continue
            if tool in {"capture_screen_snapshot"} and "vision" not in enabled_skills:
                continue
            if tool in {"propose_self_improvement", "create_custom_script", "write_file"} and "improvement" not in enabled_skills:
                continue
            filtered.append(tool)
        return filtered

    def snapshot(self):
        return dict(self.last_plan)
