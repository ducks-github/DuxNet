#!/usr/bin/env python3
"""
Wallet Integration Test CLI

A simple command-line interface for testing the wallet integration
with the DuxOS Node Registry.
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


class WalletTestCLI:
    base_url: str
    session: requests.Session

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.session = requests.Session()

    def create_wallet(self, node_id: str, wallet_name: str) -> Dict[str, Any]:
        """Create a new wallet for a node"""
        url = f"{self.base_url}/wallet/create"
        data = {"node_id": node_id, "wallet_name": wallet_name}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_wallet(self, node_id: str) -> Dict[str, Any]:
        """Get wallet information for a node"""
        url = f"{self.base_url}/wallet/{node_id}"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_balance(self, node_id: str) -> Dict[str, Any]:
        """Get wallet balance for a node"""
        url = f"{self.base_url}/wallet/{node_id}/balance"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def send_transaction(self, node_id: str, recipient: str, amount: float) -> Dict[str, Any]:
        """Send a transaction from a node's wallet"""
        url = f"{self.base_url}/wallet/{node_id}/send"
        data = {"node_id": node_id, "recipient_address": recipient, "amount": amount}

        try:
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def get_transactions(self, node_id: str, limit: int = 10) -> Dict[str, Any]:
        """Get transaction history for a node's wallet"""
        url = f"{self.base_url}/wallet/{node_id}/transactions"
        params = {"limit": limit}

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def generate_address(self, node_id: str) -> Dict[str, Any]:
        """Generate a new address for a node's wallet"""
        url = f"{self.base_url}/wallet/{node_id}/new-address"

        try:
            response = self.session.post(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Check wallet service health"""
        url = f"{self.base_url}/wallet/health"

        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def print_result(self, result: Dict[str, Any], title: str = "Result") -> None:
        """Print formatted result"""
        print(f"\n=== {title} ===")
        if result.get("success") is False:
            print(f"❌ Error: {result.get('message', result.get('error', 'Unknown error'))}")
        else:
            print("✅ Success!")
            print(json.dumps(result, indent=2))
        print()


def interactive_mode(cli: WalletTestCLI) -> None:
    """Run interactive mode"""
    print("🚀 DuxOS Wallet Integration Test CLI")
    print("Type 'help' for available commands, 'quit' to exit\n")

    while True:
        try:
            command = input("wallet> ").strip().split()
            if not command:
                continue

            cmd = command[0].lower()

            if cmd == "quit" or cmd == "exit":
                print("👋 Goodbye!")
                break
            elif cmd == "help":
                print_help()
            elif cmd == "health":
                result = cli.health_check()
                cli.print_result(result, "Health Check")
            elif cmd == "create":
                if len(command) < 3:
                    print("❌ Usage: create <node_id> <wallet_name>")
                    continue
                node_id, wallet_name = command[1], command[2]
                result = cli.create_wallet(node_id, wallet_name)
                cli.print_result(result, f"Create Wallet for {node_id}")
            elif cmd == "info":
                if len(command) < 2:
                    print("❌ Usage: info <node_id>")
                    continue
                node_id = command[1]
                result = cli.get_wallet(node_id)
                cli.print_result(result, f"Wallet Info for {node_id}")
            elif cmd == "balance":
                if len(command) < 2:
                    print("❌ Usage: balance <node_id>")
                    continue
                node_id = command[1]
                result = cli.get_balance(node_id)
                cli.print_result(result, f"Balance for {node_id}")
            elif cmd == "send":
                if len(command) < 4:
                    print("❌ Usage: send <node_id> <recipient> <amount>")
                    continue
                node_id, recipient, amount_str = command[1], command[2], command[3]
                try:
                    amount = float(amount_str)
                except ValueError:
                    print("❌ Invalid amount")
                    continue
                result = cli.send_transaction(node_id, recipient, amount)
                cli.print_result(result, f"Send Transaction from {node_id}")
            elif cmd == "transactions":
                if len(command) < 2:
                    print("❌ Usage: transactions <node_id> [limit]")
                    continue
                node_id = command[1]
                limit = int(command[2]) if len(command) > 2 else 10
                result = cli.get_transactions(node_id, limit)
                cli.print_result(result, f"Transaction History for {node_id}")
            elif cmd == "new-address":
                if len(command) < 2:
                    print("❌ Usage: new-address <node_id>")
                    continue
                node_id = command[1]
                result = cli.generate_address(node_id)
                cli.print_result(result, f"New Address for {node_id}")
            else:
                print(f"❌ Unknown command: {cmd}")
                print("Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def print_help() -> None:
    """Print help information"""
    print(
        """
Available Commands:
  health                    - Check wallet service health
  create <node_id> <name>   - Create wallet for node
  info <node_id>           - Get wallet information
  balance <node_id>        - Get wallet balance
  send <node_id> <recipient> <amount> - Send transaction
  transactions <node_id> [limit] - Get transaction history
  new-address <node_id>    - Generate new address
  help                     - Show this help
  quit/exit                - Exit the CLI
"""
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="DuxOS Wallet Integration Test CLI")
    parser.add_argument("--url", default="http://localhost:8000", help="Registry API base URL")
    parser.add_argument("--command", help="Run single command and exit")
    parser.add_argument("--node-id", help="Node ID for commands")
    parser.add_argument("--wallet-name", help="Wallet name for create command")
    parser.add_argument("--recipient", help="Recipient address for send command")
    parser.add_argument("--amount", type=float, help="Amount for send command")

    args = parser.parse_args()

    cli = WalletTestCLI(args.url)

    if args.command:
        # Single command mode
        result: Dict[str, Any]
        if args.command == "health":
            result = cli.health_check()
        elif args.command == "create" and args.node_id and args.wallet_name:
            result = cli.create_wallet(args.node_id, args.wallet_name)
        elif args.command == "info" and args.node_id:
            result = cli.get_wallet(args.node_id)
        elif args.command == "balance" and args.node_id:
            result = cli.get_balance(args.node_id)
        elif args.command == "send" and args.node_id and args.recipient and args.amount:
            result = cli.send_transaction(args.node_id, args.recipient, args.amount)
        elif args.command == "transactions" and args.node_id:
            result = cli.get_transactions(args.node_id)
        elif args.command == "new-address" and args.node_id:
            result = cli.generate_address(args.node_id)
        else:
            print("❌ Invalid command or missing arguments")
            sys.exit(1)

        cli.print_result(result, f"{args.command.title()} Result")
    else:
        # Interactive mode
        interactive_mode(cli)


if __name__ == "__main__":
    main()
