with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'r') as f:
    content = f.read()

# Add the tool definition before tools_list
content = content.replace(
    'tools_list = [',
    '''consult_agent_tool = {
    "name": "consult_agent",
    "description": "Sends a message to the agent to request advice or help with a task. The agent will respond in a shared file. Use this when you need guidance or want to delegate something.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {
                "type": "STRING",
                "description": "The message to send to the agent."
            }
        },
        "required": ["message"]
    }
}

tools_list = ['''
)

# Add to tools_list
content = content.replace(
    '    set_verbosity_tool,\n]',
    '    set_verbosity_tool,\n    consult_agent_tool,\n]'
)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'w') as f:
    f.write(content)

print('tools.py updated')
