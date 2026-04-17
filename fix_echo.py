"""
Fix echo suppression in ADA.
The existing code has _ada_speaking and _echo_cooldown flags,
but they're never set - they stay False forever.

This script:
1. Adds amplitude detection to play_audio (detects when ADA is "speaking")
2. Adds a silence timer that sets _ada_speaking=False + starts cooldown after 0.5s
3. Adds cooldown timer that sets _echo_cooldown=False after _echo_cooldown_seconds
4. Also fixes a duplicate line issue in __init__
"""

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# ==== 1. Fix duplicate audio_in_queue/out_queue/paused lines in __init__ ====
# Remove duplicate lines (lines 244-246 in current file have duplicates of 234-236)
old_duplicates = '''        self.audio_in_queue = None
        self.out_queue = None
        self.paused = False

        self.session = None'''

new_no_dupe = '''        self.audio_in_queue = None
        self.out_queue = None
        self.paused = False
        self.session = None'''

content = content.replace(old_duplicates, new_no_dupe)
print("Fixed duplicate __init__ lines")

# ==== 2. Add silence detection constants to __init__ ====
# After self._echo_cooldown_seconds
old_cooldown = '''        self._echo_cooldown_seconds = 1.5  # seconds to wait after ADA stops speaking
        # User speech suppression'''

new_cooldown = '''        self._echo_cooldown_seconds = 1.5  # seconds to wait after ADA stops speaking
        # Silence detection for echo suppression
        self._last_audio_time = 0  # timestamp of last non-silence audio
        self._silence_check_task = None
        self._audio_rms_threshold = 100  # RMS threshold to detect non-silence'''

content = content.replace(old_cooldown, new_cooldown)
print("Added silence detection state to __init__")

# ==== 3. Replace play_audio to detect speaking ====
old_play_audio = '''    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            output_device_index=self.output_device_index,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            if self.on_audio_data:
                self.on_audio_data(bytestream)
            try:
                await asyncio.to_thread(stream.write, bytestream)
            except Exception as e:
                print(f"[ADA DEBUG] [PLAY] Audio write error: {e}")

    async def get_screen(self):'''

new_play_audio = '''    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            output_device_index=self.output_device_index,
        )
        self._silence_check_task = asyncio.create_task(self._silence_checker())
        while True:
            bytestream = await self.audio_in_queue.get()
            if self.on_audio_data:
                self.on_audio_data(bytestream)

            # Detect if this chunk is non-silence (ADA is speaking)
            rms = self._calc_rms(bytestream)
            now = time.monotonic()
            if rms > self._audio_rms_threshold:
                self._last_audio_time = now
                if not self._ada_speaking:
                    self._ada_speaking = True
                    self._echo_cooldown = False
                    print(f"[ADA DEBUG] [ECHO] ADA started speaking (RMS: {rms})")

            try:
                await asyncio.to_thread(stream.write, bytestream)
            except Exception as e:
                print(f"[ADA DEBUG] [PLAY] Audio write error: {e}")

    def _calc_rms(self, bytestream):
        """Calculate RMS amplitude of PCM audio chunk."""
        if len(bytestream) < 2:
            return 0
        count = len(bytestream) // 2
        try:
            shorts = struct.unpack(f"<{count}h", bytestream)
            sum_squares = sum(s**2 for s in shorts)
            return int(math.sqrt(sum_squares / count))
        except:
            return 0

    async def _silence_checker(self):
        """Background task: marks ADA as not speaking after silence period."""
        while True:
            await asyncio.sleep(0.1)
            now = time.monotonic()
            silence_threshold = 0.5  # seconds of silence before marking "not speaking"
            if self._ada_speaking and (now - self._last_audio_time) > silence_threshold:
                self._ada_speaking = False
                self._echo_cooldown = True
                print(f"[ADA DEBUG] [ECHO] ADA stopped speaking, cooldown active")
            elif self._echo_cooldown and (now - self._last_audio_time) > (self._echo_cooldown_seconds + silence_threshold):
                self._echo_cooldown = False
                print(f"[ADA DEBUG] [ECHO] Cooldown expired")

    async def get_screen(self):'''

content = content.replace(old_play_audio, new_play_audio)
print("Replaced play_audio with speaking detection")

# ==== 4. Add _calc_rms and _silence_checker to class (after play_audio) ====
# Actually done in step 3 already

with open(r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py', 'w') as f:
    f.write(content)

print("\nCompile check:")
