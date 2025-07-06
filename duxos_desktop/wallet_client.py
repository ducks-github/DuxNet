"""
Wallet Client for DuxOS Desktop

Handles wallet operations and user account management via duxos_wallet API.
"""

import requests
from typing import Optional, Dict, Any

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

    def get_balance(self, user_id: str) -> Optional[float]:
        wallet = self.get_wallet(user_id)
        if wallet:
            return wallet.get("balance")
        return None

    def send_payment(self, from_user: str, to_address: str, amount: float) -> Dict[str, Any]:
        payload = {"from_user": from_user, "to_address": to_address, "amount": amount}
        response = requests.post(f"{self.base_url}/wallet/send", json=payload)
        response.raise_for_status()
        return response.json()

    def get_transactions(self, user_id: str) -> list:
        response = requests.get(f"{self.base_url}/wallet/{user_id}/transactions")
        response.raise_for_status()
        return response.json() 