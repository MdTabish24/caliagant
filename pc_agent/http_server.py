"""
HTTP Server - Phone se call state receive karta hai
Phone app HTTP se connect hoke state bhejti hai
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import HTTP_HOST, HTTP_PORT, logger

class CallState:
    """Shared call state between server and main agent"""
    IDLE = 0
    RINGING = 1
    ACTIVE = 2
    
    def __init__(self):
        self.state = self.IDLE
        self.phone_number = ""
        self.direction = "outgoing"  # "outgoing" or "incoming"
        self.lock = threading.Lock()
        self.callbacks = []
    
    def set_state(self, state, number="", direction="outgoing"):
        with self.lock:
            old_state = self.state
            self.state = state
            self.phone_number = number
            self.direction = direction
            
            if old_state != state:
                state_names = {0: "IDLE", 1: "RINGING", 2: "ACTIVE"}
                dir_emoji = "📤" if direction == "outgoing" else "📥"
                logger.info(f"📞 Call: {state_names.get(state, state)} | {dir_emoji} {direction.upper()} | {number}")
                
                # Notify callbacks
                for callback in self.callbacks:
                    try:
                        callback(state, number, direction)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
    
    def get_state(self):
        with self.lock:
            return self.state, self.phone_number, self.direction
    
    def is_outgoing(self):
        with self.lock:
            return self.direction == "outgoing"
    
    def on_state_change(self, callback):
        """Register callback for state changes"""
        self.callbacks.append(callback)


# Global call state
call_state = CallState()


class CallHandler(BaseHTTPRequestHandler):
    """HTTP handler for phone requests"""
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/status":
            state, number = call_state.get_state()
            self.send_json({"state": state, "number": number})
        elif self.path == "/ping":
            self.send_json({"status": "ok"})
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests from phone"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        
        number = data.get("number", "")
        direction = data.get("direction", "outgoing")
        
        if self.path == "/call/ringing":
            call_state.set_state(CallState.RINGING, number, direction)
            logger.info(f"📱 Phone: RINGING ({direction}) - {number}")
            self.send_json({"status": "ok"})
        
        elif self.path == "/call/active":
            call_state.set_state(CallState.ACTIVE, number, direction)
            logger.info(f"📱 Phone: ACTIVE ({direction}) - {number}")
            self.send_json({"status": "ok"})
        
        elif self.path == "/call/ended":
            logger.info(f"📱 Phone: ENDED ({direction}) - {number}")
            call_state.set_state(CallState.IDLE, "", direction)
            self.send_json({"status": "ok"})
        
        elif self.path == "/call/idle":
            call_state.set_state(CallState.IDLE, "", "none")
            self.send_json({"status": "ok"})
        
        else:
            self.send_json({"error": "Unknown endpoint"}, 404)


class HTTPCallServer:
    """HTTP server for receiving call states from phone"""
    
    def __init__(self, host=HTTP_HOST, port=HTTP_PORT):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
    
    def start(self):
        """Start HTTP server in background thread"""
        self.server = HTTPServer((self.host, self.port), CallHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"🌐 HTTP Server started on {self.host}:{self.port}")
    
    def stop(self):
        """Stop HTTP server"""
        if self.server:
            self.server.shutdown()
            logger.info("🌐 HTTP Server stopped")
    
    def get_call_state(self):
        """Get current call state"""
        return call_state.get_state()
    
    def is_outgoing(self):
        """Check if current call is outgoing"""
        return call_state.is_outgoing()
    
    def on_state_change(self, callback):
        """Register callback for state changes"""
        call_state.on_state_change(callback)


if __name__ == "__main__":
    # Test server
    print("Starting HTTP server for testing...")
    server = HTTPCallServer()
    server.start()
    
    print(f"\nServer running on http://{HTTP_HOST}:{HTTP_PORT}")
    print("\nEndpoints:")
    print("  POST /call/ringing  - Call ringing")
    print("  POST /call/active   - Call picked up")
    print("  POST /call/ended    - Call ended")
    print("  GET  /status        - Get current state")
    print("\nPress Ctrl+C to stop...")
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        print("\nStopped.")
