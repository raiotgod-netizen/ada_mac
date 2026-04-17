import re

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\tools.py', 'r') as f:
    content = f.read()

# Find send_email, read_inbox, search_inbox definitions
for tool_name in ['send_email', 'read_inbox', 'search_inbox', 'get_system_info', 'remind_me', 'screen_action', 'read_document', 'spotify_control', 'screen_live', 'read_system_clipboard', 'set_volume', 'shutdown_pc']:
    pattern = rf'"{tool_name}"'
    idx = content.find(pattern)
    if idx >= 0:
        print(f'=== {tool_name} ===')
        print(content[idx:idx+300])
        print('---')
    else:
        print(f'{tool_name}: NOT FOUND')
