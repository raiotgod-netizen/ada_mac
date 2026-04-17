with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Fix line 700: '                        if transcript:' -> 28 spaces
lines[699] = '                            if transcript:\n'

# Fix line 701: '                            # Skip if this...' -> 32 spaces
lines[700] = '                                # Skip if this is an exact duplicate event\n'

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(lines)
print('Done')