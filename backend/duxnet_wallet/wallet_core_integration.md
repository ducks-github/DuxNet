# wallet_core integration for DuxNet

This module provides a Python interface to Trust Wallet's wallet-core using the community Python bindings.

## Prerequisites
- Build wallet-core as described in docs/WALLET_CORE_BUILD.md
- Install the wallet-core Python bindings (see below)

## Installation

1. Build wallet-core C++ library (see docs/WALLET_CORE_BUILD.md)
2. Install the Python bindings:
   - Recommended: https://github.com/phuang/wallet-core-python
   - Or build your own bindings using SWIG/pybind11

## Usage Example

```python
from wallet_core import WalletCore
# Example: create a Bitcoin address
btc_wallet = WalletCore('bitcoin')
address = btc_wallet.get_address()
```

## Licensing
- See docs/WALLET_CORE_ATTRIBUTION.md
- Trust Wallet wallet-core is Apache 2.0 licensed
