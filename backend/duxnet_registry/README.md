# duxnet_registry

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
