#!/usr/bin/env python3
"""
Mock Ethereum RPC Server for testing
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class MockEthereumHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Check for basic authentication
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Ethereum RPC"')
            self.end_headers()
            return
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode('utf-8'))
            method = request.get('method', '')
            params = request.get('params', [])
            request_id = request.get('id', 1)
            
            print(f"Mock Ethereum server received: {method} with params: {params}")
            
            # Mock responses for common RPC methods
            if method == 'eth_getBalance':
                response = {
                    "result": "0x56bc75e2d63100000",  # 100 ETH in Wei
                    "error": None,
                    "id": request_id
                }
            elif method == 'eth_accounts':
                response = {
                    "result": ["0x2b3711a4393C36863cf5De789655cdFdf6270921"],
                    "error": None,
                    "id": request_id
                }
            elif method == 'eth_getTransactionCount':
                response = {
                    "result": "0x0",
                    "error": None,
                    "id": request_id
                }
            elif method == 'eth_gasPrice':
                response = {
                    "result": "0x3b9aca00",  # 1 Gwei
                    "error": None,
                    "id": request_id
                }
            elif method == 'eth_sendRawTransaction':
                response = {
                    "result": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                    "error": None,
                    "id": request_id
                }
            elif method == 'eth_getTransactionReceipt':
                response = {
                    "result": {
                        "transactionHash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
                        "blockNumber": "0x1234",
                        "blockHash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                        "gasUsed": "0x5208",
                        "status": "0x1"
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
        self.wfile.write(b"Mock Ethereum RPC Server Running\n")
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

def run_mock_ethereum_server(port=8545):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockEthereumHandler)
    print(f"Mock Ethereum RPC server starting on port {port}")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock Ethereum server...")
        httpd.shutdown()

if __name__ == '__main__':
    run_mock_ethereum_server() 