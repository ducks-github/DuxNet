# DuxOS Wallet Module

## Overview

The DuxOS Wallet module provides a Python interface for interacting with the Flopcoin blockchain, enabling wallet operations such as generating addresses, checking balances, and sending transactions.

## Features

- Generate new Flopcoin addresses
- Check wallet balance
- Send Flop Coin to specified addresses
- Comprehensive error handling and logging
- Configurable RPC connection settings

## Installation

```bash
# Install via Poetry
poetry install

# Or via pip
pip install duxos
```

## Configuration

The wallet uses a YAML configuration file with the following structure:

```yaml
rpc:
  host: 127.0.0.1      # Flopcoin Core RPC host
  port: 32553          # Flopcoin Core RPC port
  user: flopcoinrpc    # RPC username
  password: your_password  # RPC password
wallet:
  encryption: true     # Enable wallet encryption
  backup_interval: 3600  # Backup interval in seconds
```

## CLI Usage

```bash
# Generate a new address
duxos-wallet new-address

# Check wallet balance
duxos-wallet balance

# Send Flop Coin
duxos-wallet send --address RECIPIENT_ADDRESS --amount 10.50
```

## Programmatic Usage

```python
from duxos.wallet.wallet import FlopcoinWallet

# Initialize wallet with default config
wallet = FlopcoinWallet()

# Get a new address
new_address = wallet.get_new_address()

# Check balance
balance = wallet.get_balance()

# Send Flop Coin
txid, error = wallet.send_to_address('RECIPIENT_ADDRESS', 10.50)
```

## Security Considerations

- Always keep your RPC credentials secure
- Use strong, unique passwords
- Enable wallet encryption
- Regularly backup your wallet

## Logging

Logs are written to `~/duxos_logs/wallet.log` with detailed transaction and error information.

## Dependencies

- `requests`
- `pyyaml`
- `logging`

## Contributing

Contributions are welcome! Please submit pull requests or open issues on our GitHub repository. 