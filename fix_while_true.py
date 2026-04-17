import re

with open(r"C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py", "r", encoding="latin-1") as f:
    content = f.read()

# Fix: add while True wrapper and change session.receive() pattern
old = '''    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        try:
            async for response in self.session.receive():'''

new = '''    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        try:
            while True:
                turn = self.session.receive()
                async for response in turn:'''

content = content.replace(old, new, 1)

with open(r"C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py", "w", encoding="latin-1") as f:
    f.write(content)

print("Done")