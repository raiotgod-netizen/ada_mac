"""
Quick script to get your Telegram chat ID.
1. Make sure you've sent at least one message to @Archerbot666
2. Run this script: python get_telegram_id.py
3. Your chat ID will be printed
"""
import os
import httpx
from pathlib import Path

dotenv = Path(__file__).parent.parent / ".env"
if dotenv.exists():
    with open(dotenv) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k] = v

token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print(f"Bot token: ...{token[-4:]}")
print("Fetching updates...\n")

try:
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"https://api.telegram.org/bot{token}/getUpdates")
        data = resp.json()

        if not data.get("ok"):
            print(f"API Error: {data}")
            exit(1)

        updates = data.get("result", [])
        if not updates:
            print("No messages found. Make sure you've sent a message to the bot first!")
            exit(0)

        seen = set()
        for update in updates:
            msg = update.get("message", {})
            chat = msg.get("chat", {})
            chat_id = chat.get("id")
            username = chat.get("username", "no username")
            first_name = chat.get("first_name", "no name")

            if chat_id and chat_id not in seen:
                seen.add(chat_id)
                print(f"Chat ID: {chat_id}")
                print(f"  Name: {first_name}")
                print(f"  Username: @{username}")
                print()

        if len(seen) == 1:
            cid = list(seen)[0]
            print(f"\nYour TELEGRAM_ADMIN_CHAT_ID: {cid}")
            print(f"\nAdd this to .env:")
            print(f"TELEGRAM_ADMIN_CHAT_ID={cid}")

except Exception as e:
    print(f"Error: {e}")
