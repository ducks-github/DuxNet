# Dux_OS
🐧 Dux OS is a decentralized, Debian-based Linux distribution for collaborative computing. Nodes share real-world computational tasks and monetize API/app usage using Flop Coin — a built-in digital currency.

## 🏗️ Modular Architecture

Dux_OS is built on a modular architecture that enables distributed computing, secure payments, and decentralized services. Each module operates independently but integrates seamlessly through standardized interfaces.

### Current Modules

#### 🔧 **Build System** (`build_script/`)
- **Purpose**: Creates custom Debian-based live ISOs with Dux_OS branding
- **Components**: 
  - `build_duxos.sh` - Main build script for creating bootable ISOs
  - `Dockerfile` - Containerized build environment
  - `duxos.png` - Branding assets
- **Interfaces**: Command-line build process, generates bootable ISO files

#### 💰 **Wallet System** (`duxos_wallet/`)
- **Purpose**: Manages Flop Coin transactions and wallet operations
- **Components**:
  - `wallet.py` - Python interface to Flopcoin Core via JSON-RPC
  - `config.yaml` - Wallet configuration and RPC settings
- **Interfaces**: JSON-RPC API, local wallet management, transaction signing
- **Dependencies**: Flopcoin Core daemon, network connectivity

#### 🔄 **Daemon Framework** (`duxos_daemon_template/`)
- **Purpose**: Template for creating system daemons (escrow, airdrop, etc.)
- **Components**:
  - `daemon.py` - Base daemon class with lifecycle management
  - `config.yaml` - Daemon configuration template
  - `duxos-daemon.service` - systemd service template
- **Interfaces**: systemd integration, config management, logging
- **Usage**: Extended by other modules for background services

### Planned Modules

#### 🛡️ **Escrow System** (`duxos_escrow/`)
- **Purpose**: Manages payment escrow for API transactions
- **Features**: 
  - Temporary fund holding during API calls
  - Automatic distribution (95% to provider, 5% to community fund)
  - Dispute resolution and refund mechanisms
- **Interfaces**: Wallet API, Task Engine API, Community Fund API

#### 🎁 **Airdrop Service** (`duxos_airdrop/`)
- **Purpose**: Distributes community fund to active nodes
- **Features**:
  - Monitors community fund balance
  - Verifies node eligibility (proof of computation)
  - Executes automatic airdrops when threshold reached
- **Interfaces**: Community Fund API, Node Registry API

#### 🏪 **API/App Store** (`duxos_store/`)
- **Purpose**: Decentralized marketplace for APIs and applications
- **Features**:
  - Service discovery and registration
  - Rating and review system
  - Distributed metadata storage (IPFS/DHT)
- **Interfaces**: Task Engine API, Wallet API, Discovery Protocol

#### ⚙️ **Task Engine** (`duxos_tasks/`)
- **Purpose**: Distributes and executes computational tasks
- **Features**:
  - Task scheduling and load balancing
  - Sandboxed execution environments
  - Result verification and trust scoring
- **Interfaces**: Store API, Wallet API, Node Registry API

#### 🌐 **Node Registry** (`duxos_registry/`)
- **Purpose**: Maintains network topology and node information
- **Features**:
  - Node discovery and health monitoring
  - Reputation scoring system
  - Network topology management
- **Interfaces**: All other modules for node coordination

### 🔗 Module Interoperability

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Build System  │    │  Wallet System  │    │ Daemon Framework│
│                 │    │                 │    │                 │
│ • ISO Creation  │    │ • Flop Coin     │    │ • Service Mgmt  │
│ • Branding      │    │ • Transactions  │    │ • Config        │
│ • Distribution  │    │ • RPC Interface │    │ • Logging       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Core Services  │
                    │                 │
                    │ • Escrow        │
                    │ • Airdrop       │
                    │ • Task Engine   │
                    │ • Store         │
                    │ • Registry      │
                    └─────────────────┘
```

### 🔄 Data Flow Example

1. **Service Publication**: Developer uses Store module to register API
2. **Service Discovery**: User browses Store, finds desired API
3. **Task Execution**: Task Engine distributes request to provider node
4. **Payment Processing**: Escrow holds funds, Wallet processes transaction
5. **Community Distribution**: Airdrop service monitors fund balance
6. **Network Coordination**: Registry tracks all node activities

### 🛠️ Development Guidelines

- **Standardized Interfaces**: All modules use JSON-RPC or REST APIs
- **Configuration**: YAML-based config files for all modules
- **Logging**: Structured logging with configurable levels
- **Security**: Sandboxed execution, encrypted communications
- **Testing**: Unit tests for each module, integration tests for workflows

---

Dux Operating System (Dux OS)
=============================

Overview:
---------
Dux OS is a Linux-based, distributed operating system designed for collaborative computing. It connects multiple computers into a decentralized network where nodes share real-world computational tasks. Unlike traditional crypto networks that waste resources solving arbitrary hashes, Dux OS allows nodes to complete useful jobs such as processing data, running simulations, or executing APIs — and get paid for it.

Key Features:
-------------
- Distributed computing via DuxNet
- Node-based architecture for compute sharing
- Lightweight and customizable (based on Ubuntu/Debian)
- Task scheduling, trust scoring, and fault tolerance
- Integrated Flop Coin wallet system for payments
- Monetized API/App Store

Distributed API/App Store with Flop Coin:
-----------------------------------------
Dux OS includes a decentralized API and application marketplace. Nodes can publish services and charge others Flop Coin per use.

Flop Coin:
https://github.com/Flopcoin/Flopcoin.git
- The native digital currency of Dux OS.
- Used for buying and selling API/app access.
- Managed through local, secure wallets.

How It Works:
-------------

1. Developer Publishes an API or App
   - Uses Dux Store dashboard to register endpoint, metadata, and price in Flop Coin.
   - Metadata is distributed via decentralized registry (e.g., IPFS, DHT).

2. User Discovers Services
   - Browses distributed app store using local UI.
   - Searches/filter by tags, price, rating.

3. Execution or API Call
   - User requests execution.
   - API or App responds with results.

4. Payment Handling
   - System deducts Flop Coin from user wallet and credits provider wallet.
   - Logs and signs each transaction.

5. Security and Trust
   - Public/private key signing.
   - Optional reputation scoring for accuracy and reliability.

Optional Enhancements:
----------------------
- Smart Contracts: Enable usage terms and refunds.
- Reputation Systems: Encourage high-quality nodes.
- CLI Access: Seamless use via terminal.
- Execution Sandbox: Secure environments for remote code.

Use Case Example:
-----------------
- Alice publishes an image upscaling API (1 Flop Coin per call).
- Bob discovers it and sends an image.
- Service executes, Bob's wallet is debited, Alice earns.

Benefits:
---------
- Allows developers to monetize software usage.
- Encourages useful computation rather than wasteful mining.


# Dux Net Payment System - High-Level Specification

## Overview

The Dux Net payment system is an integrated, decentralized escrow-based economy built into every Dux OS installation. It enables secure, automated payments using Flop Coin for API/app usage on the network, with a built-in 5% tax redirected to a community fund. When the fund reaches 100 Flop Coin, it is evenly airdropped to all verified, active Dux OS nodes.

---

## System Components

### 1. **Flop Coin Wallet Daemon (**``**)**

- Installed by default on every Dux OS node.
- Handles key generation, wallet management, sending/receiving Flop Coin.
- Provides RPC interface for interaction with other components.

### 2. **Escrow Daemon (**``**)**

- Manages temporary storage of payments when a user requests a paid API.
- Validates task completion before releasing funds.
- Distributes 95% to API developer, 5% to community fund wallet.
- Stores logs for transparency.

### 3. **Community Fund Wallet**

- Shared wallet known to all Dux OS nodes.
- Accumulates 5% tax from all paid transactions.
- Visible in the wallet GUI.

### 4. **Airdrop Service (**``**)**

- Monitors the community fund balance.
- Triggers airdrop to all verified active Dux OS nodes when balance ≥ 100 Flop Coin.
- Uses deterministic user verification (e.g., proof of recent task completion or system heartbeat).

### 5. **Dux OS Wallet & GUI**

- Displays:
  - Wallet balance
  - Transaction history
  - Escrow activity
  - Community fund balance
  - Upcoming airdrops
- Allows user interaction with Flop Coin features and transparency tools.

### 6. **Dux Net Task Engine**

- Responsible for distributing and executing API tasks.
- Interfaces with `dux-escrowd` to initiate and confirm payments.

---

## Functional Flow

### API Transaction Example

1. User selects and calls a paid API (e.g., 10 Flop).
2. `dux-escrowd` moves 10 Flop into escrow.
3. API is executed by the provider node.
4. Upon verification:
   - 9.5 Flop sent to API provider's wallet
   - 0.5 Flop sent to community fund
5. GUI updates transaction history and displays success.

### Airdrop Trigger Flow

1. Community fund hits 100 Flop Coin.
2. `dux-airdropd` calculates eligible nodes.
3. 100 Flop divided equally among them.
4. Airdrop is logged and shown in all GUIs.

---

## Governance and Security

- Parameters like tax %, minimum airdrop, and eligibility criteria are configurable via a Dux OS governance layer.
- All transactions and fund changes are logged.
- Anti-Sybil protections can be enforced using proof of computation or heartbeat verifications.

---

## Deployment Notes

- All daemons are enabled at boot and require no user setup.
- Systemd services: `dux-flopd`, `dux-escrowd`, `dux-airdropd`.
- Logs and configs stored in `/etc/duxnet/` and `/var/log/duxnet/`.

---

## Future Considerations

- Add smart contract capability to Flop Coin for greater escrow automation.
- Implement community voting on community fund use or redistribution models.
- Integrate with other decentralized identity systems for fairer airdrop allocation.

---

# Security and Logic Considerations

The following considerations are critical for the secure and reliable operation of Dux OS and its payment system:

## Node Eligibility and Airdrop Distribution
- Node eligibility for airdrops must be clearly defined (e.g., proof of recent task completion, system heartbeat, or other verifiable activity).
- Anti-Sybil mechanisms (such as proof-of-computation or identity verification) are required to prevent malicious actors from claiming multiple airdrop shares.
- The method for dividing airdrops among eligible nodes should be deterministic and transparent.

## Fractional Flop Coin and Rounding
- All calculations involving Flop Coin (including the 5% tax) must specify how fractional values are handled (e.g., rounding rules, minimum transaction units) to avoid cumulative errors or disputes.

## Transaction Rollback and Dispute Resolution
- If an API call fails or is disputed, there must be a clear process for returning escrowed funds to the user.
- A dispute resolution mechanism should be defined for handling failed or fraudulent transactions.

## Wallet Security and Key Management
- Private keys for wallets must be encrypted at rest and never exposed in plaintext.
- Users should be encouraged to use strong passwords and backup their keys securely.

## Community Fund Wallet Security
- The community fund wallet must use multi-signature or threshold signature schemes to prevent unauthorized access.
- The private key should never be distributed or stored in a way that allows a single node to control the fund.

## API/App Store Security
- All distributed APIs/Apps must run in secure sandboxes to prevent malicious code execution on user nodes.
- Code review or automated scanning is recommended before publishing APIs/Apps to the marketplace.

## Network Security
- All communications between nodes, wallets, and daemons must be encrypted (e.g., using TLS) to prevent eavesdropping or tampering.

## Rate Limiting and Abuse Prevention
- Implement rate limiting and abuse prevention mechanisms to protect against spam, denial-of-service, and microtransaction attacks.

## Governance and Configurability
- The process for changing system parameters (tax %, airdrop minimums, eligibility criteria) must be transparent and require consensus or voting among stakeholders.

---

# Dux Net Payment System - System Diagram

```
+---------------------------+
|     Dux OS Wallet GUI     |
|---------------------------|
| Wallet | Escrow | Airdrop |
+---------------------------+
            |
            v
+---------------------------+
|  Flop Coin Wallet Daemon  |
|       (dux-flopd)         |
+------------+--------------+
             |
             v
+---------------------------+
|     Escrow Daemon         |
|      (dux-escrowd)        |
+------------+--------------+
             |
   +---------+--------+
   |                  |
   v                  v
 API Dev Wallet   Community Fund Wallet
     (95%)               (5%)

             v
+---------------------------+
|   Airdrop Service         |
|     (dux-airdropd)        |
+------------+--------------+
             |
             v
   All Active Dux OS Nodes
     (Equal Distribution)
```
- Builds a decentralized compute economy on Linux.

# Dux OS Node Registry CLI

## Overview

The Dux OS Node Registry CLI is a powerful command-line tool for managing and monitoring nodes in the Dux OS ecosystem. It provides comprehensive functionality for node registration, health tracking, and reputation management.

## Features

- Register new nodes with detailed hardware specifications
- Deregister nodes
- List nodes with advanced filtering
- Update node health metrics
- Track node reputation
- Flexible logging configuration

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation

### Option 1: Automated Installation (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/duxos/node-registry.git
cd node-registry
```

2. Run the installation script:
```bash
./install.sh
```

This script will:
- Check Python version compatibility
- Create a virtual environment
- Install the package and dependencies
- Run tests
- Verify CLI installation

### Option 2: Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/duxos/node-registry.git
cd node-registry
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the package:
```bash
pip install -e .[dev]
```

### Verifying Installation

After installation, you can verify the CLI is working:
```bash
# Activate the virtual environment (if not already active)
source venv/bin/activate

# Run the CLI help command
duxos-node-registry --help
```

### Troubleshooting

- Ensure you have Python 3.8+ installed
- Make sure you're in the virtual environment before running the CLI
- Check that all dependencies are installed correctly

## Usage

### Basic Commands

#### Register a Node
```bash
duxos-node-registry register \
    --wallet-address 0x1234567890abcdef1234567890abcdef12345678 \
    --ip-address 192.168.1.100 \
    --hostname my-node \
    --os-version 22.04 \
    --duxos-version 1.0.0 \
    --cpu-cores 8 \
    --memory-gb 16 \
    --storage-gb 500 \
    --gpu-enabled \
    --gpu-model "NVIDIA RTX 3080"
```

#### List Nodes
```bash
# List all nodes
duxos-node-registry list

# List nodes with minimum specifications
duxos-node-registry list \
    --min-cpu 4 \
    --min-memory 8 \
    --min-storage 250 \
    --min-reputation 0.7
```

#### Update Node Health
```bash
duxos-node-registry update-health NODE_ID \
    --load-average 0.5 \
    --memory-usage 65.5 \
    --disk-usage 45.2
```

### Logging Options

#### Console Logging Levels
```bash
# Default (INFO level)
duxos-node-registry register ...

# Verbose logging (DEBUG level)
duxos-node-registry register ... --log-level DEBUG

# Log to a file
duxos-node-registry register ... --log-file /var/log/duxos/node_registry.log

# Combine log level and file logging
duxos-node-registry register ... \
    --log-level DEBUG \
    --log-file /var/log/duxos/node_registry.log
```

## Configuration

The CLI supports various configuration options through command-line arguments. Use `--help` for detailed information:

```bash
duxos-node-registry --help
duxos-node-registry register --help
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Dux OS Team - support@duxos.org

Project Link: [https://github.com/duxos/node-registry](https://github.com/duxos/node-registry)

# DuxOS Node Registry

## Real Flopcoin Wallet Integration & Desktop Environment (Phase 2.2)

### Overview
DuxOS Node Registry now supports full integration with the real Flopcoin Core daemon and includes a complete desktop environment. This enables live wallet operations, address management, transaction processing, and a modern GUI interface for the Flopcoin blockchain.

### Flopcoin Integration Features
- Connects to a real Flopcoin Core daemon (v2.x)
- Secure RPC communication (configurable credentials)
- Wallet creation, address generation, and balance queries
- Send/receive FLOP transactions
- Transaction history and status
- Blockchain/network info and fee estimation
- Automated wallet backup

### Desktop Environment Features
- **Modern GUI** - Full desktop environment with XFCE integration
- **Desktop Manager** - Custom DuxOS desktop manager with system monitoring
- **Application Launcher** - Easy access to all DuxOS applications
- **System Tray** - Real-time system resource monitoring
- **Desktop Shortcuts** - Quick access to key applications
- **Autostart Services** - Automatic startup of DuxOS services

### Setup Instructions
1. **Install Flopcoin Core**
   - Download from: https://github.com/Flopcoin/Flopcoin/releases
   - Extract and install `flopcoind` and `flopcoin-cli` to `/usr/local/bin`

2. **Configure Flopcoin Daemon**
   - Use `scripts/setup_flopcoin.py` to generate `~/.flopcoin/flopcoin.conf` with your chosen RPC password.
   - Start the daemon: `flopcoind -daemon`

3. **Update Wallet Config**
   - Edit `duxos_wallet/config.yaml` with your RPC credentials and settings.

4. **Setup Desktop Environment (Optional)**
   - Run `sudo python scripts/setup_desktop.py` to install XFCE and configure the desktop environment.
   - Restart your system to apply changes.

5. **Test Integration**
   - Run `python scripts/test_real_flopcoin.py` to verify wallet and blockchain connectivity.

### Usage

#### Command Line
- Use the wallet API/CLI for live Flopcoin operations.
- Monitor blockchain sync status and wallet backups.
- For production, enable wallet encryption and secure your RPC credentials.

#### Desktop Environment
- Start DuxOS Desktop: `python duxos_desktop/desktop_manager.py`
- Or login to the desktop environment after setup
- Use the sidebar to access all DuxOS applications
- Monitor system resources via the system tray

### Troubleshooting
- Ensure no mock daemons are running on the RPC port.
- Check `~/.flopcoin/debug.log` for daemon errors.
- Use `flopcoin-cli` for direct RPC testing.

---

For more details, see the `docs/` directory and the development plan.
