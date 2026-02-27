#!/usr/bin/env python3
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
        self.wfile.write(b"MEX BALANCER PRO - OPERATIONAL")
    def log_message(self, format, *args):
        pass

def start():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=start, daemon=True).start()
    import time
    while True:
        time.sleep(3600)
