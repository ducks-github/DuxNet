#!/usr/bin/env python3
"""
Multi-Cryptocurrency CLI for DuxNet
Supports Bitcoin, Ethereum, and other major cryptocurrencies
"""

import argparse
import sys
from decimal import Decimal
from typing import Optional

from .multi_crypto_wallet import MultiCryptoWallet


def main():
    parser = argparse.ArgumentParser(description="DuxNet Multi-Cryptocurrency Wallet CLI")
    parser.add_argument(
        "action", 
        choices=["balance", "new-address", "send", "history", "currencies", "info"], 
        help="Wallet action to perform"
    )
    parser.add_argument("--currency", "-c", help="Cryptocurrency symbol (e.g., BTC, ETH)")
    parser.add_argument("--address", help="Recipient address for send action")
    parser.add_argument("--amount", type=float, help="Amount to send for send action")
    parser.add_argument("--fee", type=float, help="Transaction fee (optional)")
    parser.add_argument("--config", help="Path to custom config file", default=None)
    parser.add_argument("--limit", type=int, default=10, help="Number of transactions to show for history")

    args = parser.parse_args()

    try:
        wallet = MultiCryptoWallet(config_path=args.config)
        
        if args.action == "currencies":
            currencies = wallet.get_supported_currencies()
            print("Supported cryptocurrencies:")
            for currency in currencies:
                print(f"  - {currency}")
            return

        if args.action == "info":
            print("DuxNet Multi-Cryptocurrency Wallet")
            print("=" * 40)
            currencies = wallet.get_supported_currencies()
            print(f"Supported currencies: {', '.join(currencies)}")
            
            balances = wallet.get_all_balances()
            print("\nCurrent balances:")
            for currency, balance in balances.items():
                if balance is not None:
                    print(f"  {currency}: {balance}")
                else:
                    print(f"  {currency}: Error getting balance")
            return

        if args.action == "balance":
            if args.currency:
                balance = wallet.get_balance(args.currency)
                if balance is not None:
                    print(f"{args.currency} Balance: {balance}")
                else:
                    print(f"Error getting {args.currency} balance")
            else:
                balances = wallet.get_all_balances()
                print("All balances:")
                for currency, balance in balances.items():
                    if balance is not None:
                        print(f"  {currency}: {balance}")
                    else:
                        print(f"  {currency}: Error getting balance")

        elif args.action == "new-address":
            if not args.currency:
                print("Error: --currency is required for new-address action")
                sys.exit(1)
            
            address = wallet.get_new_address(args.currency)
            if address:
                print(f"New {args.currency} Address: {address}")
            else:
                print(f"Error generating {args.currency} address")
                sys.exit(1)

        elif args.action == "send":
            if not args.currency or not args.address or not args.amount:
                print("Error: send action requires --currency, --address, and --amount")
                sys.exit(1)
            
            amount = Decimal(str(args.amount))
            fee = Decimal(str(args.fee)) if args.fee else None
            
            txid, error = wallet.send_transaction(args.currency, args.address, amount, fee)
            if txid:
                print(f"{args.currency} transaction successful!")
                print(f"Transaction ID: {txid}")
            else:
                print(f"{args.currency} transaction failed: {error}")
                sys.exit(1)

        elif args.action == "history":
            if not args.currency:
                print("Error: --currency is required for history action")
                sys.exit(1)
            
            transactions = wallet.get_transaction_history(args.currency, args.limit)
            if transactions:
                print(f"{args.currency} Transaction History:")
                print("-" * 60)
                for tx in transactions:
                    print(f"TXID: {tx.get('txid', 'N/A')}")
                    print(f"Amount: {tx.get('amount', 'N/A')} {args.currency}")
                    print(f"Type: {tx.get('type', 'N/A')}")
                    print(f"Confirmations: {tx.get('confirmations', 'N/A')}")
                    if tx.get('timestamp'):
                        print(f"Date: {tx['timestamp']}")
                    print("-" * 30)
            else:
                print(f"No {args.currency} transaction history available")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 