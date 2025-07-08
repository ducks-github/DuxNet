#!/usr/bin/env python3
"""
Dux_OS Node Health Monitor Daemon
A comprehensive health monitoring system for decentralized Linux distribution nodes.
"""

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import os
import signal
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import psutil
import requests
import yaml

# Optional imports with fallbacks
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, padding
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    logging.warning("cryptography library not available, signature features disabled")

try:
    import websockets
    from websockets.server import serve as ws_serve

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logging.warning("websockets library not available, GUI integration disabled")

import sqlite3
import threading
from collections import defaultdict, deque
from sqlite3 import Connection

# Import the base daemon class
sys.path.append(os.path.join(os.path.dirname(__file__), "duxos_daemon_template"))
try:
    from daemon import DuxOSDaemon
except ImportError:
    # Fallback if daemon template is not available
    class DuxOSDaemon:
        def __init__(self, config):
            self.config = config
            self.running = True

        def run(self):
            pass


@dataclass
class NodeMetrics:
    """Node health metrics data structure"""

    uptime: int
    load_average: List[float]
    available_memory: int  # MB
    available_cpu: int
    success_rate: float
    reputation_score: float
    task_results: List[Dict[str, Any]]  # Proof-of-computation data


@dataclass
class HealthStatus:
    """Node health status data structure"""

    node_id: str
    wallet_address: str
    ip_address: str
    port: int
    status: str  # healthy, unhealthy, offline
    last_heartbeat: datetime
    metrics: NodeMetrics
    signature: str
    proof_of_computation: Optional[str] = None


class RateLimiter:
    """Rate limiting implementation for anti-sybil protection"""

    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
        self.lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limiting"""
        now = time.time()
        with self.lock:
            # Clean old requests
            while (
                self.requests[identifier]
                and self.requests[identifier][0] < now - self.window_seconds
            ):
                self.requests[identifier].popleft()

            # Check if under limit
            if len(self.requests[identifier]) < self.max_requests:
                self.requests[identifier].append(now)
                return True
            return False


class ExponentialBackoff:
    """Exponential backoff implementation for error handling"""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 300.0, max_retries: int = 5):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries

    async def retry(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    break

                delay = min(self.base_delay * (2**attempt), self.max_delay)
                await asyncio.sleep(delay)

        if last_exception:
            raise last_exception
        else:
            raise Exception("Unknown error occurred")


class IPFSStorage:
    """IPFS/DHT storage implementation with optimization features"""

    def __init__(self, endpoint: str, config: Dict[str, Any]):
        self.endpoint = endpoint
        self.config = config
        self.cache = {}
        self.cache_size = (
            config.get("ipfs_optimization", {}).get("cache_size_mb", 100) * 1024 * 1024
        )
        self.current_cache_size = 0

    async def store_health_data(self, health_data: Dict[str, Any]) -> str:
        """Store health data to IPFS with compression and deduplication"""
        try:
            # Compress data if enabled
            if self.config.get("ipfs_optimization", {}).get("compression", True):
                import gzip

                data_bytes = json.dumps(health_data).encode("utf-8")
                compressed_data = gzip.compress(data_bytes)
                health_data["_compressed"] = True
                health_data["_original_size"] = len(data_bytes)
                health_data["_compressed_size"] = len(compressed_data)

            # Generate content hash for deduplication
            content_hash = hashlib.sha256(
                json.dumps(health_data, sort_keys=True).encode()
            ).hexdigest()

            # Check cache first
            if content_hash in self.cache:
                return self.cache[content_hash]

            # Store to IPFS (placeholder implementation)
            # In real implementation, this would use IPFS HTTP API
            ipfs_hash = f"Qm{content_hash[:44]}"  # Placeholder IPFS hash

            # Cache the result
            self._add_to_cache(content_hash, ipfs_hash)

            return ipfs_hash

        except Exception as e:
            logging.error(f"Failed to store health data to IPFS: {e}")
            raise

    def _add_to_cache(self, content_hash: str, ipfs_hash: str):
        """Add to cache with size management"""
        cache_entry_size = len(content_hash) + len(ipfs_hash)

        # Remove old entries if cache is full
        while self.current_cache_size + cache_entry_size > self.cache_size and self.cache:
            oldest_key = next(iter(self.cache))
            removed_size = len(oldest_key) + len(self.cache[oldest_key])
            del self.cache[oldest_key]
            self.current_cache_size -= removed_size

        self.cache[content_hash] = ipfs_hash
        self.current_cache_size += cache_entry_size


class DynamicThresholds:
    """Dynamic threshold management with governance layer integration"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.thresholds = config.get("health_monitor", {}).get("thresholds", {})
        self.last_update = 0
        self.update_interval = config.get("dynamic_thresholds", {}).get("update_interval", 3600)

    async def update_thresholds(self):
        """Update thresholds from governance layer"""
        try:
            if not self.config.get("dynamic_thresholds", {}).get("enabled", False):
                return

            now = time.time()
            if now - self.last_update < self.update_interval:
                return

            governance_endpoint = self.config.get("dynamic_thresholds", {}).get(
                "governance_endpoint"
            )
            if not governance_endpoint:
                return

            response = requests.get(governance_endpoint, timeout=10)
            if response.status_code == 200:
                new_thresholds = response.json()
                self.thresholds.update(new_thresholds)
                self.last_update = now
                logging.info(f"Updated thresholds from governance layer: {new_thresholds}")

        except Exception as e:
            logging.warning(f"Failed to update thresholds from governance layer: {e}")


class ProofOfComputation:
    """Proof-of-computation implementation for anti-sybil protection"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.task_results_cache = {}

    def generate_proof(self, task_results: List[Dict[str, Any]]) -> str:
        """Generate proof-of-computation from task results"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logging.warning("Cryptography not available, skipping proof generation")
                return ""

            # Create a proof from recent task results
            proof_data = {
                "timestamp": int(time.time()),
                "task_count": len(task_results),
                "results_hash": hashlib.sha256(
                    json.dumps(task_results, sort_keys=True).encode()
                ).hexdigest(),
                "node_id": self.config["health_monitor"]["node_id"],
            }

            # Sign the proof
            private_key = self._load_private_key()
            proof_bytes = json.dumps(proof_data, sort_keys=True).encode()
            signature = private_key.sign(proof_bytes)

            proof_data["signature"] = base64.b64encode(signature).decode()
            return base64.b64encode(json.dumps(proof_data).encode()).decode()

        except Exception as e:
            logging.error(f"Failed to generate proof-of-computation: {e}")
            return ""

    def verify_proof(self, proof: str, public_key_bytes: bytes) -> bool:
        """Verify proof-of-computation"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logging.warning("Cryptography not available, skipping proof verification")
                return False

            proof_data = json.loads(base64.b64decode(proof).decode())
            signature = base64.b64decode(proof_data["signature"])
            proof_bytes = json.dumps(
                {k: v for k, v in proof_data.items() if k != "signature"}, sort_keys=True
            ).encode()

            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature, proof_bytes)
            return True

        except Exception as e:
            logging.error(f"Failed to verify proof-of-computation: {e}")
            return False

    def _load_private_key(self) -> ed25519.Ed25519PrivateKey:
        """Load private key for signing"""
        key_path = self.config["security"]["private_key_path"]
        with open(key_path, "rb") as f:
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(f.read())
        return private_key


class HealthMonitorDaemon(DuxOSDaemon):
    """Comprehensive health monitoring daemon for Dux_OS nodes"""

    def __init__(self, config_path: str = "/etc/duxnet/registry.yaml"):
        self.config = self._load_config(config_path)
        self.node_id = self.config["health_monitor"]["node_id"]
        self.wallet_address = self.config["health_monitor"]["wallet_address"]
        self.ip_address = self.config["health_monitor"]["ip_address"]
        self.port = self.config["health_monitor"]["port"]

        # Initialize components
        self.rate_limiter = RateLimiter(
            self.config["anti_sybil"]["rate_limiting"]["max_heartbeats_per_minute"]
        )
        self.backoff = ExponentialBackoff(**self.config["error_handling"]["exponential_backoff"])
        self.ipfs_storage = IPFSStorage(self.config["health_monitor"]["ipfs_endpoint"], self.config)
        self.dynamic_thresholds = DynamicThresholds(self.config)
        self.proof_of_computation = ProofOfComputation(self.config)

        # Database connection
        self.db_conn = self._init_database()

        # WebSocket server for GUI integration
        self.websocket_clients = set()
        self.websocket_server = None

        # Batch processing
        self.health_batch = []
        self.batch_lock = threading.Lock()

        # Initialize logging
        self._setup_logging()

        super().__init__(self.config)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logging.error(f"Failed to load config from {config_path}: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Setup structured logging"""
        log_config = self.config["logging"]
        log_file = self.config["health_monitor"]["log_file"]

        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, log_config["level"]),
            format=log_config["format"],
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )

    def _init_database(self) -> Connection:
        """Initialize SQLite database for health data persistence"""
        db_uri = self.config["database"]["uri"]
        db_path = db_uri.replace("sqlite:///", "")

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS health_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                metrics TEXT NOT NULL,
                signature TEXT NOT NULL,
                proof_of_computation TEXT,
                ipfs_hash TEXT
            )
        """
        )
        conn.commit()
        return conn

    def collect_metrics(self) -> NodeMetrics:
        """Collect comprehensive system metrics"""
        try:
            # Basic system metrics
            uptime = int(time.time() - psutil.boot_time())
            load_avg = list(psutil.getloadavg())
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count() or 1  # Handle None case

            # Calculate success rate from recent task results
            success_rate = self._calculate_success_rate()

            # Get reputation score (placeholder - would integrate with reputation system)
            reputation_score = self._get_reputation_score()

            # Get recent task results for proof-of-computation
            task_results = self._get_recent_task_results()

            return NodeMetrics(
                uptime=uptime,
                load_average=load_avg,
                available_memory=memory.available // (1024 * 1024),  # MB
                available_cpu=cpu_count,
                success_rate=success_rate,
                reputation_score=reputation_score,
                task_results=task_results,
            )

        except Exception as e:
            logging.error(f"Failed to collect metrics: {e}")
            # Return default metrics on error
            return NodeMetrics(
                uptime=0,
                load_average=[0.0, 0.0, 0.0],
                available_memory=0,
                available_cpu=1,
                success_rate=0.0,
                reputation_score=0.0,
                task_results=[],
            )

    def _calculate_success_rate(self) -> float:
        """Calculate success rate from recent task executions"""
        # Placeholder implementation - would integrate with task engine
        # In real implementation, this would query task execution history
        return 0.98  # 98% success rate

    def _get_reputation_score(self) -> float:
        """Get current reputation score"""
        # Placeholder implementation - would integrate with reputation system
        return 0.85  # 85% reputation score

    def _get_recent_task_results(self) -> List[Dict[str, Any]]:
        """Get recent task results for proof-of-computation"""
        # Placeholder implementation - would integrate with task engine
        return [
            {
                "task_id": str(uuid.uuid4()),
                "result": "success",
                "timestamp": int(time.time()),
                "computation_hash": hashlib.sha256(f"task_{time.time()}".encode()).hexdigest(),
            }
        ]

    def is_healthy(self, metrics: NodeMetrics) -> bool:
        """Determine if node is healthy based on metrics and thresholds"""
        try:
            thresholds = self.dynamic_thresholds.thresholds

            # Check load average
            if max(metrics.load_average) >= thresholds["load_average"]:
                return False

            # Check available memory
            if metrics.available_memory < thresholds["min_memory_mb"]:
                return False

            # Check success rate
            if metrics.success_rate < thresholds["min_success_rate"]:
                return False

            # Check reputation score
            if metrics.reputation_score < thresholds["min_reputation_score"]:
                return False

            return True

        except Exception as e:
            logging.error(f"Failed to check health status: {e}")
            return False

    def sign_payload(self, payload: Dict[str, Any]) -> str:
        """Sign payload with node's private key"""
        try:
            if not CRYPTOGRAPHY_AVAILABLE:
                logging.warning("Cryptography not available, skipping signature")
                return ""

            private_key = self.proof_of_computation._load_private_key()
            payload_bytes = json.dumps(payload, sort_keys=True).encode()
            signature = private_key.sign(payload_bytes)
            return base64.b64encode(signature).decode()

        except Exception as e:
            logging.error(f"Failed to sign payload: {e}")
            return ""

    async def send_heartbeat(self) -> bool:
        """Send heartbeat to registry with all required data"""
        try:
            # Check rate limiting
            if not self.rate_limiter.is_allowed(self.node_id):
                logging.warning("Rate limit exceeded for heartbeat")
                return False

            # Collect metrics
            metrics = self.collect_metrics()

            # Generate proof-of-computation
            proof = ""
            if self.config["anti_sybil"]["proof_of_computation_required"]:
                proof = self.proof_of_computation.generate_proof(metrics.task_results)

            # Create health status
            health_status = HealthStatus(
                node_id=self.node_id,
                wallet_address=self.wallet_address,
                ip_address=self.ip_address,
                port=self.port,
                status="healthy" if self.is_healthy(metrics) else "unhealthy",
                last_heartbeat=datetime.utcnow(),
                metrics=metrics,
                signature="",  # Will be set after signing
                proof_of_computation=proof,
            )

            # Convert to dict and sign
            payload = asdict(health_status)
            payload["last_heartbeat"] = payload["last_heartbeat"].isoformat()
            payload["metrics"] = asdict(payload["metrics"])

            signature = self.sign_payload(payload)
            payload["signature"] = signature

            # Send to registry with exponential backoff
            async def send_request():
                response = requests.post(
                    f"https://registry.duxos.net/nodes/health",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()

            result = await self.backoff.retry(send_request)

            # Store to IPFS
            ipfs_hash = await self.ipfs_storage.store_health_data(payload)

            # Store to local database
            self._store_health_data(payload, ipfs_hash)

            # Broadcast to WebSocket clients
            if WEBSOCKETS_AVAILABLE:
                await self._broadcast_health_update(payload)

            logging.info(f"Heartbeat sent successfully: {result}")
            return True

        except Exception as e:
            logging.error(f"Failed to send heartbeat: {e}")
            return False

    def _store_health_data(self, health_data: Dict[str, Any], ipfs_hash: str):
        """Store health data to local database"""
        try:
            self.db_conn.execute(
                """
                INSERT INTO health_history 
                (node_id, status, metrics, signature, proof_of_computation, ipfs_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    health_data["node_id"],
                    health_data["status"],
                    json.dumps(health_data["metrics"]),
                    health_data["signature"],
                    health_data.get("proof_of_computation", ""),
                    ipfs_hash,
                ),
            )
            self.db_conn.commit()

            # Clean old data
            retention_days = self.config["health_monitor"]["health_history_retention"] // 86400
            self.db_conn.execute(
                """
                DELETE FROM health_history 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(
                    retention_days
                )
            )
            self.db_conn.commit()

        except Exception as e:
            logging.error(f"Failed to store health data: {e}")

    async def _broadcast_health_update(self, health_data: Dict[str, Any]):
        """Broadcast health update to WebSocket clients"""
        if not self.websocket_clients or not WEBSOCKETS_AVAILABLE:
            return

        message = json.dumps(
            {
                "type": "health_update",
                "data": health_data,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        disconnected_clients = set()
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except Exception:
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected_clients

    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections for GUI integration"""
        if not WEBSOCKETS_AVAILABLE:
            return

        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                # Handle client messages (e.g., filter requests)
                data = json.loads(message)
                if data.get("type") == "filter_request":
                    await self._handle_filter_request(websocket, data)
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            self.websocket_clients.discard(websocket)

    async def _handle_filter_request(self, websocket, data):
        """Handle filter requests from GUI clients"""
        try:
            filter_type = data.get("filter", "all")

            # Query database based on filter
            if filter_type == "all":
                cursor = self.db_conn.execute(
                    """
                    SELECT * FROM health_history 
                    ORDER BY timestamp DESC LIMIT 100
                """
                )
            else:
                cursor = self.db_conn.execute(
                    """
                    SELECT * FROM health_history 
                    WHERE status = ? 
                    ORDER BY timestamp DESC LIMIT 100
                """,
                    (filter_type,),
                )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "node_id": row[1],
                        "timestamp": row[2],
                        "status": row[3],
                        "metrics": json.loads(row[4]),
                        "signature": row[5],
                        "proof_of_computation": row[6],
                        "ipfs_hash": row[7],
                    }
                )

            response = {
                "type": "filter_response",
                "filter": filter_type,
                "data": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

            await websocket.send(json.dumps(response))

        except Exception as e:
            logging.error(f"Failed to handle filter request: {e}")

    async def start_websocket_server(self):
        """Start WebSocket server for GUI integration"""
        if not WEBSOCKETS_AVAILABLE:
            logging.warning("WebSockets not available, GUI integration disabled")
            return

        try:
            ws_endpoint = self.config["gui_integration"]["websocket_endpoint"]
            host, port = ws_endpoint.replace("ws://", "").split(":")
            port = int(port)

            self.websocket_server = await ws_serve(self.websocket_handler, host, port)
            logging.info(f"WebSocket server started on {ws_endpoint}")

        except Exception as e:
            logging.error(f"Failed to start WebSocket server: {e}")

    async def batch_process_health_data(self):
        """Process health data in batches for scalability"""
        while self.running:
            try:
                with self.batch_lock:
                    if (
                        len(self.health_batch)
                        >= self.config["scalability"]["batch_processing"]["batch_size"]
                    ):
                        batch = self.health_batch.copy()
                        self.health_batch.clear()
                    else:
                        batch = []

                if batch:
                    # Process batch (e.g., bulk store to IPFS)
                    await self._process_health_batch(batch)

                await asyncio.sleep(self.config["scalability"]["batch_processing"]["batch_timeout"])

            except Exception as e:
                logging.error(f"Batch processing error: {e}")
                await asyncio.sleep(1)

    async def _process_health_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of health data"""
        try:
            # Bulk store to IPFS
            for health_data in batch:
                await self.ipfs_storage.store_health_data(health_data)

            logging.info(f"Processed batch of {len(batch)} health records")

        except Exception as e:
            logging.error(f"Failed to process health batch: {e}")

    async def run_async(self):
        """Main async run loop"""
        try:
            # Start WebSocket server
            if WEBSOCKETS_AVAILABLE:
                await self.start_websocket_server()

            # Start batch processing
            batch_task = asyncio.create_task(self.batch_process_health_data())

            # Main heartbeat loop
            heartbeat_interval = self.config["health_monitor"]["heartbeat_interval"]

            while self.running:
                try:
                    # Update dynamic thresholds
                    await self.dynamic_thresholds.update_thresholds()

                    # Send heartbeat
                    success = await self.send_heartbeat()

                    if not success:
                        logging.warning("Heartbeat failed, will retry on next cycle")

                    # Wait for next heartbeat
                    await asyncio.sleep(heartbeat_interval)

                except Exception as e:
                    logging.error(f"Error in main loop: {e}")
                    await asyncio.sleep(5)

            # Cleanup
            batch_task.cancel()
            if self.websocket_server and WEBSOCKETS_AVAILABLE:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()

        except Exception as e:
            logging.error(f"Fatal error in async run loop: {e}")

    def run(self):
        """Main run method (synchronous wrapper for async)"""
        logging.info("Health Monitor Daemon starting...")

        try:
            # Run the async loop
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            logging.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logging.error(f"Fatal error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.db_conn:
                self.db_conn.close()
            logging.info("Health Monitor Daemon stopped.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Dux_OS Health Monitor Daemon")
    parser.add_argument(
        "--config", default="/etc/duxnet/registry.yaml", help="Path to configuration file"
    )
    parser.add_argument("command", choices=["start", "stop", "status"], help="Daemon command")

    args = parser.parse_args()

    if args.command == "start":
        daemon = HealthMonitorDaemon(args.config)
        daemon.run()
    elif args.command == "stop":
        # Implementation for stopping daemon
        print("Stop command not implemented yet")
    elif args.command == "status":
        # Implementation for checking daemon status
        print("Status command not implemented yet")


if __name__ == "__main__":
    main()
