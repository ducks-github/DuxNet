#!/usr/bin/env python3
"""
Mock Flopcoin RPC Server for testing
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class MockFlopcoinHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Check for basic authentication
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Flopcoin RPC"')
            self.end_headers()
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode('utf-8'))
            method = request.get('method', '')
            params = request.get('params', [])
            request_id = request.get('id', 1)
            
            print(f"Mock server received: {method} with params: {params}")
            
            # Mock responses for common RPC methods
            if method == 'getnewaddress':
                response = {
                    "result": "F1234567890abcdef1234567890abcdef12345678",
                    "error": None,
                    "id": request_id
                }
            elif method == 'getbalance':
                response = {
                    "result": 100.5,
                    "error": None,
                    "id": request_id
                }
            elif method == 'sendtoaddress':
                response = {
                    "result": "txid1234567890abcdef1234567890abcdef12345678",
                    "error": None,
                    "id": request_id
                }
            elif method == 'getaddressinfo':
                response = {
                    "result": {
                        "address": params[0] if params else "F1234567890abcdef1234567890abcdef12345678",
                        "scriptPubKey": "76a9141234567890abcdef1234567890abcdef1234567890abcdef88ac",
                        "ismine": True,
                        "iswatchonly": False,
                        "isscript": False,
                        "iswitness": False,
                        "pubkey": "02abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                        "iscompressed": True,
                        "account": "",
                        "timestamp": int(time.time()),
                        "hdkeypath": "m/0'/0/0",
                        "hdmasterkeyid": "1234567890abcdef1234567890abcdef12345678"
                    },
                    "error": None,
                    "id": request_id
                }
            else:
                response = {
                    "result": None,
                    "error": {"code": -32601, "message": f"Method {method} not found"},
                    "id": request_id
                }
            
        except Exception as e:
            response = {
                "result": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                "id": request_id
            }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Mock Flopcoin RPC Server Running\n")
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

def run_mock_server(port=8332):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockFlopcoinHandler)
    print(f"Mock Flopcoin RPC server starting on port {port}")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_mock_server() 