with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Remove duplicate lines (730 and 732 are exact duplicates of 729 and 731)
# Lines are 0-indexed, so 729=line730, 731=line732
duplicate_indices = sorted(set([729, 731]))  # Remove second occurrences
# Actually remove by filtering
new_lines = []
seen_counts = {}
for i, line in enumerate(lines):
    # Check if this is a duplicate of line 728 (log_chat) or line 730 (chat_buffer)
    if i in [730, 732]:  # 0-indexed duplicates
        continue
    new_lines.append(line)

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(new_lines)
print('Removed duplicates')