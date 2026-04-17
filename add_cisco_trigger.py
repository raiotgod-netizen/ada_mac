with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    content = f.read()

# 1. Add _cisco_mentioned flag in __init__
old_init = '''        self._last_input_transcription = ""
        self._last_output_transcription = ""

        self.audio_in_queue = None'''

new_init = '''        self._last_input_transcription = ""
        self._last_output_transcription = ""
        self._cisco_mentioned = False  # True when user mentions "cisco"

        self.audio_in_queue = None'''

content = content.replace(old_init, new_init)
print("Added _cisco_mentioned flag")

# 2. Add cisco detection in user transcription handler
# Find the line that sends transcription to frontend
old_transcribe = '''                                        # Send to frontend (Streaming)
                                        if self.on_transcription:
                                             self.on_transcription({"sender": "User", "text": delta})

                                        # Buffer for Logging'''

new_transcribe = '''                                        # Send to frontend (Streaming)
                                        if self.on_transcription:
                                             self.on_transcription({"sender": "User", "text": delta})

                                        # Check if user mentioned "cisco" (secondary trigger)
                                        if "cisco" in delta.lower():
                                            self._cisco_mentioned = True
                                            print(f"[ADA DEBUG] [CISCO] 'cisco' mentioned in user speech")

                                        # Buffer for Logging'''

content = content.replace(old_transcribe, new_transcribe)
print("Added cisco detection in transcription handler")

# 3. Trigger consult_agent when cisco was mentioned and transcription ends
# Find the flush_chat or end of turn area
# Look for 'flush_chat' near end of receive_audio
old_flush = '''                # Turn/Response Loop Finished
                self.flush_chat()

                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()'''

new_flush = '''                # Turn/Response Loop Finished
                # If user mentioned 'cisco', send consult to C.I.S.C.O.
                if self._cisco_mentioned:
                    self._cisco_mentioned = False
                    consult_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, '.openclaw', 'workspace', 'memory', 'ada_consulta.md')
                    os.makedirs(os.path.dirname(consult_path), exist_ok=True)
                    user_msg = self._last_input_transcription
                    with open(consult_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Consulta de ADA\\n\\n{user_msg}")
                    print(f"[ADA DEBUG] [CISCO] Consult sent to C.I.S.C.O.")

                self.flush_chat()

                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()'''

content = content.replace(old_flush, new_flush)
print("Added consult trigger at end of turn")

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(content)

print("Done")
