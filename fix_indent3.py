with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Fix 700: '                            if transcript:' -> 24 spaces (index 699)
lines[699] = '                        if transcript:\n'

# Fix 730: log_chat -> 44 spaces (index 729)
lines[729] = '                                            self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])\n'

# Fix 732: chat_buffer assignment -> 44 spaces (index 731)
lines[731] = '                                            self.chat_buffer = {"sender": "User", "text": delta}\n'

# Fix 734: += delta -> 40 spaces (index 733)
lines[733] = '                                        self.chat_buffer["text"] += delta\n'

# Fix 739: '                            if transcript:' -> 24 spaces (index 738)
lines[738] = '                        if transcript:\n'

# Fix 745: delta = transcript[len...] -> 36 spaces (index 744)
lines[744] = '                                    delta = transcript[len(self._last_output_transcription):]\n'

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(lines)
print('Done')