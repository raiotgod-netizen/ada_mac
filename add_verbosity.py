"""
Add verbosity control to ADA.
- Adds set_verbosity tool to tools.py
- Adds _verbosity state to AudioLoop
- Adds handler in receive_audio
- Updates jarvis_personality.txt with verbosity instructions
"""

import os

# ==== 1. Add set_verbosity_tool to tools.py ====
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'r') as f:
    tools_content = f.read()

verbosity_tool = '''set_verbosity_tool = {
    "name": "set_verbosity",
    "description": "Sets how verbose ADA's responses should be. Use 'brief' for short answers, 'normal' for standard responses, or 'detailed' for comprehensive explanations. This affects only the level of detail in ADA's verbal responses.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "level": {
                "type": "STRING",
                "description": "Verbosity level: 'brief' (short answers), 'normal' (standard responses), or 'detailed' (comprehensive explanations).",
                "enum": ["brief", "normal", "detailed"]
            }
        },
        "required": ["level"]
    }
}

'''

# Insert before tools_list
tools_content = tools_content.replace(
    'tools_list = [{"function_declarations": [',
    verbosity_tool + 'tools_list = [{"function_declarations": ['
)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'w') as f:
    f.write(tools_content)

print("Added set_verbosity_tool to tools.py")

# ==== 2. Add to tools_list in tools.py ====
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'r') as f:
    tools_content = f.read()

# Add to the function declarations list (after screen_action_tool)
tools_content = tools_content.replace(
    '    screen_action_tool,\n]',
    '    screen_action_tool,\n    set_verbosity_tool,\n]'
)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'w') as f:
    f.write(tools_content)

print("Added set_verbosity to tools_list")

# ==== 3. Add verbosity state to AudioLoop __init__ ====
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    ada_content = f.read()

# Add _verbosity after _last_user_speech_interrupt
ada_content = ada_content.replace(
    'self._last_user_speech_interrupt = 0  # timestamp',
    'self._last_user_speech_interrupt = 0  # timestamp\n        self._verbosity = "normal"  # verbosity level: brief, normal, detailed'
)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(ada_content)

print("Added _verbosity state to AudioLoop")

# ==== 4. Add set_verbosity to the allowed tools list in receive_audio ====
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    ada_content = f.read()

# Add set_verbosity to the allowed tools list
old_list = '["generate_cad", "run_web_agent", "write_file", "read_directory", "read_file", "create_project", "switch_project", "list_projects", "list_smart_devices", "control_light", "discover_printers", "print_stl", "get_print_status", "iterate_cad", "spotify_control", "screen_live", "read_system_clipboard", "set_volume", "send_email", "read_document", "shutdown_pc", "read_inbox", "search_inbox", "get_system_info", "remind_me", "screen_action"]'

new_list = '["generate_cad", "run_web_agent", "write_file", "read_directory", "read_file", "create_project", "switch_project", "list_projects", "list_smart_devices", "control_light", "discover_printers", "print_stl", "get_print_status", "iterate_cad", "spotify_control", "screen_live", "read_system_clipboard", "set_volume", "send_email", "read_document", "shutdown_pc", "read_inbox", "search_inbox", "get_system_info", "remind_me", "screen_action", "set_verbosity"]'

ada_content = ada_content.replace(old_list, new_list)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(ada_content)

print("Added set_verbosity to allowed tools list")

# ==== 5. Add handler for set_verbosity (after screen_action block) ====
with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    ada_content = f.read()

verbosity_handler = '''
                                elif fc.name == "set_verbosity":
                                    level = fc.args.get("level", "normal")
                                    if level in ["brief", "normal", "detailed"]:
                                        self._verbosity = level
                                        print(f"[ADA DEBUG] [VERB] Verbosity set to '{level}'")
                                        result_text = f"Verbosity set to '{level}'."
                                    else:
                                        result_text = f"Unknown verbosity level '{level}'. Use brief, normal, or detailed."
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": result_text}
                                    )
                                    function_responses.append(function_response)'''

# Insert after screen_action block
ada_content = ada_content.replace(
    '''                                elif fc.name == "screen_action":
                                    action = fc.args.get("action", "")
                                    target = fc.args.get("target", "")
                                    params = fc.args.get("params", {})
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'screen_action' action='{action}' target='{target}'")
                                    asyncio.create_task(self.handle_screen_action(action, target, params))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": f"Screen action '{action}' started"}
                                    )
                                    function_responses.append(function_response)''',
    '''                                elif fc.name == "screen_action":
                                    action = fc.args.get("action", "")
                                    target = fc.args.get("target", "")
                                    params = fc.args.get("params", {})
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'screen_action' action='{action}' target='{target}'")
                                    asyncio.create_task(self.handle_screen_action(action, target, params))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": f"Screen action '{action}' started"}
                                    )
                                    function_responses.append(function_response)''' + verbosity_handler
)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(ada_content)

print("Added set_verbosity handler")

# ==== 6. Update jarvis_personality.txt with verbosity instructions ====
jarvis_path = r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\jarvis_personality.txt'
with open(jarvis_path, 'r', encoding='utf-8') as f:
    jarvis_content = f.read()

verbosity_section = '''

## Verbosity Control
The user can ask you to change how verbose you are:
- "be brief" / "short answers" / "summarize" → Use brief mode: 1-2 sentences max
- "give me details" / "be thorough" / "explain fully" → Use detailed mode: full explanations
- "normal" / "standard" → Default verbosity level

When in brief mode: skip pleasantries, get to the point, omit caveats unless relevant.
When in detailed mode: include context, caveats, alternatives, and thorough explanations.
'''

if 'Verbosity Control' not in jarvis_content:
    jarvis_content += verbosity_section
    with open(jarvis_path, 'w', encoding='utf-8') as f:
        f.write(jarvis_content)
    print("Updated jarvis_personality.txt")

print("\nVerbosity control installed successfully!")
print("Compile check:")
