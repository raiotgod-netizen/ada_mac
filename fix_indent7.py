with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Fix line 728 (index 727): `if ... .strip():` at 44 spaces is OK (parent is 40)
# Fix line 729 (index 728): log_chat needs 48 spaces (was 44)
lines[728] = '                                                self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])\n'

# Fix line 730 (index 729): chat_buffer needs 48 spaces (was 44)
lines[729] = '                                                self.chat_buffer = {"sender": "User", "text": delta}\n'

# Fix line 734 (index 733): '                            if transcript:' -> 24 spaces
lines[733] = '                        if transcript:\n'

# Remove the duplicate `if transcript:` at line 735 (index 734)
# Also fix the rest of output_transcription block
new_lines = [l for i, l in enumerate(lines) if i != 734]  # remove duplicate

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(new_lines)
print('Done')