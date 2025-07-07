# DuxNet

DuxNet is a modular, decentralized application platform with a Python GUI and CLI, supporting distributed computing, payments, and a decentralized app store. This repository contains the core DuxNet application, including the desktop GUI, wallet, store, daemon, and registry modules.

## Directory Structure

- `duxnet_desktop/` — PyQt-based desktop GUI for browsing, installing, and managing DuxNet apps and APIs
- `duxnet_wallet/` — Flop Coin wallet integration (Python, JSON-RPC)
- `duxnet_store/` — Decentralized app/API store backend and logic
- `duxnet_daemon_template/` — Daemon framework for network, escrow, airdrop, etc.
- `duxnet_registry/` — Node registry CLI and services
- `duxnet_wallet_cli/` — CLI wallet tools

## Installation

### Prerequisites
- Python 3.8+
- pip
- Flopcoin Core daemon (for wallet functionality)

### Setup
```bash
# Clone the repository
 git clone https://github.com/ducks-github/DuxNet.git
 cd DuxNet

# Install all Python dependencies
 pip install -r requirements.txt
```

## Running the Application

### Desktop GUI
```bash
python duxnet_desktop/desktop_manager.py
```

### Wallet CLI
```bash
python duxnet_wallet_cli/cli.py [new-address|balance|send] [options]
```

### Store Backend
```bash
python duxnet_store/main.py
```

### Daemon Example
```bash
python duxnet_daemon_template/daemon.py start
```

### Registry CLI
```bash
python duxnet_registry/cli.py [register|list|update|deregister] [options]
```

## Configuration
- Wallet: Edit `duxnet_wallet/config.yaml` with your Flopcoin RPC credentials.
- Store: Edit `duxnet_store/config.yaml` for store settings.
- Daemon: Edit `duxnet_daemon_template/config.yaml` for daemon settings.

## Modular Structure
- **Desktop GUI:** User interface for app store, wallet, and account management.
- **Wallet:** Handles Flop Coin transactions, balance, and address management.
- **Store:** Decentralized API/app store logic and metadata.
- **Daemon:** Framework for network, escrow, and airdrop services.
- **Registry:** Node management and health tracking.

## Contributing
Pull requests are welcome! Please see module READMEs for details on each component.

## License
MIT
