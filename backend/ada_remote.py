"""ada_remote.py — Client to connect to ADA remote server via cloudflared tunnel."""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

async def main():
    host = "tournament-visit-pioneer-shadows.trycloudflare.com"
    port = 443
    token = "4587"

    uri = f"wss://{host}:{port}"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri, ping_interval=10, ping_timeout=20) as ws:
            print("Connected! Waiting for server... (2s)")
            await asyncio.sleep(2)

            print("Authenticating...")
            await ws.send(json.dumps({"type": "auth", "token": token}))

            resp = await asyncio.wait_for(ws.recv(), timeout=15)
            data = json.loads(resp)
            print(f"Server: {data.get('message', data)}")

            if data.get("type") != "auth_ok":
                print("Authentication failed.")
                return

            print("\n=== Connected to ADA ===")
            print("Type your messages. 'quit' to exit.\n")

            async def receiver():
                try:
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get("type") == "chat":
                            print(f"\nADA: {data.get('text', '')}\n> ", end="", flush=True)
                        elif data.get("type") == "error":
                            print(f"\nError: {data.get('message', '')}\n> ", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed.")

            recv_task = asyncio.create_task(receiver())

            while True:
                try:
                    text = input("> ").strip()
                    if text.lower() == "quit":
                        break
                    if text:
                        await ws.send(json.dumps({"type": "chat", "text": text}))
                except (EOFError, KeyboardInterrupt):
                    break

            recv_task.cancel()

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())