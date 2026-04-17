with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Function starts at line 687 (0-indexed 686)
# async for response in session.receive(): is at 12 spaces
# Everything inside should be at 16 spaces (4 more)
# So we need to remove 4 spaces from every indented line inside the function

# Process from line 687 onward
new_lines = lines[:686]  # Keep lines 1-686 as-is

i = 686
# Skip the def line and docstring lines until we hit the async for
while i < len(lines) and 'async for response in self.session.receive()' not in lines[i]:
    new_lines.append(lines[i])
    i += 1

# Now lines[i] is 'async for response in self.session.receive():' at 12 spaces
# Everything from i+1 onward needs 4 spaces removed
new_lines.append(lines[i])  # keep the async for line as-is
i += 1

while i < len(lines):
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    if line.strip():  # non-empty line
        new_indent = indent - 4
        if new_indent < 0:
            new_indent = 0
        new_lines.append(' ' * new_indent + line.lstrip())
    else:
        new_lines.append(line)
    i += 1

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(new_lines)
print(f'Done. File now has {len(new_lines)} lines.')