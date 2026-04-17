with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Remove lines at index 729 and 731 (0-indexed duplicates of 728 and 730)
new_lines = [l for i, l in enumerate(lines) if i not in [729, 731]]

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(new_lines)
print('Done')