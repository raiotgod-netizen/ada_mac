with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

new_tools = ['spotify_control', 'screen_live', 'read_system_clipboard', 'set_volume', 'send_email', 'read_document', 'shutdown_pc', 'read_inbox', 'search_inbox', 'get_system_info', 'remind_me', 'screen_action']

for i in range(len(lines)):
    line = lines[i]
    for tool in new_tools:
        if 'elif fc.name == "' + tool + '"' in line:
            print(f'{i+1}: {tool}')
