with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    content = f.read()

replacements = [
    ('                        if response.server_content.output_transcription:', '                    if response.server_content.output_transcription:'),
    ('                            transcript = response.server_content.output_transcription.text', '                        transcript = response.server_content.output_transcription.text'),
    ('                                # Skip if this is an exact duplicate event', '                            # Skip if this is an exact duplicate event'),
    ('                                    if transcript != self._last_output_transcription:', '                                if transcript != self._last_output_transcription:'),
    ('                                        delta = transcript\n                                    if transcript.startswith(self._last_output_transcription):', '                                    delta = transcript\n                                if transcript.startswith(self._last_output_transcription):'),
    ('                                        delta = transcript[len(self._last_output_transcription):]', '                                    delta = transcript[len(self._last_output_transcription):]'),
    ('                                    self._last_output_transcription = transcript', '                                self._last_output_transcription = transcript'),
    ('                                    # Only send if there', '                                # Only send if there'),
    ('                                             self.on_transcription({"sender": "ADA"', '                                             self.on_transcription({"sender": "ADA"'),
    ('                                                self.project_manager.log_chat', '                                            self.project_manager.log_chat'),
    ('                                            # Start new', '                                        # Start new'),
    ('                                            # Append', '                                        # Append'),
    ('                                            self.chat_buffer["text"] += delta', '                                        self.chat_buffer["text"] += delta'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        print(f'Fixed: {repr(old[:60])}')
    else:
        print(f'NOT FOUND: {repr(old[:60])}')

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(content)
print('Done')