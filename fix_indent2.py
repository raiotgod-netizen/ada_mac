with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# Fix line 700 (0-indexed 699): '                            if transcript:' -> 24 spaces
lines[699] = '                        if transcript:\n'

# Fix line 729 (0-indexed 728): un-indent log_chat to 44 spaces
lines[728] = '                                            self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])\n'

# Fix line 731 (0-indexed 730): un-indent chat_buffer to 44 spaces
lines[730] = '                                            self.chat_buffer = {"sender": "User", "text": delta}\n'

# Fix line 733 (0-indexed 732): un-indent += to 40 spaces
lines[732] = '                                        self.chat_buffer["text"] += delta\n'

# Fix line 738 (0-indexed 737): '                            if transcript:' -> 24 spaces
lines[737] = '                        if transcript:\n'

# Fix line 744 (0-indexed 743): fix delta line
lines[743] = '                                    delta = transcript[len(self._last_output_transcription):]\n'

# Fix line 745 (0-indexed 744): dedent _last_output_transcription to 32 spaces
lines[744] = '                                self._last_output_transcription = transcript\n'

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(lines)
print('Done')