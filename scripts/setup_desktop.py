#!/usr/bin/env python3
"""
Setup script for DuxOS Desktop infrastructure components
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

def run_command(command, check=True, capture_output=False):
    """Run a shell command"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command '{command}': {e}")
        return None

def install_system_dependencies():
    """Install system-level dependencies"""
    system = platform.system().lower()
    
    if system == "linux":
        # Ubuntu/Debian
        if os.path.exists("/etc/debian_version"):
            packages = [
                "redis-server",
                "python3-pip",
                "python3-venv",
                "build-essential",
                "python3-dev"
            ]
            run_command(f"sudo apt-get update")
            run_command(f"sudo apt-get install -y {' '.join(packages)}")
        
        # Start Redis service
        run_command("sudo systemctl enable redis-server")
        run_command("sudo systemctl start redis-server")
        
    elif system == "darwin":  # macOS
        # Install via Homebrew
        run_command("brew install redis")
        run_command("brew services start redis")
    
    else:
        print(f"Unsupported operating system: {system}")
        print("Please install Redis manually")
        return False
    
    return True

def setup_python_environment():
    """Setup Python virtual environment and install dependencies"""
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        run_command("python3 -m venv venv")
    
    # Activate virtual environment and install dependencies
    pip_cmd = "venv/bin/pip" if os.name != "nt" else "venv\\Scripts\\pip"
    
    print("Installing Python dependencies...")
    run_command(f"{pip_cmd} install --upgrade pip")
    run_command(f"{pip_cmd} install -r requirements_desktop.txt")
    
    return True

def setup_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data",
        "certs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def setup_configuration():
    """Setup configuration files"""
    # Copy daemon config if it doesn't exist
    if not os.path.exists("duxos_daemon_template/config.yaml"):
        print("Warning: daemon config not found")
    else:
        print("Daemon configuration ready")

def test_infrastructure():
    """Test the infrastructure components"""
    print("Testing infrastructure components...")
    
    # Test Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Test Prometheus client
    try:
        import prometheus_client
        print("✅ Prometheus client available")
    except Exception as e:
        print(f"❌ Prometheus client failed: {e}")
        return False
    
    # Test Flask
    try:
        import flask
        print("✅ Flask available")
    except Exception as e:
        print(f"❌ Flask failed: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Setup DuxOS Desktop infrastructure")
    parser.add_argument("--skip-system", action="store_true", help="Skip system dependency installation")
    parser.add_argument("--skip-python", action="store_true", help="Skip Python environment setup")
    parser.add_argument("--test-only", action="store_true", help="Only run infrastructure tests")
    
    args = parser.parse_args()
    
    print("🚀 DuxOS Desktop Infrastructure Setup")
    print("=" * 50)
    
    if args.test_only:
        success = test_infrastructure()
        sys.exit(0 if success else 1)
    
    # Install system dependencies
    if not args.skip_system:
        print("\n📦 Installing system dependencies...")
        if not install_system_dependencies():
            print("Failed to install system dependencies")
            sys.exit(1)
    
    # Setup Python environment
    if not args.skip_python:
        print("\n🐍 Setting up Python environment...")
        if not setup_python_environment():
            print("Failed to setup Python environment")
            sys.exit(1)
    
    # Setup directories
    print("\n📁 Creating directories...")
    setup_directories()
    
    # Setup configuration
    print("\n⚙️  Setting up configuration...")
    setup_configuration()
    
    # Test infrastructure
    print("\n🧪 Testing infrastructure...")
    if test_infrastructure():
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the daemon: python duxos_daemon_template/daemon.py start")
        print("2. Check health: curl http://localhost:8080/healthz")
        print("3. View metrics: curl http://localhost:9090/metrics")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 