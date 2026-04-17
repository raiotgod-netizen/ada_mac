"""
Remote Monitor Server for ADA v1.
Streams desktop to a web page accessible locally or via ngrok tunnel.
"""
import asyncio
import base64
import io
import threading
import time
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import json
import mss
import numpy as np

try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except Exception:
    NGROK_AVAILABLE = False
    ngrok = None


class RemoteMonitorServer:
    """
    Serves live desktop stream via HTTP (MJPEG-style) and exposes it via ngrok.
    """

    def __init__(self, port=5000, quality=75, fps=10, monitor_index=1):
        self.port = port
        self.quality = quality
        self.fps = fps
        self.monitor_index = monitor_index

        self._running = False
        self._stream_task = None
        self._server = None
        self._ngrok_tunnel = None
        self._public_url = None

        # Latest frame for streaming
        self._latest_frame_b64 = None
        self._frame_lock = threading.Lock()

        # Motion detection
        self._last_frame_hash = None
        self._motion_threshold = 500  # Number of different pixels to trigger "motion"
        self._motion_only = False  # If True, only capture on motion

        # Connected clients
        self._client_count = 0
        self._client_lock = threading.Lock()

        # HTTP server
        self._server_ready = threading.Event()

    # ── STREAMING ──────────────────────────────────────────────

    def _capture_frame(self):
        """Capture a single screen frame as JPEG base64."""
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[self.monitor_index]
                img = sct.grab(monitor)
                from PIL import Image
                pil_img = Image.frombytes("RGB", img.size, img.rgb)
                # Resize for bandwidth
                pil_img.thumbnail([1280, 720])
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=self.quality)
                buf.seek(0)
                return base64.b64encode(buf.read()).decode()
        except Exception as e:
            print(f"[REMOTE MONITOR] Capture error: {e}")
            return None

    def _has_motion(self, frame_b64):
        """Simple motion detection via perceptual hash."""
        try:
            data = base64.b64decode(frame_b64)
            buf = io.BytesIO(data)
            from PIL import Image
            img = Image.open(buf).convert("L").resize((64, 36))
            pixels = np.array(img).flatten()
            # Simple diff with previous
            if self._last_frame_hash is None:
                self._last_frame_hash = pixels.tobytes()
                return True
            diff = np.sum(pixels.astype(np.int16) - np.frombuffer(self._last_frame_hash, dtype=np.uint8).astype(np.int16))
            self._last_frame_hash = pixels.tobytes()
            return abs(diff) > self._motion_threshold * 255
        except Exception:
            return True

    async def _stream_loop(self):
        """Background loop that captures and updates latest frame."""
        interval = 1.0 / self.fps
        while self._running:
            try:
                frame = await asyncio.to_thread(self._capture_frame)
                if frame:
                    if self._motion_only:
                        if self._has_motion(frame):
                            with self._frame_lock:
                                self._latest_frame_b64 = frame
                    else:
                        with self._frame_lock:
                            self._latest_frame_b64 = frame
            except Exception as e:
                print(f"[REMOTE MONITOR] Stream loop error: {e}")
            await asyncio.sleep(interval)

    def get_latest_frame(self):
        with self._frame_lock:
            return self._latest_frame_b64

    # ── HTTP SERVER ─────────────────────────────────────────────

    def _make_handler(self):
        """Create a MJPEG-style handler class bound to this server."""
        server = self

        class StreamHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/stream":
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(self._html_page().encode())

                elif self.path == "/mjpeg":
                    self.send_response(200)
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    last_send = 0
                    while server._running:
                        frame = server.get_latest_frame()
                        if frame:
                            try:
                                self.wfile.write(b"--frame\r\n")
                                self.send_header("Content-Type", "image/jpeg")
                                self.send_header("Content-Length", str(len(base64.b64decode(frame))))
                                self.end_headers()
                                self.wfile.write(base64.b64decode(frame))
                                self.wfile.write(b"\r\n")
                            except Exception:
                                break
                        time.sleep(1.0 / server.fps)

                elif self.path == "/status":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    status = {
                        "running": server._running,
                        "fps": server.fps,
                        "quality": server.quality,
                        "motion_only": server._motion_only,
                        "public_url": server._public_url,
                        "ngrok": NGROK_AVAILABLE
                    }
                    self.wfile.write(json.dumps(status).encode())

                elif self.path == "/favicon.ico":
                    self.send_response(204)
                    self.end_headers()

                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, fmt, *args):
                pass  # Silence access logs

        return StreamHandler

    @staticmethod
    def _html_page():
        return """<!DOCTYPE html>
<html><head><title>ADA Remote Monitor</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;font-family:monospace}
#video{width:90vw;max-width:1280px;border:2px solid #00ffc8;border-radius:8px;background:#000}
#info{color:#00ffc8;padding:12px;font-size:13px;text-align:center;letter-spacing:1px}
#status{color:#666;font-size:11px;margin-top:4px}
button{background:#00ffc820;border:1px solid #00ffc8;color:#00ffc8;padding:8px 20px;
  margin:6px;border-radius:6px;cursor:pointer;font-family:monospace;font-size:12px}
button:hover{background:#00ffc840}
#controls{padding:10px;display:flex;gap:10px;flex-wrap:wrap;justify-content:center}
</style></head>
<body>
<div id="info">ADA REMOTE MONITOR<span id="status"></span></div>
<div id="controls">
  <button onclick="toggleStream()">PAUSE</button>
  <button onclick="toggleMotion()">MOTION: OFF</button>
  <select id="qualitySelect" onchange="setQuality(this.value)" style="background:#00ffc820;border:1px solid #00ffc8;color:#00ffc8;padding:8px;border-radius:6px;font-family:monospace">
    <option value="50">Low Q</option>
    <option value="75" selected>Medium Q</option>
    <option value="90">High Q</option>
  </select>
</div>
<img id="video" src="/mjpeg" />
<script>
const img=document.getElementById('video');
const status=document.getElementById('status');
let paused=false, motion=false;

function toggleStream(){
  paused=!paused;
  img.src=paused?'/mjpeg?pause=1':'/mjpeg';
  document.querySelector('button').textContent=paused?'RESUME':'PAUSE';
}
function toggleMotion(){
  motion=!motion;
  document.getElementById('qualitySelect').style.display=motion?'none':'inline-block';
  fetch('/status').then(r=>r.json()).then(s=>{
    s.motion_only=motion;
    status.textContent=' | Motion: '+(motion?'ON':'OFF')+' | '+s.fps+' FPS | URL: '+window.location.href;
  });
}
setInterval(()=>fetch('/status').then(r=>r.json()).then(s=>{
  if(!paused) status.textContent=' | FPS: '+s.fps+' | Quality: '+s.quality+' | '+s.public_url;
}),2000);
</script>
</body></html>"""

    # ── CONTROL API ─────────────────────────────────────────────

    def start(self, expose_ngrok=True):
        """Start the monitor server."""
        if self._running:
            return {"ok": True, "result": "Already running", "url": self._public_url}

        self._running = True

        # Start capture loop
        self._stream_task = asyncio.create_task(self._stream_loop())

        # Start HTTP server
        handler = self._make_handler()
        self._server = ThreadingHTTPServer(("0.0.0.0", self.port), handler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()

        local_url = f"http://localhost:{self.port}"

        # Expose via ngrok
        public_url = None
        if expose_ngrok and NGROK_AVAILABLE:
            try:
                # Terminate any existing tunnels
                ngrok.kill()
                self._ngrok_tunnel = ngrok.open(f"{self.port}", "http")
                public_url = self._ngrok_tunnel.public_url
                self._public_url = public_url
                print(f"[REMOTE MONITOR] Ngrok tunnel: {public_url}")
            except Exception as e:
                print(f"[REMOTE MONITOR] Ngrok error: {e}")
                public_url = f"{local_url} (ngrok failed: {e})"
        else:
            public_url = local_url
            self._public_url = local_url

        return {
            "ok": True,
            "result": f"Remote monitor running at {public_url}",
            "local_url": local_url,
            "public_url": public_url,
            "ngrok_available": NGROK_AVAILABLE
        }

    def stop(self):
        """Stop the monitor server."""
        if not self._running:
            return {"ok": True, "result": "Not running"}

        self._running = False

        if self._ngrok_tunnel:
            try:
                ngrok.kill()
            except Exception:
                pass

        if self._server:
            self._server.shutdown()

        if self._stream_task:
            self._stream_task.cancel()

        self._public_url = None
        return {"ok": True, "result": "Remote monitor stopped"}

    def set_motion_detection(self, enabled, threshold=500):
        """Enable/disable motion-triggered capture."""
        self._motion_only = enabled
        self._motion_threshold = threshold
        self._last_frame_hash = None  # Reset hash
        return {"ok": True, "result": f"Motion detection: {enabled}"}

    def set_quality(self, quality):
        """Change JPEG quality (10-100)."""
        self.quality = max(10, min(100, quality))
        return {"ok": True, "result": f"Quality set to {self.quality}"}

    def set_fps(self, fps):
        """Change capture FPS."""
        self.fps = max(1, min(30, fps))
        return {"ok": True, "result": f"FPS set to {self.fps}"}

    def get_status(self):
        """Get server status."""
        return {
            "running": self._running,
            "local_url": f"http://localhost:{self.port}",
            "public_url": self._public_url,
            "fps": self.fps,
            "quality": self.quality,
            "motion_only": self._motion_only,
            "ngrok_available": NGROK_AVAILABLE
        }


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


# Singleton instance
_monitor_server = None


def get_monitor():
    global _monitor_server
    if _monitor_server is None:
        _monitor_server = RemoteMonitorServer()
    return _monitor_server


if __name__ == "__main__":
    # Test: start server and print URL
    monitor = RemoteMonitorServer(port=5000)
    result = monitor.start(expose_ngrok=True)
    print(result)
    print("Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
