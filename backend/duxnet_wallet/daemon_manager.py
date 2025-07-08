#!/usr/bin/env python3
"""
Daemon Manager for DuxNet
Manages multiple cryptocurrency daemons and their configurations
"""

import logging
import os
import subprocess
import time
import json
import requests
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DaemonStatus(Enum):
    """Daemon status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    SYNCING = "syncing"


@dataclass
class DaemonConfig:
    """Configuration for a cryptocurrency daemon"""
    name: str
    currency: str
    daemon_path: str
    config_path: str
    data_dir: str
    rpc_port: int
    rpc_user: str
    rpc_password: str
    network: str  # mainnet, testnet, devnet
    enabled: bool = True
    auto_start: bool = False
    sync_mode: str = "full"  # full, light, fast


class DaemonManager:
    """Manages multiple cryptocurrency daemons"""
    
    def __init__(self, config_path: str = "daemon_config.yaml"):
        self.config_path = config_path
        self.daemons: Dict[str, DaemonConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status: Dict[str, DaemonStatus] = {}
        self._load_config()
    
    def _load_config(self):
        """Load daemon configurations from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                for daemon_data in config_data.get('daemons', []):
                    try:
                        daemon = DaemonConfig(**daemon_data)
                        self.daemons[daemon.currency] = daemon
                        self.status[daemon.currency] = DaemonStatus.STOPPED
                    except Exception as e:
                        logger.error(f"Failed to load daemon config: {e}")
                        continue
                
                logger.info(f"Loaded {len(self.daemons)} daemon configurations")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load daemon config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default daemon configuration"""
        default_config = {
            'daemons': [
                {
                    'name': 'Bitcoin Core',
                    'currency': 'BTC',
                    'daemon_path': '/usr/local/bin/bitcoind',
                    'config_path': '/etc/bitcoin/bitcoin.conf',
                    'data_dir': '/var/lib/bitcoin',
                    'rpc_port': 8332,
                    'rpc_user': 'bitcoinrpc',
                    'rpc_password': 'your_password_here',
                    'network': 'testnet',
                    'enabled': True,
                    'auto_start': False,
                    'sync_mode': 'full'
                },
                {
                    'name': 'Ethereum Geth',
                    'currency': 'ETH',
                    'daemon_path': '/usr/local/bin/geth',
                    'config_path': '/etc/ethereum/geth.conf',
                    'data_dir': '/var/lib/ethereum',
                    'rpc_port': 8545,
                    'rpc_user': '',
                    'rpc_password': '',
                    'network': 'goerli',
                    'enabled': True,
                    'auto_start': False,
                    'sync_mode': 'light'
                },
                {
                    'name': 'Dogecoin Core',
                    'currency': 'DOGE',
                    'daemon_path': '/usr/local/bin/dogecoind',
                    'config_path': '/etc/dogecoin/dogecoin.conf',
                    'data_dir': '/var/lib/dogecoin',
                    'rpc_port': 22555,
                    'rpc_user': 'dogecoinrpc',
                    'rpc_password': 'your_password_here',
                    'network': 'testnet',
                    'enabled': False,
                    'auto_start': False,
                    'sync_mode': 'full'
                }
            ]
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default config file: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
    
    def start_daemon(self, currency: str) -> bool:
        """Start a cryptocurrency daemon"""
        if currency not in self.daemons:
            logger.error(f"Daemon not configured for currency: {currency}")
            return False
        
        daemon = self.daemons[currency]
        if not daemon.enabled:
            logger.warning(f"Daemon disabled for currency: {currency}")
            return False
        
        try:
            # Check if daemon is already running
            if self.is_daemon_running(currency):
                logger.info(f"Daemon already running for {currency}")
                self.status[currency] = DaemonStatus.RUNNING
                return True
            
            # Create data directory if it doesn't exist
            os.makedirs(daemon.data_dir, exist_ok=True)
            
            # Build daemon command
            cmd = self._build_daemon_command(daemon)
            
            # Start daemon process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=daemon.data_dir
            )
            
            self.processes[currency] = process
            self.status[currency] = DaemonStatus.STARTING
            
            logger.info(f"Started {currency} daemon (PID: {process.pid})")
            
            # Wait for daemon to start
            time.sleep(5)
            
            # Check if daemon is responding
            if self._check_daemon_health(currency):
                self.status[currency] = DaemonStatus.RUNNING
                logger.info(f"{currency} daemon is running and healthy")
                return True
            else:
                self.status[currency] = DaemonStatus.ERROR
                logger.error(f"{currency} daemon failed to start properly")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {currency} daemon: {e}")
            self.status[currency] = DaemonStatus.ERROR
            return False
    
    def stop_daemon(self, currency: str) -> bool:
        """Stop a cryptocurrency daemon"""
        if currency not in self.processes:
            logger.warning(f"No running process for {currency}")
            return True
        
        try:
            process = self.processes[currency]
            
            # Send SIGTERM
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                process.kill()
                process.wait()
            
            del self.processes[currency]
            self.status[currency] = DaemonStatus.STOPPED
            
            logger.info(f"Stopped {currency} daemon")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {currency} daemon: {e}")
            return False
    
    def restart_daemon(self, currency: str) -> bool:
        """Restart a cryptocurrency daemon"""
        logger.info(f"Restarting {currency} daemon")
        self.stop_daemon(currency)
        time.sleep(2)
        return self.start_daemon(currency)
    
    def is_daemon_running(self, currency: str) -> bool:
        """Check if a daemon is running"""
        if currency not in self.processes:
            return False
        
        process = self.processes[currency]
        return process.poll() is None
    
    def get_daemon_status(self, currency: str) -> DaemonStatus:
        """Get the status of a daemon"""
        if currency not in self.status:
            return DaemonStatus.STOPPED
        
        # Update status based on process state
        if currency in self.processes:
            process = self.processes[currency]
            if process.poll() is not None:
                self.status[currency] = DaemonStatus.ERROR
        
        return self.status[currency]
    
    def get_all_status(self) -> Dict[str, DaemonStatus]:
        """Get status of all daemons"""
        return {currency: self.get_daemon_status(currency) for currency in self.daemons.keys()}
    
    def _build_daemon_command(self, daemon: DaemonConfig) -> List[str]:
        """Build the command to start a daemon"""
        if daemon.currency == 'BTC':
            return [
                daemon.daemon_path,
                f'-datadir={daemon.data_dir}',
                f'-rpcport={daemon.rpc_port}',
                f'-rpcuser={daemon.rpc_user}',
                f'-rpcpassword={daemon.rpc_password}',
                '-daemon',
                '-server',
                '-rpcallowip=127.0.0.1'
            ] + (['-testnet'] if daemon.network == 'testnet' else [])
        
        elif daemon.currency == 'ETH':
            return [
                daemon.daemon_path,
                f'--datadir={daemon.data_dir}',
                f'--http.port={daemon.rpc_port}',
                '--http',
                '--http.addr=127.0.0.1',
                '--http.corsdomain=*',
                '--http.api=eth,net,web3,personal',
                '--allow-insecure-unlock'
            ] + (['--goerli'] if daemon.network == 'goerli' else [])
        
        elif daemon.currency == 'DOGE':
            return [
                daemon.daemon_path,
                f'-datadir={daemon.data_dir}',
                f'-rpcport={daemon.rpc_port}',
                f'-rpcuser={daemon.rpc_user}',
                f'-rpcpassword={daemon.rpc_password}',
                '-daemon',
                '-server',
                '-rpcallowip=127.0.0.1'
            ] + (['-testnet'] if daemon.network == 'testnet' else [])
        
        else:
            # Generic command for other daemons
            return [daemon.daemon_path]
    
    def _check_daemon_health(self, currency: str) -> bool:
        """Check if a daemon is healthy and responding"""
        if currency not in self.daemons:
            return False
        
        daemon = self.daemons[currency]
        
        try:
            if daemon.currency == 'BTC':
                return self._check_bitcoin_health(daemon)
            elif daemon.currency == 'ETH':
                return self._check_ethereum_health(daemon)
            elif daemon.currency == 'DOGE':
                return self._check_dogecoin_health(daemon)
            else:
                return self._check_generic_health(daemon)
        except Exception as e:
            logger.error(f"Health check failed for {currency}: {e}")
            return False
    
    def _check_bitcoin_health(self, daemon: DaemonConfig) -> bool:
        """Check Bitcoin daemon health"""
        try:
            response = requests.post(
                f'http://127.0.0.1:{daemon.rpc_port}',
                json={
                    'jsonrpc': '1.0',
                    'id': 'health_check',
                    'method': 'getblockchaininfo',
                    'params': []
                },
                auth=(daemon.rpc_user, daemon.rpc_password),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_ethereum_health(self, daemon: DaemonConfig) -> bool:
        """Check Ethereum daemon health"""
        try:
            response = requests.post(
                f'http://127.0.0.1:{daemon.rpc_port}',
                json={
                    'jsonrpc': '2.0',
                    'id': 'health_check',
                    'method': 'eth_blockNumber',
                    'params': []
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_dogecoin_health(self, daemon: DaemonConfig) -> bool:
        """Check Dogecoin daemon health"""
        try:
            response = requests.post(
                f'http://127.0.0.1:{daemon.rpc_port}',
                json={
                    'jsonrpc': '1.0',
                    'id': 'health_check',
                    'method': 'getblockchaininfo',
                    'params': []
                },
                auth=(daemon.rpc_user, daemon.rpc_password),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_generic_health(self, daemon: DaemonConfig) -> bool:
        """Generic health check for other daemons"""
        try:
            # Try to connect to the RPC port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', daemon.rpc_port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_daemon_info(self, currency: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a daemon"""
        if currency not in self.daemons:
            return None
        
        daemon = self.daemons[currency]
        status = self.get_daemon_status(currency)
        
        info = {
            'currency': currency,
            'name': daemon.name,
            'status': status.value,
            'network': daemon.network,
            'rpc_port': daemon.rpc_port,
            'data_dir': daemon.data_dir,
            'enabled': daemon.enabled,
            'auto_start': daemon.auto_start
        }
        
        if currency in self.processes:
            process = self.processes[currency]
            info['pid'] = process.pid
            info['running'] = process.poll() is None
        
        return info
    
    def start_all_enabled(self) -> Dict[str, bool]:
        """Start all enabled daemons"""
        results = {}
        for currency, daemon in self.daemons.items():
            if daemon.enabled and daemon.auto_start:
                results[currency] = self.start_daemon(currency)
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        """Stop all running daemons"""
        results = {}
        for currency in list(self.processes.keys()):
            results[currency] = self.stop_daemon(currency)
        return results


if __name__ == "__main__":
    # Example usage
    manager = DaemonManager()
    
    print("Daemon Manager initialized")
    print(f"Configured daemons: {list(manager.daemons.keys())}")
    
    # Get status of all daemons
    status = manager.get_all_status()
    for currency, status in status.items():
        print(f"{currency}: {status.value}")
    
    # Start Bitcoin daemon (if configured)
    if 'BTC' in manager.daemons:
        print("\nStarting Bitcoin daemon...")
        success = manager.start_daemon('BTC')
        print(f"Bitcoin daemon start: {'Success' if success else 'Failed'}")
    
    # Get detailed info
    for currency in manager.daemons.keys():
        info = manager.get_daemon_info(currency)
        if info:
            print(f"\n{currency} Info: {info}") 