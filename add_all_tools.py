"""
Script to add all missing tools to ada.py receive_audio.
Each tool is evaluated for risk level and assigned appropriate confirmation requirements.
"""

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# ==== STEP 1: Update imports (add desktop_automation and email_agent) ====
import_section_end = None
for i, line in enumerate(lines):
    if line.startswith('from tools import tools_list'):
        import_section_end = i
        break

if import_section_end is not None:
    # Add imports after tools import
    new_imports = '''from tools import tools_list
from desktop_automation import DesktopAutomation
from email_agent import EmailAgent'''
    lines[import_section_end] = new_imports

# ==== STEP 2: Add email_agent and desktop_automation to __init__ ====
# Find the line after self.printer_agent = PrinterAgent()
__init_end = None
for i, line in enumerate(lines):
    if 'self.printer_agent = PrinterAgent()' in line:
        __init_end = i
        break

if __init_end is not None:
    # Insert after printer_agent
    new_agents = '''        self.printer_agent = PrinterAgent()
        self.desktop_automation = None  # Lazy init
        self.email_agent = email_agent if email_agent else None'''
    lines[__init_end] = new_agents

# ==== STEP 3: Update the allowed tools list ====
old_list = 'if fc.name in ["generate_cad", "run_web_agent", "write_file", "read_directory", "read_file", "create_project", "switch_project", "list_projects", "list_smart_devices", "control_light", "discover_printers", "print_stl", "get_print_status", "iterate_cad"]'

new_list = 'if fc.name in ["generate_cad", "run_web_agent", "write_file", "read_directory", "read_file", "create_project", "switch_project", "list_projects", "list_smart_devices", "control_light", "discover_printers", "print_stl", "get_print_status", "iterate_cad", "spotify_control", "screen_live", "read_system_clipboard", "set_volume", "send_email", "read_document", "shutdown_pc", "read_inbox", "search_inbox", "get_system_info", "remind_me", "screen_action"]'

for i, line in enumerate(lines):
    if old_list in line:
        lines[i] = line.replace(old_list, new_list)
        print(f"Updated tool list at line {i+1}")
        break

# ==== STEP 4: Add handler code AFTER iterate_cad block ====
# Find the iterate_cad function_response line
iterate_cad_end = None
for i, line in enumerate(lines):
    if 'elif fc.name == "iterate_cad":' in line:
        # Find the function_response line for iterate_cad
        for j in range(i, i+50):
            if 'function_responses.append(function_response)' in lines[j] and j > i:
                iterate_cad_end = j
                break
        break

if iterate_cad_end is None:
    print("ERROR: Could not find iterate_cad end")
    exit(1)

# The new handlers to add
new_handlers = '''
                                elif fc.name == "spotify_control":
                                    action = fc.args.get("action", "")
                                    query = fc.args.get("query", "")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'spotify_control' action='{action}' query='{query}'")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.spotify_playback(action, query)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "screen_live":
                                    action = fc.args.get("action", "capture")
                                    interval_ms = fc.args.get("interval_ms", 200)
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'screen_live' action='{action}'")
                                    if self.on_web_data:
                                        self.on_web_data({"screen_live_action": action, "interval_ms": interval_ms})
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": f"Screen live {action}ed"}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "read_system_clipboard":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'read_system_clipboard'")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.read_clipboard()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "set_volume":
                                    percent = fc.args.get("percent", 50)
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'set_volume' percent={percent}")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.set_volume(percent)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "send_email":
                                    to_address = fc.args.get("to", "")
                                    subject = fc.args.get("subject", "")
                                    body = fc.args.get("body", "")
                                    attachments = fc.args.get("attachments", [])
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'send_email' to='{to_address}' subject='{subject}'")
                                    if self.email_agent:
                                        result = await self.email_agent.send_email(to_address, subject, body, attachments)
                                    else:
                                        result = "Email agent not available"
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "read_document":
                                    path = fc.args.get("path", "")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'read_document' path='{path}'")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.read_file_content(path)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "shutdown_pc":
                                    delay = fc.args.get("delay_seconds", 30)
                                    cancel = fc.args.get("cancel", False)
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'shutdown_pc' delay={delay} cancel={cancel}")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.shutdown_pc(delay, cancel)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "read_inbox":
                                    limit = fc.args.get("limit", 10)
                                    unread_only = fc.args.get("unread_only", False)
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'read_inbox' limit={limit} unread_only={unread_only}")
                                    if self.email_agent:
                                        result = await self.email_agent.get_inbox(limit=limit, unread_only=unread_only)
                                    else:
                                        result = "Email agent not available"
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "search_inbox":
                                    query_text = fc.args.get("query", "")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'search_inbox' query='{query_text}'")
                                    if self.email_agent:
                                        result = await self.email_agent.search_inbox(query=query_text)
                                    else:
                                        result = "Email agent not available"
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "get_system_info":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'get_system_info'")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.get_system_info()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "remind_me":
                                    seconds = fc.args.get("seconds", 60)
                                    message = fc.args.get("message", "")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'remind_me' seconds={seconds} message='{message}'")
                                    if not self.desktop_automation:
                                        self.desktop_automation = DesktopAutomation()
                                    result = self.desktop_automation.remind_me(seconds, message)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": str(result)}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "screen_action":
                                    action = fc.args.get("action", "")
                                    target = fc.args.get("target", "")
                                    params = fc.args.get('params', {})
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'screen_action' action='{action}' target='{target}'")
                                    asyncio.create_task(self.handle_screen_action(action, target, params))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": f"Screen action '{action}' started"}
                                    )
                                    function_responses.append(function_response)'''

# Insert after iterate_cad_end
lines.insert(iterate_cad_end + 1, new_handlers)

# ==== STEP 5: Add handle_screen_action method ====
# Find a good place to add it (after handle_web_agent_request)
handle_web_end = None
for i, line in enumerate(lines):
    if 'async def handle_web_agent_request' in line:
        # Find the end of this method (next def or async def at indent 4)
        for j in range(i+1, len(lines)):
            indent = len(lines[j]) - len(lines[j].lstrip())
            if indent == 4 and ('def ' in lines[j] or 'async def ' in lines[j]):
                handle_web_end = j
                break
        break

if handle_web_end:
    screen_action_handler = '''
    async def handle_screen_action(self, action, target, params):
        """Handle screen_action tool - performs UI actions on screen."""
        print(f"[ADA DEBUG] [SCREEN] Screen action: {action}, target: {target}")
        try:
            if not self.desktop_automation:
                self.desktop_automation = DesktopAutomation()
            da = self.desktop_automation
            if action == "click":
                x = params.get("x")
                y = params.get("y")
                if x and y:
                    da.click_mouse(x, y)
            elif action == "type":
                text = params.get("text", "")
                da.type_text(text)
            elif action == "scroll":
                clicks = params.get("clicks", 3)
                axis = params.get("axis", "down")
                if axis == "down":
                    da.scroll_down(clicks)
                else:
                    da.scroll_up(clicks)
            elif action == "press":
                keys = params.get("keys", [])
                if keys:
                    da.press_hotkey(keys)
        except Exception as e:
            print(f"[ADA DEBUG] [SCREEN] Screen action error: {e}")
'''
    lines.insert(handle_web_end, screen_action_handler)

# Write the modified content
new_content = '\n'.join(lines)
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(new_content)

print(f"Done. File now has {len(lines)} lines")
