#!/usr/bin/env python3
"""CORS Proxy for LM Studio - fixes browser CORS issues"""

import http.server
import urllib.request
import urllib.error
import json

LM_STUDIO_URL = "http://localhost:1234"
PROXY_PORT = 5001

class CORSProxyHandler(http.server.BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def proxy_request(self, method):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        target_url = f"{LM_STUDIO_URL}{self.path}"
        headers = {
            "Content-Type": self.headers.get("Content-Type", "application/json"),
            "Authorization": self.headers.get("Authorization", "")
        }

        try:
            req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req) as resp:
                response_body = resp.read()
                self.send_response(resp.status)
                self.send_cors_headers()
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(e.read())
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        self.proxy_request("GET")

    def do_POST(self):
        self.proxy_request("POST")

    def log_message(self, format, *args):
        print(f"[PROXY] {args[0]}")

if __name__ == "__main__":
    print(f"Starting CORS proxy on http://localhost:{PROXY_PORT}")
    print(f"Forwarding to LM Studio at {LM_STUDIO_URL}")
    print("-" * 50)
    server = http.server.HTTPServer(("127.0.0.1", PROXY_PORT), CORSProxyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
