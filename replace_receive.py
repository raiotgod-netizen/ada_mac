with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\receive_audio_edith.txt', 'r') as f:
    edith_content = f.read()

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    ada_lines = f.readlines()

# Find the exact range of receive_audio in ADA_v2
start_idx = None
end_idx = None
for i in range(len(ada_lines)):
    line = ada_lines[i]
    if 'async def receive_audio' in line and 'def receive_audio' in line:
        start_idx = i
    if start_idx is not None and i > start_idx:
        if line.strip() and not line.strip().startswith('#'):
            indent = len(line) - len(line.lstrip())
            if indent == 4 and ('async def ' in line or 'def ' in line):
                end_idx = i
                break

print(f'Will replace lines {start_idx+1} to {end_idx} ({end_idx-start_idx} lines)')

# Build new file
new_content = ''.join(ada_lines[:start_idx]) + edith_content + '\n' + ''.join(ada_lines[end_idx:])

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(new_content)

print(f'Done. New file has {len(new_content.splitlines())} lines')
