# DuxNet

https://github.com/ducks-github/DuxNet/releases/tag/v2.3.0

DuxNet is a modular, decentralized application platform with a Python GUI and CLI, supporting distributed computing, payments, and a decentralized app store. This repository contains the core DuxNet application, including the desktop GUI, wallet, store, daemon, and registry modules.

## 🏗️ **New Organized Structure**

The codebase has been reorganized for better maintainability:

```
DuxNet/
├── backend/           # All backend services and APIs
│   ├── duxnet_store/  # Store service (API/App Store)
│   ├── duxos_escrow/  # Escrow service
│   ├── duxnet_wallet/ # Wallet service
│   └── ...           # Other backend modules
├── frontend/          # Desktop GUI and frontend code
│   ├── duxnet_desktop/
│   └── duxos_desktop/
├── shared/            # Shared utilities and constants
├── scripts/           # Setup, launcher, and utility scripts
├── docs/              # Documentation
└── tests/             # Test files
```

---

## 🚀 Multi-Cryptocurrency Wallet & Escrow Support

DuxNet now supports escrow and wallet operations for the top 10 cryptocurrencies (BTC, ETH, USDT, BNB, XRP, SOL, ADA, DOGE, TON, TRX) in addition to Flopcoin (FLOP).

- **MultiCryptoWallet**: Unified wallet interface for multiple cryptocurrencies.
- **Multi-Crypto Escrow**: Escrow contracts can be created, funded, and released in any supported currency.
- **Mock Wallets**: For development, mock wallets are used if real crypto libraries are not installed.
- **Optional Dependencies**: To use real Bitcoin, Ethereum, or XRP wallets, install the optional dependencies listed in `backend/duxnet_wallet/requirements.txt`.

---

## 🚀 Quickstart

### **Prerequisites**
- Python 3.8+  
- pip (Python package manager)  
- Flopcoin Core daemon (required for Flopcoin wallet functionality)  
  - Download and run from: https://github.com/flopcoin/flopcoin-core
- (Optional) For real multi-crypto support:
  - `bitcoinlib`, `web3`, `eth-account`, `xrpl-py` (see `backend/duxnet_wallet/requirements.txt`)

### **Installation**
```bash
# Clone the repository
git clone https://github.com/ducks-github/DuxNet.git
cd DuxNet

# (Recommended) Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt
# (Optional) For real multi-crypto support:
pip install -r backend/duxnet_wallet/requirements.txt
```

### **Configuration**
- **Wallet:** Edit `backend/duxnet_wallet/config.yaml` with your Flopcoin RPC credentials.
- **Multi-Crypto Wallet:** Edit `backend/duxnet_wallet/multi_crypto_config.yaml` for multi-crypto settings.
- **Store:** Edit `backend/duxnet_store/config.yaml` for store settings.
- **Daemon:** Edit `scripts/duxnet_daemon_template/config.yaml` for daemon settings.

### **Running the Application**

#### **Option 1: All-in-One Launcher (Recommended)**
```bash
# Run all services and desktop GUI
python scripts/duxnet_launcher_cross_platform.py

# Or use the convenience scripts
./scripts/run_duxnet.sh      # Linux/Mac
scripts/run_duxnet.bat       # Windows
```

#### **Option 2: Individual Services**
```bash
# Desktop GUI
python -m frontend.duxnet_desktop.desktop_manager

# Store Backend
python -m backend.duxnet_store.main --config backend/duxnet_store/config.yaml

# Escrow Service
python -m backend.duxos_escrow.escrow_service

# Wallet CLI
python frontend/duxnet_wallet_cli/cli.py [new-address|balance|send] [options]

# Registry CLI
python -m backend.duxnet_registry.registry.cli [register|list|update|deregister] [options]
```

### **Flopcoin Core Setup**
- Download Flopcoin Core from [Flopcoin GitHub](https://github.com/flopcoin/flopcoin-core).
- Start the Flopcoin daemon:
  ```bash
  flopcoind -daemon
  ```
- Ensure your RPC credentials in `backend/duxnet_wallet/config.yaml` match your Flopcoin Core configuration.

### **Troubleshooting & Common Issues**
- **pip install error ("externally-managed-environment"):**  
  Use a virtual environment as shown above, or (not recommended) use `pip install --break-system-packages -r requirements.txt`.
- **Flopcoin wallet connection errors:**  
  - Make sure Flopcoin Core is running and RPC credentials are correct.
  - Check that the RPC port is open and not firewalled.
- **Missing dependencies:**  
  - Ensure you are using the correct Python version (`python3 --version`).
  - Run `pip install -r requirements.txt` inside your virtual environment.
  - For real multi-crypto support, run `pip install -r backend/duxnet_wallet/requirements.txt`.
- **Multi-crypto wallet/escrow not working:**
  - By default, mock wallets are used for development. For real crypto, install the optional dependencies.
- **Port conflicts:**  
  - If port 8000 is in use, use `--port 8001` or edit the config file.

### **IMPORTANT REMINDER**
**Every time you open a new terminal or restart your session, you need to activate the virtual environment again with:**
```bash
cd ~/DuxNet/DuxNet
source .venv/bin/activate
```

## 🛠️ Developer Experience

### **Quick Setup (Recommended)**
Use our automated setup script for a complete development environment:

```bash
# Clone and setup in one command
git clone https://github.com/ducks-github/DuxNet.git
cd DuxNet
./scripts/setup.sh

# For development with pre-commit hooks
./scripts/setup.sh --with-pre-commit
```

### **Docker Development**
Run the entire DuxNet stack with Docker Compose:

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Available Services:**
- **Store Service** - `http://localhost:8000`
- **Task Engine** - `http://localhost:8001`
- **Registry** - `http://localhost:8002`
- **Wallet** - `http://localhost:8003`
- **Escrow** - `http://localhost:8004`
- **Desktop GUI** - `http://localhost:8005`
- **Health Monitor** - `http://localhost:8006`

### **Development Commands**
Use the Makefile for common development tasks:

```bash
# Show all available commands
make help

# Install development dependencies
make install-dev

# Format code
make format

# Run linting
make lint

# Run tests
make test

# Start development server with hot reload
make dev-store
```

### **Code Quality**
Pre-commit hooks automatically ensure code quality:

```bash
# Install pre-commit hooks
make pre-commit

# Run manually
pre-commit run --all-files
```

**Hooks include:**
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **bandit** - Security checks
- **yamllint** - YAML validation

## 🏗️ Architecture Overview

DuxNet follows a modular, decentralized architecture with clear separation of concerns. Each module operates independently while communicating through well-defined interfaces.

### **Backend Services**
- **Store Service** (`backend/duxnet_store/`): API/App Store with service registration, search, and reviews
- **Escrow Service** (`backend/duxos_escrow/`): Multi-crypto escrow contract management
- **Wallet Service** (`backend/duxnet_wallet/`): Multi-crypto wallet operations
- **Registry Service** (`backend/duxnet_registry/`): Node registration and discovery
- **Task Engine** (`backend/duxos_tasks/`): Distributed computing task management

### **Frontend Applications**
- **Desktop GUI** (`frontend/duxnet_desktop/`): PyQt5-based desktop application
- **Wallet CLI** (`frontend/duxnet_wallet_cli/`): Command-line wallet interface

### **Shared Components**
- **Models** (`backend/*/models/`): Data models and schemas
- **API Routes** (`backend/*/api/`): REST API endpoints
- **Services** (`backend/*/services/`): Business logic layer

## 📚 Documentation

- **Build Guide**: `docs/BUILD_GUIDE.md`
- **Implementation Summary**: `docs/IMPLEMENTATION_SUMMARY.md`
- **Multi-Crypto Integration**: `docs/MULTI_CRYPTO_ESCROW_INTEGRATION.md`
- **Executable Guide**: `docs/README_DUXNET_EXE.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/ducks-github/DuxNet/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ducks-github/DuxNet/discussions)
- **Documentation**: Check the `docs/` directory for detailed guides

---

**DuxNet** - Building the future of decentralized applications! 🚀 
