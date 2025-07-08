#!/usr/bin/env python3
"""
Mock Flopcoin RPC Server

This script provides a mock Flopcoin Core RPC server for testing
wallet integration without requiring the full Flopcoin Core installation.
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
import hashlib
import random
from typing import Dict, Any, List
import threading


class MockFlopcoinRPC(BaseHTTPRequestHandler):
    """Mock Flopcoin RPC server for testing"""
    
    # Mock wallet data
    wallet_balance = 1000.0
    wallet_addresses = [
        "FdKj8mN2pQrS5tUvWxYz1aBcDeFgHiJkL3",
        "FnM4oP6qRs7uVwXyZ2bCdEfGhIjKlM5nO8",
        "FpN5pQ7rSt8vWxYz3cDeFgHiJkLmN6oP9qR"
    ]
    transactions = []
    
    def do_POST(self):
        """Handle POST requests (RPC calls)"""
        # Parse request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            request = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        
        # Check authentication
        if not self._check_auth():
            self.send_error(401, "Unauthorized")
            return
        
        # Handle RPC method
        method = request.get('method', '')
        params = request.get('params', [])
        request_id = request.get('id', 1)
        
        response = self._handle_rpc_method(method, params, request_id)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _check_auth(self) -> bool:
        """Check Basic Authentication"""
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            return False
        
        try:
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)
            return username == 'flopcoinrpc' and password == 'test'
        except:
            return False
    
    def _handle_rpc_method(self, method: str, params: List[Any], request_id: int) -> Dict[str, Any]:
        """Handle different RPC methods"""
        handlers = {
            'getnetworkinfo': self._get_network_info,
            'getblockchaininfo': self._get_blockchain_info,
            'getwalletinfo': self._get_wallet_info,
            'getbalance': self._get_balance,
            'getnewaddress': self._get_new_address,
            'listtransactions': self._list_transactions,
            'sendtoaddress': self._send_to_address,
            'getaddressinfo': self._get_address_info,
            'getblockcount': self._get_block_count,
            'getblockhash': self._get_block_hash,
            'getblock': self._get_block,
            'getrawtransaction': self._get_raw_transaction,
            'decoderawtransaction': self._decode_raw_transaction,
            'signrawtransaction': self._sign_raw_transaction,
            'sendrawtransaction': self._send_raw_transaction,
        }
        
        handler = handlers.get(method)
        if handler:
            try:
                result = handler(params)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -1,
                        "message": str(e)
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method {method} not found"
                }
            }
    
    def _get_network_info(self, params: List[Any]) -> Dict[str, Any]:
        """Mock getnetworkinfo response"""
        return {
            "version": 1000000,
            "subversion": "/Flopcoin:1.0.0/",
            "protocolversion": 70015,
            "localservices": "0000000000000001",
            "localrelay": True,
            "timeoffset": 0,
            "networkactive": True,
            "connections": 8,
            "networks": [
                {
                    "name": "ipv4",
                    "limited": False,
                    "reachable": True,
                    "proxy": "",
                    "proxy_randomize_credentials": False
                }
            ]
        }
    
    def _get_blockchain_info(self, params: List[Any]) -> Dict[str, Any]:
        """Mock getblockchaininfo response"""
        return {
            "chain": "main",
            "blocks": 12345,
            "headers": 12345,
            "bestblockhash": "0000000000000000000000000000000000000000000000000000000000000000",
            "difficulty": 1.0,
            "mediantime": int(time.time()) - 3600,
            "verificationprogress": 1.0,
            "initialblockdownload": False,
            "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
            "size_on_disk": 123456789,
            "pruned": False,
            "pruneheight": None,
            "automatic_pruning": False,
            "prune_target_size": 0,
            "warnings": ""
        }
    
    def _get_wallet_info(self, params: List[Any]) -> Dict[str, Any]:
        """Mock getwalletinfo response"""
        return {
            "walletname": "wallet.dat",
            "walletversion": 169900,
            "balance": self.wallet_balance,
            "unconfirmed_balance": 0.0,
            "immature_balance": 0.0,
            "txcount": len(self.transactions),
            "keypoololdest": int(time.time()) - 86400,
            "keypoolsize": 100,
            "keypoolsize_hd_internal": 100,
            "unlocked_until": 0,
            "paytxfee": 0.0001,
            "hdseedid": "0000000000000000000000000000000000000000000000000000000000000000",
            "private_keys_enabled": True,
            "avoid_reuse": False,
            "scanning": False
        }
    
    def _get_balance(self, params: List[Any]) -> float:
        """Mock getbalance response"""
        return self.wallet_balance
    
    def _get_new_address(self, params: List[Any]) -> str:
        """Mock getnewaddress response"""
        # Generate a new mock address
        new_address = f"F{hashlib.sha256(str(random.random()).encode()).hexdigest()[:33]}"
        self.wallet_addresses.append(new_address)
        return new_address
    
    def _list_transactions(self, params: List[Any]) -> List[Dict[str, Any]]:
        """Mock listtransactions response"""
        return self.transactions
    
    def _send_to_address(self, params: List[Any]) -> str:
        """Mock sendtoaddress response"""
        if len(params) < 2:
            raise ValueError("sendtoaddress requires address and amount")
        
        address = params[0]
        amount = float(params[1])
        
        if amount > self.wallet_balance:
            raise ValueError("Insufficient funds")
        
        # Generate mock transaction ID
        txid = hashlib.sha256(f"{address}{amount}{time.time()}".encode()).hexdigest()
        
        # Create transaction record
        tx = {
            "txid": txid,
            "address": address,
            "category": "send",
            "amount": -amount,
            "confirmations": 0,
            "time": int(time.time()),
            "timereceived": int(time.time()),
            "comment": params[2] if len(params) > 2 else "",
            "fee": 0.0001
        }
        
        self.transactions.append(tx)
        self.wallet_balance -= amount
        
        return txid
    
    def _get_address_info(self, params: List[Any]) -> Dict[str, Any]:
        """Mock getaddressinfo response"""
        address = params[0] if params else ""
        return {
            "address": address,
            "scriptPubKey": f"76a914{hashlib.sha256(address.encode()).hexdigest()[:40]}88ac",
            "ismine": address in self.wallet_addresses,
            "iswatchonly": False,
            "isscript": False,
            "iswitness": False,
            "pubkey": "",
            "iscompressed": True,
            "account": "",
            "timestamp": int(time.time()),
            "hdkeypath": "",
            "hdseedid": "",
            "hdmasterfingerprint": "",
            "labels": []
        }
    
    def _get_block_count(self, params: List[Any]) -> int:
        """Mock getblockcount response"""
        return 12345
    
    def _get_block_hash(self, params: List[Any]) -> str:
        """Mock getblockhash response"""
        return "0000000000000000000000000000000000000000000000000000000000000000"
    
    def _get_block(self, params: List[Any]) -> Dict[str, Any]:
        """Mock getblock response"""
        return {
            "hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "confirmations": 1,
            "size": 1000,
            "weight": 4000,
            "height": 12345,
            "version": 1,
            "versionHex": "00000001",
            "merkleroot": "0000000000000000000000000000000000000000000000000000000000000000",
            "tx": [],
            "time": int(time.time()),
            "mediantime": int(time.time()) - 600,
            "nonce": 0,
            "bits": "1d00ffff",
            "difficulty": 1.0,
            "chainwork": "0000000000000000000000000000000000000000000000000000000000000000",
            "previousblockhash": "0000000000000000000000000000000000000000000000000000000000000000",
            "nextblockhash": "0000000000000000000000000000000000000000000000000000000000000000"
        }
    
    def _get_raw_transaction(self, params: List[Any]) -> str:
        """Mock getrawtransaction response"""
        return "010000000000000000000000000000000000000000000000000000000000000000000000"
    
    def _decode_raw_transaction(self, params: List[Any]) -> Dict[str, Any]:
        """Mock decoderawtransaction response"""
        return {
            "txid": "0000000000000000000000000000000000000000000000000000000000000000",
            "hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "version": 1,
            "size": 100,
            "vsize": 100,
            "weight": 400,
            "locktime": 0,
            "vin": [],
            "vout": []
        }
    
    def _sign_raw_transaction(self, params: List[Any]) -> Dict[str, Any]:
        """Mock signrawtransaction response"""
        return {
            "hex": "010000000000000000000000000000000000000000000000000000000000000000000000",
            "complete": True,
            "errors": []
        }
    
    def _send_raw_transaction(self, params: List[Any]) -> str:
        """Mock sendrawtransaction response"""
        return "0000000000000000000000000000000000000000000000000000000000000000"
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        pass


def start_mock_flopcoin_server(port: int = 32553) -> None:
    """Start the mock Flopcoin RPC server"""
    server = HTTPServer(('127.0.0.1', port), MockFlopcoinRPC)
    print(f"🚀 Starting Mock Flopcoin RPC server on port {port}")
    print(f"   RPC URL: http://127.0.0.1:{port}")
    print(f"   Username: flopcoinrpc")
    print(f"   Password: test")
    print("   Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Stopping Mock Flopcoin RPC server...")
        server.shutdown()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 32553
    start_mock_flopcoin_server(port) 