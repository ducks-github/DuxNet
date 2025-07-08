import json
import random
import string
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict


class MockFlopcoinRPCHandler(BaseHTTPRequestHandler):
    """Mock RPC server to simulate Flopcoin Core interactions."""

    def _generate_mock_address(self) -> str:
        """Generate a mock Flopcoin address."""
        prefix = "FLOP"
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=34))
        return f"{prefix}{random_part}"

    def do_POST(self):
        """Handle POST requests simulating RPC calls."""
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        rpc_request = json.loads(post_data.decode("utf-8"))

        # Simulate RPC method responses
        response_data = {"jsonrpc": "2.0", "id": rpc_request.get("id", 1)}

        try:
            method = rpc_request.get("method")

            if method == "getnewaddress":
                response_data["result"] = self._generate_mock_address()

            elif method == "getbalance":
                response_data["result"] = round(random.uniform(0.01, 1000.00), 2)

            elif method == "sendtoaddress":
                # Simulate successful transaction
                response_data["result"] = "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=64)
                )

            else:
                response_data["error"] = {"code": -32601, "message": f"Method {method} not found"}

        except Exception as e:
            response_data["error"] = {"code": -32000, "message": str(e)}

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode("utf-8"))


def run_mock_rpc_server(port: int = 32553):
    """Run the mock Flopcoin RPC server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, MockFlopcoinRPCHandler)
    print(f"Mock Flopcoin RPC server running on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_mock_rpc_server()
