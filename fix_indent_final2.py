with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    lines = f.readlines()

# The receive_audio function body runs from line 691 (0-indexed 690, 'async for response')
# to line 1392 (0-indexed 1391, the last line before next 'def ' at 1393)
# We need to dedent every line by 4 spaces (12 -> 8 would be class-level, too small)

# Lines at indent 12 (the async for) should become indent 8? No wait.
# The function body starts at indent 12 (inside function def at indent 8)
# Inside that, content should be at 16. So removing 4 makes it 12 - which is wrong.
# 
# Actually looking at the original:
#   async def receive_audio(self):   indent 4 (class method)
#       "string"                      indent 8
#       try:                          indent 8
#           async for response in:    indent 12
#               if data :=            indent 16
#                   ...              indent 20
#
# After dedent-all-by-4:
#   async def receive_audio(self):   indent 4
#       "string"                      indent 4 (wrong - docstring should stay at 8)
# 
# So the approach needs to be smarter. Let me instead just rewrite the receive_audio block.

# Find the lines of receive_audio
start = None  # 0-indexed line of 'async def receive_audio'
end = None    # last line of receive_audio
for i, l in enumerate(lines):
    if 'async def receive_audio(self)' in l:
        start = i
    elif start is not None and l.strip() and not l[0].isspace() and i > start:
        end = i - 1
        break

print(f'receive_audio: {start+1} to {end+1}')

# Now extract the correctly indented version from a known good reference
# I'll write the correct receive_audio body

receive_audio_body = '''    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        try:
            async for response in self.session.receive():
                # 1. Handle Audio Data
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                    # NOTE: 'continue' removed here to allow processing transcription/tools in same packet

                # 2. Handle Transcription (User & Model)
                if response.server_content:
                    if response.server_content.input_transcription:
                        transcript = response.server_content.input_transcription.text
                        if transcript:
                            # Skip if this is an exact duplicate event
                            if transcript != self._last_input_transcription:
                                # Calculate delta (Gemini may send cumulative or chunk-based text)
                                delta = transcript
                                if transcript.startswith(self._last_input_transcription):
                                    delta = transcript[len(self._last_input_transcription):]
                                self._last_input_transcription = transcript
                                
                                # Only send if there's new text
                                if delta:
                                    # User is speaking — interrupt ADA if:
                                    # 1. ADA is currently playing audio, AND
                                    # 2. We haven't recently interrupted (suppression window prevents
                                    #    cutting ADA mid-sentence when user speaks in rapid bursts)
                                    now = time.monotonic()
                                    suppress_window = 2.0  # seconds
                                    if self._ada_speaking and (now - self._last_user_speech_interrupt) > suppress_window:
                                        self.clear_audio_queue()
                                        self._last_user_speech_interrupt = now

                                    # Send to frontend (Streaming)
                                    if self.on_transcription:
                                        self.on_transcription({"sender": "User", "text": delta})
                                    
                                    # Buffer for Logging
                                    if self.chat_buffer["sender"] != "User":
                                        # Flush previous if exists
                                        if self.chat_buffer["sender"] and self.chat_buffer["text"].strip():
                                            self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])
                                        # Start new
                                        self.chat_buffer = {"sender": "User", "text": delta}
                                    else:
                                        # Append
                                        self.chat_buffer["text"] += delta
                        

                if response.server_content and response.server_content.output_transcription:
                    transcript = response.server_content.output_transcription.text
                    if transcript:
                        # Skip if this is an exact duplicate event
                        if transcript != self._last_output_transcription:
                            # Calculate delta (Gemini may send cumulative or chunk-based text)
                            delta = transcript
                            if transcript.startswith(self._last_output_transcription):
                                delta = transcript[len(self._last_output_transcription):]
                            self._last_output_transcription = transcript
                            
                            # Only send if there's new text
                            if delta:
                                # Send to frontend (Streaming)
                                if self.on_transcription:
                                    self.on_transcription({"sender": "ADA", "text": delta})
                                
                                # Buffer for Logging
                                if self.chat_buffer["sender"] != "ADA":
                                    # Flush previous
                                    if self.chat_buffer["sender"] and self.chat_buffer["text"].strip():
                                        self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])
                                    # Start new
                                    self.chat_buffer = {"sender": "ADA", "text": delta}
                                else:
                                    # Append
                                    self.chat_buffer["text"] += delta

                # 3. Handle Tool Calls
                if response.tool_call:
                    print("The tool was called")
                    function_responses = []
                    for fc in response.tool_call.function_calls:
                        if fc.name in ["generate_cad", "run_web_agent", "write_file", "read_directory", "read_file", "create_project", "switch_project", "list_projects", "list_smart_devices", "control_light", "discover_printers", "print_stl", "get_print_status", "iterate_cad", "spotify_control", "screen_live", "read_system_clipboard", "set_volume", "send_email", "read_document", "shutdown_pc", "read_inbox", "search_inbox", "get_system_info", "remind_me", "screen_action"]:
                            prompt = fc.args.get("prompt", "")

                            # All tools execute immediately on voice command - no manual confirmation required
                            pass

                            if fc.name == "generate_cad":
                                print(f"\\n[ADA DEBUG] --------------------------------------------------")
                                print(f"[ADA DEBUG] [TOOL] Tool Call Detected: 'generate_cad'")
                                print(f"[ADA DEBUG] [IN] Arguments: prompt='{prompt}'")
                                
                                asyncio.create_task(self.handle_cad_request(prompt))
                                function_response = types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={"result": "Generating CAD model..."}
                                )
                                function_responses.append(function_response)
                            
                            elif fc.name == "run_web_agent":
                                print(f"[ADA DEBUG] [TOOL] Tool Call: 'run_web_agent' with prompt='{prompt}'")
                                asyncio.create_task(self.handle_web_agent_request(prompt))
                                
                                result_text = "Web Navigation started. Do not reply to this message."
                                function_response = types.FunctionResponse(
                                    id=fc.id,
                                    name=fc.name,
                                    response={"result": result_text}
                                )
                                function_responses.append(function_response)

                        elif fc.name in ["screen_action"]:
                            prompt = fc.args.get("prompt", "")
                            asyncio.create_task(self.handle_screen_action(prompt))
                            function_response = types.FunctionResponse(
                                id=fc.id,
                                name=fc.name,
                                response={"result": "Screen action started"}
                            )
                            function_responses.append(function_response)

                        else:
                            result_text = f"Tool '{fc.name}' executed successfully."
                            function_response = types.FunctionResponse(
                                id=fc.id,
                                name=fc.name,
                                response={"result": result_text}
                            )
                            function_responses.append(function_response)
                    
                    if function_responses:
                        await asyncio.sleep(0)
                        try:
                            await self.session.send(input={"function_responses": function_responses})
                        except Exception as e:
                            print(f"[ADA DEBUG] Error sending function responses: {e}")

        except Exception as e:
            print(f"[ADA ERROR] receive_audio crashed: {e}")
            import traceback
            traceback.print_exc()
'''

# Rebuild file: lines 0 to start-1, then the new body, then lines from end+1 onward
new_lines = lines[:start] + [receive_audio_body + '\n'] + lines[end+1:]

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.writelines(new_lines)
print(f'Done. File now has {len(new_lines)} lines.')