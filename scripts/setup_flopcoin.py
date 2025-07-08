#!/usr/bin/env python3
"""
Flopcoin Setup Script

This script helps set up and configure Flopcoin Core for integration
with the DuxOS Node Registry wallet system.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests


class FlopcoinSetup:
    flopcoin_dir: Path
    config_file: Path
    wallet_file: Path
    pid_file: Path

    def __init__(self) -> None:
        self.flopcoin_dir = Path.home() / ".flopcoin"
        self.config_file = self.flopcoin_dir / "flopcoin.conf"
        self.wallet_file = self.flopcoin_dir / "wallet.dat"
        self.pid_file = self.flopcoin_dir / "flopcoind.pid"

    def create_config(self, rpc_password: str) -> bool:
        """Create Flopcoin configuration file"""
        config_content: str = f"""# Flopcoin Core Configuration for DuxOS Integration

# RPC Configuration
server=1
rpcuser=flopcoinrpc
rpcpassword={rpc_password}
rpcallowip=127.0.0.1
rpcport=32553

# Network Configuration
listen=1
port=32552
maxconnections=125

# Wallet Configuration
wallet=wallet.dat
walletnotify=echo "Wallet transaction: %s"

# Logging
debug=rpc
logtimestamps=1

# Security
txindex=1
addressindex=1
timestampindex=1
spentindex=1

# Performance
dbcache=450
maxorphantx=10
maxmempool=50

# Flopcoin-specific settings
# Block time: 60 seconds
# Algorithm: Scrypt
# Address prefix: F
"""

        # Create directory if it doesn't exist
        self.flopcoin_dir.mkdir(exist_ok=True)

        # Write config file
        with open(self.config_file, "w") as f:
            f.write(config_content)

        print(f"✅ Flopcoin configuration created at {self.config_file}")
        return True

    def check_flopcoin_installation(self) -> bool:
        """Check if Flopcoin Core is installed"""
        try:
            # Try to run flopcoind
            result = subprocess.run(
                ["flopcoind", "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("✅ Flopcoin Core is installed")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        print("❌ Flopcoin Core not found. Please install it first.")
        print("   Download from: https://github.com/Flopcoin/Flopcoin/releases")
        return False

    def stop_existing_daemon(self) -> None:
        """Stop any existing Flopcoin daemon"""
        try:
            # Try to stop using flopcoin-cli
            subprocess.run(["flopcoin-cli", "stop"], capture_output=True, timeout=10)
            print("🔄 Stopping existing Flopcoin daemon...")
            time.sleep(3)
        except:
            pass

        # Kill by PID if exists
        if self.pid_file.exists():
            try:
                with open(self.pid_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"🔄 Killed Flopcoin daemon (PID: {pid})")
                time.sleep(2)
            except:
                pass

    def start_flopcoin_daemon(self) -> bool:
        """Start Flopcoin daemon"""
        try:
            # Stop any existing daemon
            self.stop_existing_daemon()

            # Check if already running
            if self.is_flopcoin_running():
                print("✅ Flopcoin daemon is already running")
                return True

            # Start daemon
            subprocess.Popen(
                ["flopcoind", "-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            print("🔄 Starting Flopcoin daemon...")
            time.sleep(5)

            # Wait for RPC to be available
            for i in range(30):
                if self.is_flopcoin_running():
                    print("✅ Flopcoin daemon started successfully")
                    return True
                print(f"   Waiting for daemon to start... ({i+1}/30)")
                time.sleep(2)

            print("❌ Failed to start Flopcoin daemon")
            return False

        except Exception as e:
            print(f"❌ Error starting Flopcoin daemon: {e}")
            return False

    def is_flopcoin_running(self) -> bool:
        """Check if Flopcoin daemon is running"""
        try:
            # Try to connect to RPC
            response = requests.post(
                "http://127.0.0.1:32553",
                json={"method": "getnetworkinfo", "params": [], "jsonrpc": "2.0", "id": 1},
                auth=("flopcoinrpc", "test"),
                timeout=5,
            )
            return bool(response.status_code == 200)
        except:
            return False

    def test_rpc_connection(self, rpc_password: str) -> bool:
        """Test RPC connection"""
        try:
            response = requests.post(
                "http://127.0.0.1:32553",
                json={"method": "getnetworkinfo", "params": [], "jsonrpc": "2.0", "id": 1},
                auth=("flopcoinrpc", rpc_password),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    print("✅ RPC connection successful")
                    return True

            print("❌ RPC connection failed")
            return False

        except Exception as e:
            print(f"❌ RPC connection error: {e}")
            return False

    def get_sync_status(self, rpc_password: str) -> bool:
        """Get sync status"""
        try:
            response = requests.post(
                "http://127.0.0.1:32553",
                json={"method": "getblockchaininfo", "params": [], "jsonrpc": "2.0", "id": 1},
                auth=("flopcoinrpc", rpc_password),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    result = data["result"]
                    blocks = result.get("blocks", 0)
                    headers = result.get("headers", 0)
                    progress = result.get("verificationprogress", 0)

                    print(f"📊 Sync Status:")
                    print(f"   Blocks: {blocks}")
                    print(f"   Headers: {headers}")
                    print(f"   Progress: {progress:.2%}")

                    if progress >= 0.9999:
                        print("✅ Blockchain is fully synced")
                        return True
                    else:
                        print("🔄 Blockchain is still syncing...")
                        return False

            return False

        except Exception as e:
            print(f"❌ Error getting sync status: {e}")
            return False

    def get_network_info(self, rpc_password: str) -> bool:
        """Get network information"""
        try:
            response = requests.post(
                "http://127.0.0.1:32553",
                json={"method": "getnetworkinfo", "params": [], "jsonrpc": "2.0", "id": 1},
                auth=("flopcoinrpc", rpc_password),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    result = data["result"]
                    connections = result.get("connections", 0)
                    version = result.get("subversion", "Unknown")

                    print(f"🌐 Network Info:")
                    print(f"   Version: {version}")
                    print(f"   Connections: {connections}")
                    return True

            return False

        except Exception as e:
            print(f"❌ Error getting network info: {e}")
            return False


def main() -> None:
    print("🚀 Flopcoin Setup for DuxOS Integration")
    print("=" * 50)

    setup = FlopcoinSetup()

    # Check installation
    if not setup.check_flopcoin_installation():
        return

    # Get RPC password
    rpc_password: str = input("Enter RPC password for Flopcoin Core: ").strip()
    if not rpc_password:
        print("❌ RPC password is required")
        return

    # Create configuration
    print("\n📝 Creating Flopcoin configuration...")
    setup.create_config(rpc_password)

    # Start daemon
    print("\n🔄 Starting Flopcoin daemon...")
    if not setup.start_flopcoin_daemon():
        return

    # Test RPC connection
    print("\n🔗 Testing RPC connection...")
    if not setup.test_rpc_connection(rpc_password):
        return

    # Get network info
    print("\n🌐 Getting network information...")
    setup.get_network_info(rpc_password)

    # Check sync status
    print("\n📊 Checking blockchain sync status...")
    setup.get_sync_status(rpc_password)

    print("\n✅ Flopcoin setup complete!")
    print("\nNext steps:")
    print("1. Wait for blockchain to fully sync (this may take several hours)")
    print("2. Update your wallet config with the RPC password")
    print("3. Test the integration with the wallet CLI")
    print(f"\nRPC Configuration:")
    print(f"   Host: 127.0.0.1")
    print(f"   Port: 32553")
    print(f"   User: flopcoinrpc")
    print(f"   Password: {rpc_password}")


if __name__ == "__main__":
    main()
