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

CONFIG_PATH = os.environ.get('DUXOS_DAEMON_CONFIG', 'config.yaml')
LOG_PATH = os.environ.get('DUXOS_DAEMON_LOG', 'daemon.log')
PID_PATH = os.environ.get('DUXOS_DAEMON_PID', 'daemon.pid')

# Global Flask app instance (to be initialized by DuxOSDaemon)
app = None

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/healthz':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

class ServiceDiscoveryAgent:
    def __init__(self, config, daemon_id):
        self.config = config
        self.daemon_id = daemon_id
        self.enabled = config.get('service_discovery', {}).get('enabled', False)
        self.broadcast_port = config.get('service_discovery', {}).get('broadcast_port', 9334)
        self.broadcast_interval = config.get('service_discovery', {}).get('broadcast_interval', 15)
        self.service_type = config.get('service_discovery', {}).get('service_type', 'duxos-daemon')

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
            'type': 'duxos_discovery',
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

                if message.get('type') == 'duxos_discovery' and message.get('daemon_id') != self.daemon_id:
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
        self.running = True

        # Configuration hot-reloading properties
        self.config_path = CONFIG_PATH
        self.last_config_mod_time = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0

        global app
        app = Flask(__name__)
        self.api_port = self.config.get('api_server', {}).get('port', 5000)
        self.api_enabled = self.config.get('api_server', {}).get('enabled', False)
        self.api_server_thread = None

        # Service Discovery Integration
        self.daemon_id = socket.gethostname() + "_" + str(os.getpid())
        self.service_discovery_agent = ServiceDiscoveryAgent(self.config, self.daemon_id)

        # Define API endpoints using the global app instance
        @app.route('/api/v1/status', methods=['GET'])
        def get_status():
            return jsonify({"status": "running", "timestamp": time.time(), "daemon_id": self.daemon_id})

        @app.route('/api/v1/config', methods=['GET'])
        def get_daemon_config():
            sanitized_config = self.config.copy()
            # Remove sensitive information before exposing
            if 'security' in sanitized_config:
                sanitized_config['security'].pop('key_path', None)
                for key in sanitized_config.keys():
                    if isinstance(sanitized_config[key], dict) and 'password' in sanitized_config[key]:
                        sanitized_config[key]['password'] = '********'
            return jsonify(sanitized_config)

        @app.route('/api/v1/heartbeat_interval', methods=['GET'])
        def get_heartbeat_interval():
            return jsonify({"heartbeat_interval": self.config.get('heartbeat_interval', 10)})

        @app.route('/api/v1/peers', methods=['GET'])
        def get_known_peers():
            # Clean up old peers before returning
            cutoff_time = time.time() - (self.service_discovery_agent.broadcast_interval * 2)
            active_peers = {
                pid: info for pid, info in self.service_discovery_agent.known_peers.items()
                if info['last_seen'] > cutoff_time
            }
            self.service_discovery_agent.known_peers = active_peers
            return jsonify({"peers": active_peers})

    def run(self):
        logging.info('Daemon started.')
        # Start API server in a separate thread
        if self.api_enabled:
            try:
                self.api_server_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=self.api_port, debug=False, use_reloader=False))
                self.api_server_thread.daemon = True
                self.api_server_thread.start()
                logging.info(f"REST API server enabled on port {self.api_port}/api/v1/status, /api/v1/config, /api/v1/heartbeat_interval, /api/v1/peers")
            except Exception as e:
                logging.error(f"Failed to start REST API server: {e}")
                self.api_enabled = False

        # Start service discovery agent
        self.service_discovery_agent.start()

        while self.running:
            # --- Main daemon logic goes here ---
            logging.info('Daemon heartbeat...')

            # Implement configuration hot-reloading
            self._check_and_reload_config()

            # TODO: Add metrics and monitoring hooks (e.g., Prometheus, custom logs)
            time.sleep(self.config.get('heartbeat_interval', 10))
        logging.info('Daemon stopped.')

    def stop(self, signum=None, frame=None):
        logging.info('Received stop signal.')
        self.running = False
        # Stop service discovery agent
        self.service_discovery_agent.stop()
        # ... existing shutdown logic for other components ...
        # Flask's development server doesn't have a direct shutdown method in this context for thread.
        # It relies on the daemon thread exiting when the main program does.
        # For production, a proper WSGI server (like Gunicorn) would be used with graceful shutdown.
        # However, for this template, setting self.running = False will eventually stop the main loop.
        # A more robust shutdown mechanism for the Flask thread is beyond the scope of this template.
        if self.health_server:
            self.health_server.shutdown()
            self.health_server.server_close()
            logging.info("Health check server shut down.")

class DuxNetDaemon(DuxOSDaemon):
    def __init__(self, config):
        super().__init__(config)
        self.listen_port = config.get('duxnet_port', 9333)
        self.server_socket = None
        self.tls_enabled = config.get('security', {}).get('tls_enabled', False)
        self.cert_path = config.get('security', {}).get('cert_path')
        self.key_path = config.get('security', {}).get('key_path')
        self.ssl_context = None

        self.rate_limit_per_minute = config.get('security', {}).get('rate_limit_per_minute', 60)
        self.connection_timestamps = []
        self.rate_limit_window_seconds = 60

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
                self.health_thread = threading.Thread(target=self.health_server.serve_forever)
                self.health_thread.daemon = True
                self.health_thread.start()
                logging.info(f"Health check endpoint enabled on port {self.health_check_port}/healthz")
            except Exception as e:
                logging.error(f"Failed to start health check server: {e}")
                self.health_check_enabled = False

        try:
            while self.running:
                current_time = time.time()
                self.connection_timestamps = [ts for ts in self.connection_timestamps if ts > current_time - self.rate_limit_window_seconds]

                if len(self.connection_timestamps) >= self.rate_limit_per_minute:
                    logging.warning(f"Rate limit exceeded ({self.rate_limit_per_minute} connections/{self.rate_limit_window_seconds}s). Rejecting new connection.")
                    time.sleep(0.1)
                    continue

                try:
                    client_sock, addr = self.server_socket.accept()
                    self.connection_timestamps.append(current_time)

                    if self.tls_enabled:
                        try:
                            client_sock = self.ssl_context.wrap_socket(client_sock, server_side=True)
                            logging.info(f'Accepted TLS connection from {addr}')
                        except ssl.SSLError as e:
                            logging.warning(f"TLS handshake failed with {addr}: {e}")
                            client_sock.close()
                            continue
                    else:
                        logging.info(f'Accepted connection from {addr}')

                    client_sock.sendall(b"Welcome to DuxNet!\n")
                    client_sock.close()
                except socket.timeout:
                    continue
                except ssl.SSLError as e:
                    logging.warning(f"SSL error during connection: {e}")
                except Exception as e:
                    logging.error(f"Error handling client connection: {e}")
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