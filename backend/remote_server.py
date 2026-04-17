"""remote_server.py — WebSocket + HTTP server for remote ADA access via CMD."""

import asyncio
import json
import sys
import os
import secrets
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import websockets

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8001

TOKEN_FILE = Path(__file__).parent / ".remote_token"

def get_remote_password() -> str:
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    token = secrets.token_urlsafe(16)
    TOKEN_FILE.write_text(token)
    print(f"[REMOTE] New access token: {token}")
    return token

def verify_password(token: str) -> bool:
    return secrets.compare_digest(token, get_remote_password())

async def groq_chat(text: str) -> str:
    try:
        from groq import AsyncGroq
        from pathlib import Path
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "GROQ_API_KEY no configurada."
        client = AsyncGroq(api_key=api_key)
        p = Path(__file__).parent / "jarvis_personality.txt"
        personality = p.read_text(encoding="utf-8").strip() if p.exists() else "You are ADA."
        resp = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": personality}, {"role": "user", "content": text}],
            temperature=0.7, max_tokens=1024,
        )
        return resp.choices[0].message.content.strip() or "No response."
    except Exception as e:
        return f"Error: {str(e)[:200]}"

class RemoteClient:
    def __init__(self, websocket, client_id: str):
        self.ws = websocket
        self.client_id = client_id
        self.authenticated = False

    async def send(self, data: dict):
        try:
            await self.ws.send_json(data)
        except Exception as e:
            print(f"[REMOTE] Send error: {e}")

    async def handle_message(self, data: dict):
        msg_type = data.get("type")
        if msg_type == "auth":
            if verify_password(data.get("token", "")):
                self.authenticated = True
                await self.send({"type": "auth_ok", "message": "Autenticado."})
                print(f"[REMOTE] Client {self.client_id} authenticated")
            else:
                await self.send({"type": "auth_fail", "message": "Token incorrecto."})
                await self.ws.close()
            return
        if not self.authenticated:
            await self.send({"type": "error", "message": "No autenticado."})
            return
        if msg_type == "chat":
            text = data.get("text", "")
            if text:
                response = await groq_chat(text)
                await self.send({"type": "chat", "sender": "ADA", "text": response})

async def websocket_handler(websocket, path):
    import uuid
    client_id = str(uuid.uuid4())[:8]
    client = RemoteClient(websocket, client_id)
    print(f"[REMOTE] New WS connection: {client_id}")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                await client.handle_message(data)
            except json.JSONDecodeError:
                await client.send({"type": "error", "message": "Invalid JSON."})
    except Exception as e:
        print(f"[REMOTE] WS error: {e}")
    finally:
        print(f"[REMOTE] Client disconnected: {client_id}")

async def handle_http(reader, writer):
    request_line = await reader.readline()
    if not request_line:
        writer.close()
        return

    parts = request_line.decode().split()
    if len(parts) < 3:
        writer.close()
        return

    method, path, _ = parts[0], parts[1], parts[2]

    if path == "/health":
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")
        await writer.drain()
        writer.close()
        return

    content_length = 0
    while True:
        line = await reader.readline()
        if line in (b"\r\n", b"\n", b""):
            break
        if line.lower().startswith(b"content-length:"):
            content_length = int(line.decode().split(":")[1].strip())

    body = b""
    if content_length > 0:
        body = await reader.read(content_length)

    if path == "/auth":
        try:
            data = json.loads(body.decode())
            token = data.get("token", "")
            if verify_password(token):
                resp = json.dumps({"type": "auth_ok", "message": "Authenticated"})
                resp_bytes = resp.encode()
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
            else:
                resp = json.dumps({"type": "auth_fail", "message": "Invalid token"})
                resp_bytes = resp.encode()
                writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
        except Exception as e:
            resp = json.dumps({"error": str(e)})
            resp_bytes = resp.encode()
            writer.write(b"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
        await writer.drain()
        writer.close()
        return

    if path == "/chat":
        try:
            data = json.loads(body.decode())
            token = data.get("token", "")
            text = data.get("text", "")
            if verify_password(token):
                response = await groq_chat(text)
                resp = json.dumps({"type": "chat", "sender": "ADA", "text": response})
                resp_bytes = resp.encode()
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
            else:
                resp = json.dumps({"error": "Invalid token"})
                resp_bytes = resp.encode()
                writer.write(b"HTTP/1.1 401 Unauthorized\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
        except Exception as e:
            resp = json.dumps({"error": str(e)})
            resp_bytes = resp.encode()
            writer.write(b"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nContent-Length: " + str(len(resp_bytes)).encode() + b"\r\n\r\n" + resp_bytes)
        await writer.drain()
        writer.close()
        return

    resp = b"Not Found"
    writer.write(b"HTTP/1.1 404 Not Found\r\nContent-Length: 9\r\n\r\nNot Found")
    await writer.drain()
    writer.close()

async def main():
    password = get_remote_password()
    print(f"[REMOTE] Token: {password}")
    print(f"[REMOTE] HTTP: /auth, /chat, /health | WS: port {LISTEN_PORT}")

    http_server = await asyncio.start_server(handle_http, LISTEN_HOST, LISTEN_PORT)
    ws_server = await websockets.serve(websocket_handler, LISTEN_HOST, LISTEN_PORT + 1)

    print(f"[REMOTE] HTTP listening on port {LISTEN_PORT}")
    print(f"[REMOTE] WebSocket listening on port {LISTEN_PORT + 1}")

    async with http_server, ws_server:
        await asyncio.Future()

if __name__ == "__main__":
    print("[REMOTE] Starting...")
    asyncio.run(main())