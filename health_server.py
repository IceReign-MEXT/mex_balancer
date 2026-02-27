#!/usr/bin/env python3
import http.server, socketserver, threading, os
PORT = int(os.environ.get("PORT", 10000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MEX BALANCER PRO - OPERATIONAL")
    def log_message(self, *args): pass

def start():
    socketserver.TCPServer(("", PORT), Handler).serve_forever()

threading.Thread(target=start, daemon=True).start()
import time
while True: time.sleep(3600)
