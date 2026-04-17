import re
path = r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\ada.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: send_realtime break -> continue
old1 = '                break\n\n    async def listen_audio(self):'
new1 = '                continue\n\n    async def listen_audio(self):'
if 'break\n\n    async def listen_audio(self):' in content:
    content = content.replace('break\n\n    async def listen_audio(self):', 'continue\n\n    async def listen_audio(self):')
    print('Fix 1 applied: send_realtime break->continue')
else:
    # find the specific block
    idx = content.find('session.send() error: {e}')
    if idx >= 0:
        print('Found session.send() error line at idx', idx)
        print(repr(content[idx-100:idx+200]))
    else:
        print('Fix 1 NOT FOUND - session.send() error line not found')

# Fix 2: listen_audio queue put -> put_nowait with QueueFull handling
old2 = '                elif self.out_queue:\n                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})'
new2 = '                elif self.out_queue:\n                    try:\n                        self.out_queue.put_nowait({"data": data, "mime_type": "audio/pcm"})\n                    except asyncio.QueueFull:\n                        # Queue full -- skip to keep VAD loop responsive\n                        pass'
if old2 in content:
    content = content.replace(old2, new2)
    print('Fix 2 applied: out_queue put_nowait')
else:
    print('Fix 2 NOT FOUND')
    idx = content.find('await self.out_queue.put')
    if idx >= 0:
        print('Found at idx', idx)
        print(repr(content[idx-50:idx+150]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
