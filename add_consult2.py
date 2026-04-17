with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    content = f.read()

# Add consult_agent to allowed tools
old_list = '"set_verbosity", "screen_action"]'
new_list = '"set_verbosity", "screen_action", "consult_agent"]'
content = content.replace(old_list, new_list)
print('Updated tools list')

# Add the handler after set_verbosity
# Find the set_verbosity block and add after it
set_verbosity_block = content.find('elif fc.name == "set_verbosity"')
if set_verbosity_block == -1:
    print('ERROR: set_verbosity handler not found')
    exit(1)

# Find the end of the set_verbosity block
block_end = content.find('function_responses.append(function_response)', set_verbosity_block)
insert_point = content.find('\n                        if function_responses:', block_end)
if insert_point == -1:
    print('ERROR: Could not find insert point')
    exit(1)

handler_code = '''

                                elif fc.name == "consult_agent":
                                    msg = fc.args.get("message", "")
                                    print(f"[ADA DEBUG] [AGENT] Consulting agent: {msg[:100]}")
                                    consult_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, '.openclaw', 'workspace', 'memory', 'ada_consulta.md')
                                    os.makedirs(os.path.dirname(consult_path), exist_ok=True)
                                    with open(consult_path, 'w', encoding='utf-8') as f:
                                        f.write(f"# Consulta de ADA\\n\\n{msg}")
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": "Message sent to agent, waiting for response."}
                                    )
                                    function_responses.append(function_response)
'''

content = content[:insert_point] + handler_code + content[insert_point:]
print('Added consult_agent handler')

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(content)

print('Done')
