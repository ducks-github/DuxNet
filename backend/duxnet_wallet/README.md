# duxnet_wallet

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
