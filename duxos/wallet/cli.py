import argparse
import sys
from .wallet import FlopcoinWallet

def main():
    parser = argparse.ArgumentParser(description="DuxOS Flop Coin Wallet CLI")
    parser.add_argument('action', choices=['new-address', 'balance', 'send'], 
                        help='Wallet action to perform')
    parser.add_argument('--address', help='Recipient address for send action')
    parser.add_argument('--amount', type=float, help='Amount to send for send action')
    parser.add_argument('--config', help='Path to custom config file', default=None)

    args = parser.parse_args()

    try:
        wallet = FlopcoinWallet(config_path=args.config)

        if args.action == 'new-address':
            address = wallet.get_new_address()
            print(f"New Flopcoin Address: {address}")

        elif args.action == 'balance':
            balance = wallet.get_balance()
            print(f"Current Balance: {balance} Flop Coin")

        elif args.action == 'send':
            if not args.address or not args.amount:
                print("Error: Send action requires both --address and --amount")
                sys.exit(1)
            
            txid, error = wallet.send_to_address(args.address, args.amount)
            if txid:
                print(f"Transaction successful! TXID: {txid}")
            else:
                print(f"Transaction failed: {error}")
                sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 