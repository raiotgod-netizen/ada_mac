"""
Fix indentation of receive_audio body.
The async for response in turn: loop body is empty because all handler code
is at 16 spaces (same as async for) instead of 20 spaces (inside the loop).
"""
import re

filepath = r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py'

with open(filepath, 'r', encoding='latin-1', errors='replace') as f:
    content = f.read()

lines = content.split('\n')

# Find the line "                async for response in turn:"
# and the line "                # 1. Handle Audio Data" right after it
# All lines from "# 1. Handle Audio Data" until the end of receive_audio 
# need to be indented by 4 more spaces.

# Find async for response in turn:
start_idx = None
for i, line in enumerate(lines):
    if 'async for response in turn:' in line:
        start_idx = i
        break

if start_idx is None:
    print("ERROR: Could not find 'async for response in turn:'")
    exit(1)

print(f"Found 'async for response in turn:' at line {start_idx + 1}")
print(f"Line content: {repr(lines[start_idx])}")
print(f"Next line: {repr(lines[start_idx + 1])}")

# The next line should be "# 1. Handle Audio Data" at 16 spaces
# We need to indent it and all subsequent lines in receive_audio by 4 spaces
# until we hit the except/finally at the same level as the try:

# Find where receive_audio ends (at the except line of this function)
# We look for the except that matches the try at indentation 8 spaces inside receive_audio
# receive_audio starts at 8 spaces indent
# The try: is at 8 spaces
# The while True: is at 12 spaces  
# The async for is at 16 spaces
# We need to find where the except: for this try: is

# Strategy: find the end of the receive_audio function by finding where 
# the next function definition appears at 8 spaces indent, or the except at 8 spaces

end_idx = len(lines)
for i in range(start_idx + 1, len(lines)):
    line = lines[i]
    # Stop at the next top-level function/class or the except for this try
    if line.startswith('    async def ') or line.startswith('    def ') or line.startswith('class '):
        end_idx = i
        break
    # Also stop at the except that matches the try at 8 spaces indent inside receive_audio
    # Actually, the try is at 8 spaces, its except should be at 8 spaces
    # But we want to indent everything from line start_idx+1 to the except
    if line.strip().startswith('except ') and not line.startswith('        '):
        # This is an except at the function body level (8 spaces)
        end_idx = i
        break

print(f"Will re-indent lines {start_idx + 2} to {end_idx} (0-indexed: {start_idx + 1} to {end_idx - 1})")

# Re-indent lines from start_idx+1 to end_idx-1 by adding 4 spaces
fixed_lines = lines[:]
for i in range(start_idx + 1, end_idx):
    line = lines[i]
    if line.strip():  # Only indent non-empty lines
        fixed_lines[i] = '    ' + line  # Add 4 spaces
    # Empty lines stay as-is

fixed_content = '\n'.join(fixed_lines)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Done!")
print(f"Lines modified: {end_idx - start_idx - 1}")
