#!/usr/bin/env python3
import argparse
import logging
import os
import signal
import sys
import time
import yaml
import socket
import ssl
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from flask import Flask, request, jsonify
import json
import redis
import prometheus_client
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, Optional, List
import hashlib
import hmac

CONFIG_PATH = os.environ.get('DUXOS_DAEMON_CONFIG', 'config.yaml')
LOG_PATH = os.environ.get('DUXOS_DAEMON_LOG', 'daemon.log')
PID_PATH = os.environ.get('DUXOS_DAEMON_PID', 'daemon.pid')

# Global Flask app instance (to be initialized by DuxOSDaemon)
app = None

# Prometheus metrics
REQUEST_COUNT = prometheus_client.Counter('duxnet_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = prometheus_client.Histogram('duxnet_request_duration_seconds', 'Request latency')
ACTIVE_CONNECTIONS = prometheus_client.Gauge('duxnet_active_connections', 'Active connections')
ERROR_COUNT = prometheus_client.Counter('duxnet_errors_total', 'Total errors', ['type'])

class MessageQueue:
    """Message queue implementation using Redis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redis_client = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            uri = self.config.get('message_queue', {}).get('uri', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(uri)
            # Test connection
            self.redis_client.ping()
            self.connected = True
            logging.info("Connected to Redis message queue")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
            self.connected = False
    
    def publish(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish message to channel"""
        if not self.connected:
            return False
        try:
            self.redis_client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            return False
    
    def subscribe(self, channel: str, callback) -> bool:
        """Subscribe to channel"""
        if not self.connected:
            return False
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(**{channel: callback})
            pubsub.run_in_thread(sleep_time=0.001)
            return True
        except Exception as e:
            logging.error(f"Failed to subscribe to channel: {e}")
            return False
    
    def enqueue(self, queue: str, message: Dict[str, Any]) -> bool:
        """Add message to queue"""
        if not self.connected:
            return False
        try:
            self.redis_client.lpush(queue, json.dumps(message))
            return True
        except Exception as e:
            logging.error(f"Failed to enqueue message: {e}")
            return False
    
    def dequeue(self, queue: str, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """Get message from queue"""
        if not self.connected:
            return None
        try:
            result = self.redis_client.brpop(queue, timeout=timeout)
            if result:
                return json.loads(result[1])
            return None
        except Exception as e:
            logging.error(f"Failed to dequeue message: {e}")
            return None

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limit_per_minute = config.get('security', {}).get('rate_limit_per_minute', 60)
        self.rate_limit_window_seconds = 60
        self.connection_timestamps = defaultdict(deque)
        self.ip_blacklist = set()
        self.blacklist_duration = 300  # 5 minutes
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limiting"""
        current_time = time.time()
        
        # Check if IP is blacklisted
        if identifier in self.ip_blacklist:
            return False
        
        # Clean old timestamps
        timestamps = self.connection_timestamps[identifier]
        while timestamps and timestamps[0] < current_time - self.rate_limit_window_seconds:
            timestamps.popleft()
        
        # Check rate limit
        if len(timestamps) >= self.rate_limit_per_minute:
            # Add to blacklist for repeated violations
            self.ip_blacklist.add(identifier)
            logging.warning(f"Rate limit exceeded for {identifier}, added to blacklist")
            return False
        
        # Add current timestamp
        timestamps.append(current_time)
        return True
    
    def cleanup_blacklist(self):
        """Clean up expired blacklist entries"""
        current_time = time.time()
        # This is a simplified cleanup - in production, you'd use a more sophisticated approach
        if len(self.ip_blacklist) > 1000:  # Prevent memory issues
            self.ip_blacklist.clear()

class Monitoring:
    """Monitoring and metrics collection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('monitoring', {}).get('enabled', False)
        self.metrics_port = config.get('monitoring', {}).get('metrics_port', 9090)
        self.metrics_server = None
        self.metrics_thread = None
        
        # Custom metrics
        self.daemon_uptime = prometheus_client.Gauge('duxnet_daemon_uptime_seconds', 'Daemon uptime in seconds')
        self.config_reloads = prometheus_client.Counter('duxnet_config_reloads_total', 'Total config reloads')
        self.message_queue_operations = prometheus_client.Counter('duxnet_mq_operations_total', 'Message queue operations', ['operation', 'status'])
        
        if self.enabled:
            self._start_metrics_server()
    
    def _start_metrics_server(self):
        """Start Prometheus metrics server"""
        try:
            prometheus_client.start_http_server(self.metrics_port)
            logging.info(f"Prometheus metrics server started on port {self.metrics_port}")
        except Exception as e:
            logging.error(f"Failed to start metrics server: {e}")
            self.enabled = False
    
    def record_request(self, method: str, endpoint: str, duration: float, success: bool = True):
        """Record request metrics"""
        if not self.enabled:
            return
        
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.observe(duration)
        
        if not success:
            ERROR_COUNT.labels(type='request_error').inc()
    
    def record_connection(self, active: bool):
        """Record connection metrics"""
        if not self.enabled:
            return
        
        if active:
            ACTIVE_CONNECTIONS.inc()
        else:
            ACTIVE_CONNECTIONS.dec()
    
    def update_uptime(self, uptime_seconds: float):
        """Update uptime metric"""
        if self.enabled:
            self.daemon_uptime.set(uptime_seconds)
    
    def record_config_reload(self):
        """Record config reload"""
        if self.enabled:
            self.config_reloads.inc()
    
    def record_mq_operation(self, operation: str, success: bool):
        """Record message queue operation"""
        if self.enabled:
            status = 'success' if success else 'error'
            self.message_queue_operations.labels(operation=operation, status=status).inc()

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': time.time() - getattr(self.server, 'start_time', time.time())
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # Return Prometheus metrics
            metrics = prometheus_client.generate_latest()
            self.wfile.write(metrics)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logging.info(f"Health check: {format % args}")

class ServiceDiscoveryAgent:
    def __init__(self, config, daemon_id):
        self.config = config
        self.daemon_id = daemon_id
        self.enabled = config.get('service_discovery', {}).get('enabled', False)
        self.broadcast_port = config.get('service_discovery', {}).get('broadcast_port', 9334)
        self.broadcast_interval = config.get('service_discovery', {}).get('broadcast_interval', 15)
        self.service_type = config.get('service_discovery', {}).get('service_type', 'duxnet-daemon')

        self.running = False
        self.broadcast_thread = None
        self.listen_thread = None
        self.known_peers = {}

    def _broadcast_presence(self):
        logging.info(f"Service Discovery: Broadcasting presence every {self.broadcast_interval} seconds.")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)

        message = {
            'type': 'duxnet_discovery',
            'daemon_id': self.daemon_id,
            'service_type': self.service_type,
            'address': {
                'ip': '0.0.0.0',
                'duxnet_port': self.config.get('duxnet_port')
            },
            'timestamp': time.time()
        }

        while self.running:
            try:
                encoded_message = json.dumps(message).encode('utf-8')
                sock.sendto(encoded_message, ('<broadcast>', self.broadcast_port))
            except Exception as e:
                logging.error(f"Service Discovery: Error broadcasting presence: {e}")
            time.sleep(self.broadcast_interval)
        sock.close()

    def _listen_for_broadcasts(self):
        logging.info(f"Service Discovery: Listening for broadcasts on port {self.broadcast_port}.")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.broadcast_port))
        sock.settimeout(1)

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))

                if message.get('type') == 'duxnet_discovery' and message.get('daemon_id') != self.daemon_id:
                    peer_id = message['daemon_id']
                    peer_ip = addr[0]
                    peer_duxnet_port = message['address'].get('duxnet_port')
                    
                    if peer_duxnet_port:
                        peer_address = (peer_ip, peer_duxnet_port)
                        self.known_peers[peer_id] = {
                            'address': peer_address,
                            'service_type': message.get('service_type'),
                            'last_seen': time.time()
                        }
                        logging.info(f"Service Discovery: Discovered peer: {peer_id} at {peer_address} (Type: {message.get('service_type')})")
            except socket.timeout:
                continue
            except Exception as e:
                logging.error(f"Service Discovery: Error listening for broadcasts: {e}")
        sock.close()

    def start(self):
        if self.enabled:
            self.running = True
            self.broadcast_thread = threading.Thread(target=self._broadcast_presence)
            self.broadcast_thread.daemon = True
            self.broadcast_thread.start()

            self.listen_thread = threading.Thread(target=self._listen_for_broadcasts)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            logging.info("Service Discovery Agent started.")

    def stop(self):
        if self.enabled and self.running:
            self.running = False
            time.sleep(1)
            logging.info("Service Discovery Agent stopped.")

class DuxOSDaemon:
    def __init__(self, config):
        self.config = config
        self.running = False
        self.daemon_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        self.start_time = time.time()
        
        # Initialize infrastructure components
        self.message_queue = MessageQueue(config)
        self.rate_limiter = RateLimiter(config)
        self.monitoring = Monitoring(config)
        
        # Service discovery
        self.service_discovery_agent = ServiceDiscoveryAgent(config, self.daemon_id)
        
        # Configuration hot-reloading
        self.config_file_mtime = os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else 0
        
        # Flask app for REST API
        global app
        app = Flask(__name__)
        
        @app.route('/api/v1/status', methods=['GET'])
        def get_status():
            start_time = time.time()
            try:
                response = {
                    'status': 'running',
                    'daemon_id': self.daemon_id,
                    'uptime': time.time() - self.start_time,
                    'config_reloads': getattr(self.monitoring, 'config_reloads', 0),
                    'message_queue_connected': self.message_queue.connected
                }
                self.monitoring.record_request('GET', '/api/v1/status', time.time() - start_time, True)
                return jsonify(response)
            except Exception as e:
                self.monitoring.record_request('GET', '/api/v1/status', time.time() - start_time, False)
                return jsonify({'error': str(e)}), 500

        @app.route('/api/v1/config', methods=['GET'])
        def get_daemon_config():
            start_time = time.time()
            try:
                # Return safe config (without sensitive data)
                safe_config = {
                    'heartbeat_interval': self.config.get('heartbeat_interval'),
                    'duxnet_port': self.config.get('duxnet_port'),
                    'monitoring_enabled': self.config.get('monitoring', {}).get('enabled'),
                    'tls_enabled': self.config.get('security', {}).get('tls_enabled')
                }
                self.monitoring.record_request('GET', '/api/v1/config', time.time() - start_time, True)
                return jsonify(safe_config)
            except Exception as e:
                self.monitoring.record_request('GET', '/api/v1/config', time.time() - start_time, False)
                return jsonify({'error': str(e)}), 500

        @app.route('/api/v1/heartbeat_interval', methods=['GET'])
        def get_heartbeat_interval():
            return jsonify({'heartbeat_interval': self.config.get('heartbeat_interval', 10)})

        @app.route('/api/v1/peers', methods=['GET'])
        def get_known_peers():
            # Clean up old peers before returning
            current_time = time.time()
            active_peers = [
                peer for peer in self.service_discovery_agent.known_peers.values()
                if current_time - peer['last_seen'] < 300  # 5 minutes
            ]
            return jsonify({'peers': active_peers})

    def _check_and_reload_config(self):
        """Check if config file has changed and reload if necessary"""
        try:
            if os.path.exists(CONFIG_PATH):
                current_mtime = os.path.getmtime(CONFIG_PATH)
                if current_mtime > self.config_file_mtime:
                    logging.info("Configuration file changed, reloading...")
                    with open(CONFIG_PATH, 'r') as f:
                        self.config = yaml.safe_load(f)
                    self.config_file_mtime = current_mtime
                    self.monitoring.record_config_reload()
                    logging.info("Configuration reloaded successfully")
        except Exception as e:
            logging.error(f"Failed to reload configuration: {e}")

    def run(self):
        logging.info('DuxOSDaemon starting...')
        self.running = True
        
        # Start service discovery
        self.service_discovery_agent.start()

        while self.running:
            # --- Main daemon logic goes here ---
            logging.info('Daemon heartbeat...')

            # Implement configuration hot-reloading
            self._check_and_reload_config()

            # Update monitoring metrics
            self.monitoring.update_uptime(time.time() - self.start_time)
            
            # Cleanup rate limiter blacklist
            self.rate_limiter.cleanup_blacklist()
            
            time.sleep(self.config.get('heartbeat_interval', 10))
        
        logging.info('Daemon stopped.')

    def stop(self, signum=None, frame=None):
        logging.info('Received stop signal.')
        self.running = False
        # Stop service discovery agent
        self.service_discovery_agent.stop()
        # Stop Flask app if running
        if app:
            try:
                # For development server, we can't easily shut it down
                # In production, use a proper WSGI server like Gunicorn
                logging.info("Flask app shutdown initiated")
            except Exception as e:
                logging.error(f"Error shutting down Flask app: {e}")

class DuxNetDaemon(DuxOSDaemon):
    def __init__(self, config):
        super().__init__(config)
        self.listen_port = config.get('duxnet_port', 9333)
        self.server_socket = None
        self.tls_enabled = config.get('security', {}).get('tls_enabled', False)
        self.cert_path = config.get('security', {}).get('cert_path')
        self.key_path = config.get('security', {}).get('key_path')
        self.ssl_context = None

        self.health_check_enabled = config.get('monitoring', {}).get('enabled', False)
        self.health_check_port = config.get('monitoring', {}).get('health_check_port', 8080)
        self.health_server = None
        self.health_thread = None

        if self.tls_enabled:
            if not self.cert_path or not self.key_path:
                logging.error("TLS is enabled but cert_path or key_path is not specified in config.yaml")
                self.tls_enabled = False
            else:
                try:
                    self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    self.ssl_context.load_cert_chain(certfile=self.cert_path, keyfile=self.key_path)
                    logging.info("TLS context loaded successfully.")
                except Exception as e:
                    logging.error(f"Failed to load TLS certificates: {e}")
                    self.tls_enabled = False

    def run(self):
        logging.info(f'DuxNetDaemon starting, listening on port {self.listen_port}' +
                     (' with TLS enabled.' if self.tls_enabled else '.'))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.listen_port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(2)

        if self.tls_enabled and self.ssl_context:
            try:
                self.server_socket = self.ssl_context.wrap_socket(self.server_socket, server_side=True)
                logging.info("Server socket wrapped with TLS.")
            except ssl.SSLError as e:
                logging.error(f"Failed to wrap socket with TLS: {e}")
                self.running = False
                return

        if self.health_check_enabled:
            try:
                self.health_server = HTTPServer(('0.0.0.0', self.health_check_port), HealthCheckHandler)
                self.health_server.start_time = self.start_time
                self.health_thread = threading.Thread(target=self.health_server.serve_forever)
                self.health_thread.daemon = True
                self.health_thread.start()
                logging.info(f"Health check endpoint enabled on port {self.health_check_port}/healthz")
            except Exception as e:
                logging.error(f"Failed to start health check server: {e}")
                self.health_check_enabled = False

        # Start service discovery
        self.service_discovery_agent.start()

        try:
            while self.running:
                current_time = time.time()
                
                # Check rate limiting
                if not self.rate_limiter.is_allowed("global"):
                    logging.warning("Global rate limit exceeded. Skipping connection acceptance.")
                    time.sleep(0.1)
                    continue

                try:
                    client_sock, addr = self.server_socket.accept()
                    
                    # Check rate limiting for specific IP
                    if not self.rate_limiter.is_allowed(addr[0]):
                        logging.warning(f"Rate limit exceeded for {addr[0]}. Rejecting connection.")
                        client_sock.close()
                        continue

                    self.monitoring.record_connection(True)

                    if self.tls_enabled:
                        try:
                            client_sock = self.ssl_context.wrap_socket(client_sock, server_side=True)
                            logging.info(f'Accepted TLS connection from {addr}')
                        except ssl.SSLError as e:
                            logging.warning(f"TLS handshake failed with {addr}: {e}")
                            client_sock.close()
                            self.monitoring.record_connection(False)
                            continue
                    else:
                        logging.info(f'Accepted connection from {addr}')

                    client_sock.sendall(b"Welcome to DuxNet!\n")
                    client_sock.close()
                    self.monitoring.record_connection(False)
                    
                except socket.timeout:
                    continue
                except ssl.SSLError as e:
                    logging.warning(f"SSL error during connection: {e}")
                except Exception as e:
                    logging.error(f"Error handling client connection: {e}")
                    self.monitoring.record_connection(False)
        finally:
            if self.server_socket:
                self.server_socket.close()
            if self.health_server:
                self.health_server.shutdown()
                self.health_server.server_close()
                logging.info("Health check server shut down.")
            logging.info('DuxNetDaemon stopped.')

def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(log_path):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

def write_pid(pid_path):
    with open(pid_path, 'w') as f:
        f.write(str(os.getpid()))

def read_pid(pid_path):
    try:
        with open(pid_path, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return None

def remove_pid(pid_path):
    try:
        os.remove(pid_path)
    except FileNotFoundError:
        pass

def start_daemon():
    config = load_config(CONFIG_PATH)
    setup_logging(LOG_PATH)
    daemon = DuxOSDaemon(config)
    write_pid(PID_PATH)
    signal.signal(signal.SIGTERM, daemon.stop)
    signal.signal(signal.SIGINT, daemon.stop)
    try:
        daemon.run()
    finally:
        remove_pid(PID_PATH)

def stop_daemon():
    pid = read_pid(PID_PATH)
    if pid:
        os.kill(pid, signal.SIGTERM)
        print(f"Stopped daemon (PID {pid})")
    else:
        print("No running daemon found.")

def status_daemon():
    pid = read_pid(PID_PATH)
    if pid and os.path.exists(f"/proc/{pid}"):
        print(f"Daemon is running (PID {pid})")
    else:
        print("Daemon is not running.")

def main():
    parser = argparse.ArgumentParser(description='Dux OS Daemon Template')
    parser.add_argument('command', choices=['start', 'stop', 'status'])
    args = parser.parse_args()

    if args.command == 'start':
        if read_pid(PID_PATH):
            print('Daemon already running.')
            sys.exit(1)
        pid = os.fork()
        if pid > 0:
            # Parent process
            sys.exit(0)
        # Child process
        os.setsid()
        start_daemon()
    elif args.command == 'stop':
        stop_daemon()
    elif args.command == 'status':
        status_daemon()

if __name__ == '__main__':
    main() 