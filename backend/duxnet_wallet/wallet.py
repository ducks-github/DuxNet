import logging
import os

import requests
import yaml

# Ensure the log directory exists
log_dir = os.path.expanduser("~/duxnet_logs")
os.makedirs(log_dir, exist_ok=True)

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(os.path.join(log_dir, "wallet.log")), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class FlopcoinWallet:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = self._load_config(config_path)
        self.rpc_url = f"http://{self.config['rpc']['host']}:{self.config['rpc']['port']}"
        self.rpc_user = self.config["rpc"]["user"]
        self.rpc_password = self.config["rpc"]["password"]
        logger.info("FlopcoinWallet initialized.")

    def _load_config(self, config_path):
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found at {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise

    def _make_rpc_call(self, method, params=None):
        headers = {"content-type": "application/json"}
        payload = {
            "method": method,
            "params": params if params is not None else [],
            "jsonrpc": "2.0",
            "id": 1,
        }
        try:
            logger.info(f"Attempting RPC call: {method} with params: {params}")
            response = requests.post(
                self.rpc_url, json=payload, headers=headers, auth=(self.rpc_user, self.rpc_password)
            )
            response.raise_for_status()
            rpc_response = response.json()
            if rpc_response.get("error"):
                logger.error(f"RPC Error for {method}: {rpc_response['error']}")
                return None, rpc_response["error"]
            logger.info(f"RPC call {method} successful.")
            return rpc_response.get("result"), None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network error connecting to Flopcoin Core: {e}")
            return None, f"Network error: {e}"
        except requests.exceptions.Timeout:
            logger.error("RPC call timed out.")
            return None, "RPC call timed out."
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during RPC call: {e}")
            return None, f"Request error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during RPC call: {e}")
            return None, f"Unexpected error: {e}"

    def get_new_address(self):
        """Generate a new Flopcoin address."""
        address, error = self._make_rpc_call("getnewaddress")
        if error:
            logger.warning(f"Failed to get new address: {error}")
            return None
        logger.info(f"Generated new address: {address}")
        return address

    def get_balance(self):
        """Retrieve the wallet's total balance."""
        balance, error = self._make_rpc_call("getbalance")
        if error:
            logger.warning(f"Failed to get balance: {error}")
            return None
        logger.info(f"Retrieved balance: {balance}")
        return balance

    def send_to_address(self, address: str, amount: float):
        """Send Flop Coin to a specified address."""
        if not isinstance(address, str) or not address:
            logger.error("Invalid input: Address must be a non-empty string.")
            return None, "Invalid address"
        if not isinstance(amount, (int, float)) or amount <= 0:
            logger.error("Invalid input: Amount must be a positive number.")
            return None, "Invalid amount"

        # Round amount to 2 decimal places
        rounded_amount = round(amount, 2)
        logger.info(f"Attempting to send {rounded_amount} Flop Coin to {address}")

        # Bitcoin Core's sendtoaddress typically takes address, amount, comment, comment_to
        # We'll use just address and amount as per prompt.
        txid, error = self._make_rpc_call("sendtoaddress", [address, rounded_amount])
        if error:
            logger.error(f"Failed to send {rounded_amount} Flop Coin to {address}: {error}")
            return None, error
        logger.info(f"Transaction successful! TXID: {txid}")
        return txid, None


if __name__ == "__main__":
    print("Running FlopcoinWallet examples...")
    wallet = FlopcoinWallet()

    print("\n--- Get New Address ---")
    new_address = wallet.get_new_address()
    if new_address:
        print(f"New Flopcoin Address: {new_address}")
    else:
        print("Could not generate a new address.")

    print("\n--- Get Balance ---")
    balance = wallet.get_balance()
    if balance is not None:
        print(f"Current Balance: {balance} Flop Coin")
    else:
        print("Could not retrieve balance.")

    print("\n--- Send To Address (Example) ---")
    # NOTE: Replace with a real address and a small test amount for actual testing.
    #       Ensure your Flopcoin Core wallet has funds.
    test_address = "FLOP_TEST_ADDRESS_HERE"  # Replace with a valid Flopcoin address
    test_amount = 0.01
    if new_address:  # Use the newly generated address as a recipient for testing purposes
        test_address = new_address

    print(f"Attempting to send {test_amount} Flop Coin to {test_address}")
    txid, send_error = wallet.send_to_address(test_address, test_amount)
    if txid:
        print(f"Transaction successful! TXID: {txid}")
    else:
        print(f"Transaction failed: {send_error}")

    print("\n--- Invalid Send To Address Example (Negative Amount) ---")
    txid_invalid_amount, send_error_invalid_amount = wallet.send_to_address(test_address, -0.5)
    if not txid_invalid_amount:
        print(f"As expected, transaction with invalid amount failed: {send_error_invalid_amount}")

    print("\n--- Invalid Send To Address Example (Empty Address) ---")
    txid_empty_address, send_error_empty_address = wallet.send_to_address("", 1.0)
    if not txid_empty_address:
        print(f"As expected, transaction with empty address failed: {send_error_empty_address}")

    print("\nFlopcoinWallet examples finished. Check /var/log/duxnet/wallet.log for detailed logs.")
