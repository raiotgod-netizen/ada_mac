"""
ada_remote.py — Connect to ADA from any PC via CMD.
Minimal dependencies: websockets (pip install websockets)

Usage:
    python ada_remote.py --host <ip> --port 8001 --token <password>
    
    Shortcuts:
    python ada_remote.py                    # Connect to local LAN IP
    python ada_remote.py --tailnet          # Connect via Tailscale (if available)
    python ada_remote.py --local            # Force local IP discovery
    python ada_remote.py --help              # Show help
"""

import asyncio
import sys
import os
import json
import argparse
import uuid
from pathlib import Path

# Default connection settings
DEFAULT_PORT = 8001


class AdaRemoteClient:
    def __init__(self, host: str, port: int, token: str):
        self.host = host
        self.port = port
        self.token = token
        self.url = f"ws://{host}:{port}"
        self.client_id = str(uuid.uuid4())[:8]
        self.authenticated = False
        self.running = True
        self.ws = None

    async def connect(self):
        """Establish WebSocket connection and authenticate."""
        try:
            import websockets
        except ImportError:
            print("ERROR: 'websockets' package required.")
            print("Install it with: pip install websockets")
            print("Or: python -m pip install websockets")
            sys.exit(1)

        try:
            print(f"[CLIENT] Connecting to {self.url}...")
            self.ws = await websockets.connect(self.url, ping_interval=None)
            print(f"[CLIENT] Connected. Authenticating...")

            # Auth
            await self.ws.send(json.dumps({
                "type": "auth",
                "token": self.token
            }))

            # Wait for auth response
            response = await asyncio.wait_for(self.ws.recv(), timeout=10)
            data = json.loads(response)

            if data.get("type") == "auth_ok":
                self.authenticated = True
                print(f"[CLIENT] ✅ {data.get('message')}")
                print("[CLIENT] Welcome! Type your messages and press Enter.")
                print("[CLIENT] Type /help for commands, /quit to exit.\n")
            else:
                print(f"[CLIENT] ❌ Auth failed: {data.get('message', 'Unknown error')}")
                await self.ws.close()
                sys.exit(1)

        except asyncio.TimeoutError:
            print("[CLIENT] ❌ Connection timeout. Is ADA running?")
            sys.exit(1)
        except Exception as e:
            print(f"[CLIENT] ❌ Connection error: {e}")
            sys.exit(1)

    async def listen_server(self):
        """Listen for messages from server in background."""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "chat":
                        sender = data.get("sender", "ADA")
                        text = data.get("text", "")
                        print(f"\r{sender}: {text}\n> ", end="")

                    elif msg_type == "error":
                        print(f"\r[ERROR]: {data.get('message', 'Unknown error')}\n> ", end="")

                    else:
                        print(f"\r[SERVER]: {data}\n> ", end="")

                except json.JSONDecodeError:
                    print(f"\r[SERVER] Raw: {message}\n> ", end="")

        except Exception as e:
            if self.running:
                print(f"\n[CLIENT] Disconnected: {e}")

    async def send_message(self, text: str):
        """Send a chat message to ADA."""
        if not self.authenticated:
            print("[CLIENT] Not authenticated.")
            return

        try:
            await self.ws.send(json.dumps({
                "type": "chat",
                "text": text
            }))
        except Exception as e:
            print(f"[CLIENT] Send error: {e}")
            self.running = False

    async def run(self):
        """Main client loop."""
        await self.connect()

        # Start server listener task
        listener = asyncio.create_task(self.listen_server())

        print("> ", end="", flush=True)
        while self.running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                user_input = user_input.strip()

                if not user_input:
                    print("> ", end="", flush=True)
                    continue

                # Built-in commands
                if user_input.lower() in ("/quit", "/exit", "/close"):
                    print("[CLIENT] Closing connection...")
                    self.running = False
                    break

                if user_input.lower() == "/help":
                    print("Commands:")
                    print("  /help  - Show this help")
                    print("  /quit  - Close connection and exit")
                    print("  /clear - Clear screen")
                    print("  Anything else - Send to ADA")
                    print("> ", end="", flush=True)
                    continue

                if user_input.lower() == "/clear":
                    os.system("cls" if os.name == "nt" else "clear")
                    print("> ", end="", flush=True)
                    continue

                # Send to ADA
                await self.send_message(user_input)
                print("> ", end="", flush=True)

            except (EOFError, KeyboardInterrupt):
                print("\n[CLIENT] Interrupted.")
                self.running = False
                break

        listener.cancel()
        try:
            await listener
        except asyncio.CancelledError:
            pass

        if self.ws:
            await self.ws.close()
        print("[CLIENT] Disconnected.")


def discover_local_ip() -> str:
    """Get local LAN IP of this machine."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def discover_ada_host() -> str | None:
    """Try to find ADA server on LAN via UDP broadcast."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(3)
        # Send broadcast to ADA's port (or a known port)
        sock.sendto(b"ADA_DISCOVER", ("<broadcast>", 8002))
        data, addr = sock.recvfrom(1024)
        sock.close()
        if data == b"ADA_HERE":
            return addr[0]
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Connect to ADA remotely via CMD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ada_remote.py --host 192.168.1.100 --port 8001 --token mypassword
  python ada_remote.py --local          # Auto-discover on LAN
  python ada_remote.py --host 100.92.x.x  --token mypassword   # Tailscale

Environment variables:
  ADA_REMOTE_HOST   Override default host
  ADA_REMOTE_TOKEN  Override default token (not recommended for security)
        """
    )
    parser.add_argument("--host", default=os.environ.get("ADA_REMOTE_HOST"), help="ADA server host/IP")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port (default: {DEFAULT_PORT})")
    parser.add_argument("--token", default=os.environ.get("ADA_REMOTE_TOKEN"), help="Access token/password")
    parser.add_argument("--local", action="store_true", help="Auto-discover ADA on LAN")
    args = parser.parse_args()

    # Token from env or file
    if not args.token:
        token_file = Path(__file__).parent / ".remote_token"
        if token_file.exists():
            args.token = token_file.read_text().strip()

    # Resolve host
    if args.local:
        print("[CLIENT] Discovering ADA on LAN...")
        host = asyncio.run(discover_ada_host())
        if host:
            args.host = host
            print(f"[CLIENT] Found ADA at {host}")
        else:
            print("[CLIENT] Could not find ADA on LAN. Use --host to specify manually.")
            sys.exit(1)

    if not args.host:
        host = discover_local_ip()
        print(f"[CLIENT] No host specified, using local IP: {host}")
        print("[CLIENT] If ADA is on another machine, use: --host <ip>")
        print()
        print("Usage: python ada_remote.py --host <ADA_IP> --port 8001 --token <PASSWORD>")
        sys.exit(1)

    if not args.token:
        print("[CLIENT] ERROR: Token required. Get it from the server terminal or .remote_token file.")
        print("Usage: python ada_remote.py --host <host> --port 8001 --token <PASSWORD>")
        sys.exit(1)

    # Run client
    client = AdaRemoteClient(args.host, args.port, args.token)
    asyncio.run(client.run())


if __name__ == "__main__":
    main()
