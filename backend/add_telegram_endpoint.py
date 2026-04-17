path = r'C:\Users\raiot\OneDrive\Escritorio\ADA\ada_v2\backend\server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add endpoint after /status
old = '@app.get("/status")\nasync def status():\n    return {"status": "running", "service": "A.D.A Backend"}'

new = '''@app.get("/status")
async def status():
    return {"status": "running", "service": "A.D.A Backend"}

# --- Telegram command executor endpoint ---
@app.post("/telegram/exec")
async def telegram_exec(request: dict):
    """
    Receives commands from Telegram bot and executes them.
    Called by telegram_session via HTTP (avoids importing socketio in telegram session).
    """
    try:
        command = request.get("command", "")
        if not command:
            return {"ok": False, "error": "No command provided"}

        from telegram_executor import get_executor
        executor = get_executor()
        result = await executor.execute(command)
        if result is None:
            return {"ok": False, "handled": False, "result": "Command not recognized"}
        return {"ok": True, "handled": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}'''

if old in content:
    content = content.replace(old, new)
    print('Endpoint added successfully')
else:
    print('Pattern not found!')
    # Try to find the status endpoint
    idx = content.find('@app.get("/status")')
    if idx >= 0:
        print('Found @app.get("/status") at idx', idx)
        print(repr(content[idx:idx+200]))

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
