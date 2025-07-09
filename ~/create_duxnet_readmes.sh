#!/bin/bash

set -e

# Helper function to write a README file
write_readme() {
  local path="$1"
  local content="$2"
  mkdir -p "$(dirname "$path")"
  echo "$content" > "$path"
  echo "Created $path"
}

# duxnet_wallet
write_readme backend/duxnet_wallet/README.md "# duxnet_wallet

A backend module for managing Flopcoin and multi-cryptocurrency wallets in DuxNet.

## Features

- Create, import, and manage wallets
- Send and receive Flopcoin and other supported cryptocurrencies
- Transaction history and balance queries
- Secure key storage

## Usage

python main.py

## API

- create_wallet()
- import_wallet(mnemonic)
- send(to_address, amount)
- get_balance()
- get_transaction_history()

## Configuration

Edit config.yaml for wallet settings.

## Security

- Private keys are encrypted at rest.
- Never share your mnemonic or private key.

## Testing

pytest ../../tests/backend/test_wallet.py
"

# duxnet_registry
write_readme backend/duxnet_registry/README.md "# duxnet_registry

Node registry and governance backend for DuxNet.

## Features

- Register and manage nodes
- Governance voting and proposals
- Node status and metadata queries

## Usage

python main.py

## API

- register_node(public_key, metadata)
- get_node(node_id)
- list_nodes()
- submit_proposal(proposal_data)
- vote(proposal_id, vote)

## Configuration

Edit config.yaml for registry settings.

## Security

- Node registration requires cryptographic proof.
- Governance actions are logged and auditable.

## Testing

pytest ../../tests/backend/test_node_registry.py
"

# duxnet_store
write_readme backend/duxnet_store/README.md "# duxnet_store

Decentralized storage backend for DuxNet.

## Features

- Store and retrieve files and metadata
- Service discovery for storage nodes
- Data integrity verification

## Usage

python main.py

## API

- store_file(file_path)
- retrieve_file(file_id)
- list_files(owner)

## Configuration

Edit config.yaml for storage settings.

## Security

- Files are hashed and verified on retrieval.
- Access control via public/private keys.

## Testing

pytest ../../tests/backend/test_store_service.py
"

# duxos_escrow
write_readme backend/duxos_escrow/README.md "# duxos_escrow

Escrow and payment logic for DuxNet and DuxOS.

## Features

- Create and manage escrow contracts
- Multi-party payment flows
- Dispute resolution

## Usage

python main.py

## API

- create_escrow(buyer, seller, amount)
- release_funds(escrow_id)
- raise_dispute(escrow_id, reason)

## Configuration

Edit config.yaml for escrow settings.

## Security

- Funds are locked in smart contracts until release.
- Disputes require multi-signature resolution.

## Testing

pytest ../../tests/backend/test_escrow_logic.py
"

# duxos_registry
write_readme backend/duxos_registry/README.md "# duxos_registry

DuxOS node registry backend.

## Features

- Register DuxOS nodes
- Query node status and metadata

## Usage

python main.py

## API

- register_node(public_key, metadata)
- get_node(node_id)
- list_nodes()

## Configuration

Edit config.yaml for DuxOS registry settings.

## Testing

pytest ../../tests/backend/test_node_registry.py
"

# duxos_store
write_readme backend/duxos_store/README.md "# duxos_store

DuxOS storage backend.

## Features

- Store and retrieve files for DuxOS nodes
- Data integrity and redundancy

## Usage

python main.py

## API

- store_file(file_path)
- retrieve_file(file_id)

## Configuration

Edit config.yaml for DuxOS storage settings.

## Testing

pytest ../../tests/backend/test_store_service.py
"

# duxos_tasks
write_readme backend/duxos_tasks/README.md "# duxos_tasks

Task engine and scheduler for DuxOS.

## Features

- Schedule and manage distributed tasks
- Monitor task status and results

## Usage

python main.py

## API

- schedule_task(task_data)
- get_task_status(task_id)
- list_tasks(owner)

## Configuration

Edit config.yaml for task engine settings.

## Testing

pytest ../../tests/backend/test_task_engine_integration.py
"

# duxos_wallet
write_readme backend/duxos_wallet/README.md "# duxos_wallet

DuxOS wallet backend.

## Features

- Manage DuxOS-specific wallets
- Send and receive tokens

## Usage

python main.py

## API

- create_wallet()
- send(to_address, amount)
- get_balance()

## Configuration

Edit config.yaml for wallet settings.

## Testing

pytest ../../tests/backend/test_wallet.py
"

# duxnet_desktop
write_readme frontend/duxnet_desktop/README.md "# duxnet_desktop

Desktop GUI for DuxNet.

## Features

- Visual wallet management
- Node and service monitoring
- Transaction history

## Usage

python main.py

## Requirements

- Python 3.8+
- PyQt5 or Tkinter

## Development

Install dependencies:
pip install -r ../../../tests/requirements.txt
"

# duxnet_wallet_cli
write_readme frontend/duxnet_wallet_cli/README.md "# duxnet_wallet_cli

Command-line wallet interface for DuxNet.

## Features

- Create/import wallets
- Send/receive funds
- View balances and transactions

## Usage

python wallet/main.py --help

## Example

python wallet/main.py create
python wallet/main.py send --to <address> --amount 10

## Development

Install dependencies:
pip install -r ../../../tests/requirements.txt
"

# duxos_desktop
write_readme frontend/duxos_desktop/README.md "# duxos_desktop

Desktop GUI for DuxOS.

## Features

- Manage DuxOS wallets and nodes
- Monitor DuxOS services

## Usage

python main.py

## Requirements

- Python 3.8+
- PyQt5 or Tkinter

## Development

Install dependencies:
pip install -r ../../../tests/requirements.txt
"

echo "All DuxNet submodule README files created."