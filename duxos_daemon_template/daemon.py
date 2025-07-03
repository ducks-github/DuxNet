#!/usr/bin/env python3
import argparse
import logging
import os
import signal
import sys
import time
import yaml
import socket

CONFIG_PATH = os.environ.get('DUXOS_DAEMON_CONFIG', 'config.yaml')
LOG_PATH = os.environ.get('DUXOS_DAEMON_LOG', 'daemon.log')
PID_PATH = os.environ.get('DUXOS_DAEMON_PID', 'daemon.pid')

class DuxOSDaemon:
    def __init__(self, config):
        self.config = config
        self.running = True

    def run(self):
        logging.info('Daemon started.')
        while self.running:
            # --- Main daemon logic goes here ---
            logging.info('Daemon heartbeat...')
            time.sleep(self.config.get('heartbeat_interval', 10))
        logging.info('Daemon stopped.')

    def stop(self, signum=None, frame=None):
        logging.info('Received stop signal.')
        self.running = False

class DuxNetDaemon(DuxOSDaemon):
    def __init__(self, config):
        super().__init__(config)
        self.listen_port = config.get('duxnet_port', 9333)  # Default port 9333 (like Bitcoin)
        self.server_socket = None

    def run(self):
        logging.info(f'DuxNetDaemon starting, listening on port {self.listen_port}')
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.listen_port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(2)
        try:
            while self.running:
                try:
                    client_sock, addr = self.server_socket.accept()
                    logging.info(f'Accepted connection from {addr}')
                    client_sock.sendall(b"Welcome to DuxNet!\n")
                    client_sock.close()
                except socket.timeout:
                    continue
        finally:
            if self.server_socket:
                self.server_socket.close()
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