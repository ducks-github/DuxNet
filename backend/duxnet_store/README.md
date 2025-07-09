# duxnet_store

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
