# DuxOS Flop Wallet Component

## Overview

The DuxOS Flop Wallet is a core component of the Dux OS project, designed to facilitate Flop Coin transactions. It acts as a Python wrapper around the Flopcoin Core's JSON-RPC API, allowing Dux OS to interact with the Flopcoin blockchain for operations such as generating new addresses, checking balances, and sending Flop Coins.

## Setup Instructions

To set up and run the Flop Wallet, follow these steps:

1.  **Install Flopcoin Core**: 
    Download and install the Flopcoin Core client (`flopcoind`) from the official Flopcoin repository: `https://github.com/Flopcoin/Flopcoin.git`.

2.  **Configure Flopcoin Core**: 
    Edit the `flopcoin.conf` file, typically located in `~/.flopcoin/`. Add or modify the following lines:
    ```conf
    rpcuser=flopcoinrpc
    rpcpassword=your_secure_password  # **IMPORTANT: Replace with a strong, unique password**
    rpcport=32553
    server=1
    ```

3.  **Start Flopcoin Core Daemon**: 
    Run Flopcoin Core in daemon mode:
    ```bash
    flopcoind -daemon
    ```

4.  **Navigate to Wallet Directory**:
    ```bash
    cd duxos_wallet
    ```

5.  **Install Python Dependencies**: 
    Install the required Python packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Set up Logging Directory**:
    The wallet logs to `/var/log/duxnet/wallet.log`. Ensure this directory exists and has appropriate permissions:
    ```bash
    sudo mkdir -p /var/log/duxnet/
    sudo chmod 755 /var/log/duxnet/
    # Ensure the user running the wallet has write permissions to wallet.log
    # For example, if running as 'dux':
    # sudo chown dux:dux /var/log/duxnet/wallet.log
    ```

## Usage Examples

After setting up Flopcoin Core and installing dependencies, you can use the `wallet.py` script to interact with your Flopcoin wallet.

To run the example usage:

```bash
python wallet.py
```

This will demonstrate the following functionalities:

### `get_new_address()`
Generates and returns a new Flopcoin address.

```python
# Example usage in wallet.py:
new_address = wallet.get_new_address()
if new_address:
    print(f"New Flopcoin Address: {new_address}")
```

### `get_balance()`
Retrieves and returns the total balance of the wallet.

```python
# Example usage in wallet.py:
balance = wallet.get_balance()
if balance is not None:
    print(f"Current Balance: {balance} Flop Coin")
```

### `send_to_address(address, amount)`
Sends a specified `amount` of Flop Coin to a given `address`. Amounts are rounded to 2 decimal places (minimum unit: 0.01 Flop Coin). Includes input validation.

```python
# Example usage in wallet.py:
# NOTE: Replace with a real address and a small test amount for actual testing.
#       Ensure your Flopcoin Core wallet has funds.
test_address = "FLOP_TEST_ADDRESS_HERE"  # Replace with a valid Flopcoin address
test_amount = 0.01
txid, send_error = wallet.send_to_address(test_address, test_amount)
if txid:
    print(f"Transaction successful! TXID: {txid}")
else:
    print(f"Transaction failed: {send_error}")
```

## Security Notes

-   **Secure `config.yaml`**: The `config.yaml` file contains sensitive RPC credentials. Ensure its permissions are set to `600` (owner-only read/write) to prevent unauthorized access:
    ```bash
    chmod 600 duxos_wallet/config.yaml
    ```
-   **Backup Wallet Keys**: Regularly back up your Flopcoin Core wallet keys (`wallet.dat` file) to a secure, offline location.
-   **Input Validation**: `wallet.py` implements basic input validation. Always ensure that values passed to methods like `send_to_address` are sanitized and validated to prevent unexpected behavior or vulnerabilities.
-   **Logging**: All RPC calls and errors are logged to `/var/log/duxnet/wallet.log` for debugging and auditing purposes. Monitor these logs for any suspicious activity.

## Testing

1.  Ensure Flopcoin Core (`flopcoind`) is installed, configured, and running with RPC enabled as described in the [Setup Instructions](#setup-instructions).
2.  Navigate to the `duxos_wallet` directory.
3.  Run the `wallet.py` script:
    ```bash
    python wallet.py
    ```
4.  Verify the output for new address generation, balance retrieval, and transaction sending. For transaction sending, ensure your Flopcoin Core wallet has sufficient funds.
5.  Check the logs in `/var/log/duxnet/wallet.log` for detailed messages, errors, or success confirmations.

## Future Enhancements

As per the Dux OS development plan (Phase 2.2), future enhancements for the Flop Wallet may include:

-   **Wallet Encryption**: Implement client-side wallet encryption for enhanced security.
-   **Multi-signature Support**: Add support for multi-signature transactions to enable shared control of funds.
-   **Transaction History**: Implement functionality to retrieve and display transaction history. 