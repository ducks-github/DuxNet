"""
Wallet Client for DuxOS Desktop

Handles wallet operations and user account management via duxnet_wallet API.
"""

from typing import Any, Dict, Optional

import requests

WALLET_API_URL = "http://localhost:8002"  # Can be made configurable


class WalletClient:
    def __init__(self, base_url: str = WALLET_API_URL):
        self.base_url = base_url.rstrip("/")

    def get_wallet(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = requests.get(f"{self.base_url}/wallet/{user_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_balance(self, user_id: Optional[str] = None, currency: str = "FLOP") -> Optional[float]:
        if user_id:
            wallet = self.get_wallet(user_id)
            if wallet:
                return wallet.get("balance")
            return None
        else:
            # Direct balance query for multi-crypto
            try:
                response = requests.get(f"{self.base_url}/balance/{currency}")
                response.raise_for_status()
                return response.json().get("balance", 0.0)
            except Exception as e:
                print(f"Error getting {currency} balance: {e}")
                return 0.0

    def send_payment(self, from_user: str, to_address: str, amount: float) -> Dict[str, Any]:
        payload = {"from_user": from_user, "to_address": to_address, "amount": amount}
        response = requests.post(f"{self.base_url}/wallet/send", json=payload)
        response.raise_for_status()
        return response.json()

    def get_transactions(self, user_id: str) -> list:
        response = requests.get(f"{self.base_url}/wallet/{user_id}/transactions")
        response.raise_for_status()
        return response.json()

    def get_all_balances(self) -> Dict[str, Dict[str, Any]]:
        """Get balances for all supported currencies"""
        try:
            response = requests.get(f"{self.base_url}/balances")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting all balances: {e}")
            return {
                "BTC": {"balance": 0.0, "address": "unknown"},
                "ETH": {"balance": 0.0, "address": "unknown"},
                "FLOP": {"balance": 0.0, "address": "unknown"},
                "USDT": {"balance": 0.0, "address": "unknown"},
                "BNB": {"balance": 0.0, "address": "unknown"},
                "XRP": {"balance": 0.0, "address": "unknown"},
                "SOL": {"balance": 0.0, "address": "unknown"},
                "ADA": {"balance": 0.0, "address": "unknown"},
                "DOGE": {"balance": 0.0, "address": "unknown"},
                "TON": {"balance": 0.0, "address": "unknown"},
                "TRX": {"balance": 0.0, "address": "unknown"}
            }

    def send_transaction(self, currency: str, to_address: str, amount: float) -> Dict[str, Any]:
        """Send transaction for specific currency"""
        try:
            data = {"currency": currency, "to_address": to_address, "amount": amount}
            response = requests.post(f"{self.base_url}/send", json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending {currency} transaction: {e}")
            return {"txid": "unknown"}

    def get_transaction_history(self, currency: str = "FLOP", limit: int = 10) -> list:
        """Get transaction history for specific currency"""
        try:
            response = requests.get(f"{self.base_url}/transactions/{currency}?limit={limit}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting {currency} transaction history: {e}")
            return []
