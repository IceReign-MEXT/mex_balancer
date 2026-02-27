"""Health check server for Render"""
import http.server
import socketserver
import threading
import os

PORT = int(os.environ.get("PORT", 10000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MEX BALANCER BOT - OPERATIONAL")
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    thread = threading.Thread(target=start_server, daemon=True)
    thread.start()
    
    # Keep main thread alive
    import time
    while True:
        time.sleep(3600)
