# Steps to Create the DuxOS Wallet (Flop Wallet)

This document outlines the steps taken to create the DuxOS Wallet component, implementing the Flop Wallet functionality.

## 1. Create the `duxnet_wallet/` Directory
- A directory named `duxnet_wallet` was created at the root of the Dux OS project to house the wallet component files.

## 2. Create `wallet.py`
- File: `duxnet_wallet/wallet.py`
- Purpose: Implements the `FlopcoinWallet` class as a Python wrapper for Flopcoin Core's JSON-RPC API.
- Functionalities:
  - `get_new_address()`: Generates a new Flopcoin address using the `getnewaddress` RPC call.
  - `get_balance()`: Retrieves the wallet's total balance using the `getbalance` RPC call.
  - `send_to_address(address, amount)`: Sends Flop Coin to a specified address using the `sendtoaddress` RPC call.
- Features:
  - Uses `requests` for JSON-RPC calls to Flopcoin Core (assumed running at `http://127.0.0.1:32553`).
  - Loads configuration from `config.yaml` using `pyyaml`.
  - Implements structured logging to `/var/log/duxnet/wallet.log` with `logging`.
  - Includes input validation (e.g., positive amounts, valid addresses).
  - Rounds amounts to 2 decimal places (assumed minimum unit: 0.01 Flop Coin).
  - Handles errors for RPC failures, network issues, and invalid inputs.
- Dependencies: `requests`, `pyyaml`.

## 3. Create `config.yaml`
- File: `duxnet_wallet/config.yaml`
- Purpose: Stores RPC connection details and wallet settings.
- Content:
  ```yaml
  rpc:
    host: 127.0.0.1
    port: 32553
    user: flopcoinrpc
    password: your_secure_password
  wallet:
    encryption: true
    backup_interval: 3600
  logging:
    level: INFO
    file: /var/log/duxnet/wallet.log
  ```
- Security: File permissions should be set to `600` (owner-only read/write) manually by the user for security.

## 4. Add Dependencies File
- File: `duxnet_wallet/requirements.txt`
- Content: Lists required Python packages (`requests`, `pyyaml`).
- Purpose: Simplifies dependency installation via `pip install -r requirements.txt`.

## 5. Create Documentation
- File: `duxnet_wallet/README_wallet.md`
- Content:
  - Overview of the Flop Wallet component.
  - Setup instructions (e.g., install Flopcoin Core, configure `flopcoin.conf`, install dependencies).
  - Usage examples for `get_new_address()`, `get_balance()`, `send_to_address()`.
  - Security notes (e.g., secure `config.yaml`, backup wallet keys).
  - Testing instructions (e.g., run `python wallet.py` with Flopcoin Core running).

## 6. Set Up Logging Directory
- The directory `/var/log/duxnet/` needs to be created to store logs (e.g., `wallet.log`).
- Permissions should be set to ensure write access for the wallet process (e.g., `chmod 755 /var/log/duxnet`). This is a manual step for the user due to system-level permissions.

## 7. Testing Setup
- Ensure Flopcoin Core (`flopcoind`) is installed and running with RPC enabled (`rpcuser=flopcoinrpc`, `rpcpassword=your_secure_password`, `rpcport=32553` in `flopcoin.conf`).
- Test the wallet by running `python wallet.py` and verifying:
  - New address generation.
  - Balance retrieval.
  - Transaction sending (with a test amount, e.g., 1.0 Flop Coin).
- Check logs in `/var/log/duxnet/wallet.log` for errors or success messages.

## 8. Security Considerations
- Secure `config.yaml` with `chmod 600` to protect RPC credentials. (Manual step for user).
- Validate inputs in `wallet.py` (e.g., positive amounts, non-empty addresses).
- Log all RPC calls and errors for debugging and auditing.
- Prepare for future enhancements (e.g., wallet encryption, multi-signature support) as noted in the development plan (Phase 2.2). 