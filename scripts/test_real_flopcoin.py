#!/usr/bin/env python3
"""
Test Real Flopcoin Integration

This script tests the integration with the real Flopcoin Core daemon.
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import json

from duxos_registry.services.wallet_service import FlopcoinWalletService


def test_flopcoin_integration():
    """Test the real Flopcoin integration"""
    print("🚀 Testing Real Flopcoin Integration")
    print("=" * 50)

    try:
        # Initialize the wallet service
        print("📡 Connecting to Flopcoin Core...")
        wallet_service = FlopcoinWalletService()
        print("✅ Connected to Flopcoin Core")

        # Test 1: Get wallet info
        print("\n📊 Getting wallet information...")
        wallet_info = wallet_service.get_wallet_info()
        print(f"✅ Wallet Info:")
        print(f"   Balance: {wallet_info['balance']} FLOP")
        print(f"   Version: {wallet_info['version']}")
        print(f"   Blocks: {wallet_info['blocks']}")
        print(f"   Connections: {wallet_info['connections']}")

        # Test 2: Get balance
        print("\n💰 Getting balance...")
        balance = wallet_service.get_balance()
        print(f"✅ Balance:")
        print(f"   Confirmed: {balance['confirmed']} FLOP")
        print(f"   Unconfirmed: {balance['unconfirmed']} FLOP")
        print(f"   Total: {balance['total']} FLOP")

        # Test 3: Generate new address
        print("\n📍 Generating new address...")
        new_address = wallet_service.get_new_address("test_account")
        print(f"✅ New Address: {new_address['address']}")
        print(f"   Account: {new_address['account']}")
        print(f"   Type: {new_address['type']}")

        # Test 4: Get addresses
        print("\n📋 Getting addresses...")
        addresses = wallet_service.get_addresses("test_account")
        print(f"✅ Found {len(addresses)} addresses")
        for addr in addresses[:3]:  # Show first 3
            print(f"   {addr['address']} (valid: {addr['is_valid']}, mine: {addr['is_mine']})")

        # Test 5: Get transaction history
        print("\n📜 Getting transaction history...")
        history = wallet_service.get_transaction_history(count=5)
        print(f"✅ Found {len(history)} recent transactions")
        for tx in history[:3]:  # Show first 3
            print(f"   {tx['txid'][:16]}... - {tx['amount']} FLOP ({tx['category']})")

        # Test 6: Get network info
        print("\n🌐 Getting network information...")
        network_info = wallet_service.get_network_info()
        print(f"✅ Network Info:")
        print(f"   Version: {network_info['version']}")
        print(f"   Protocol: {network_info['protocol_version']}")
        print(f"   Connections: {network_info['connections']}")
        print(f"   Testnet: {network_info['testnet']}")

        # Test 7: Get blockchain info
        print("\n⛓️ Getting blockchain information...")
        blockchain_info = wallet_service.get_blockchain_info()
        print(f"✅ Blockchain Info:")
        print(f"   Chain: {blockchain_info['chain']}")
        print(f"   Blocks: {blockchain_info['blocks']}")
        print(f"   Headers: {blockchain_info['headers']}")
        print(f"   Verification Progress: {blockchain_info['verification_progress']:.2%}")

        # Test 8: Estimate fee
        print("\n💸 Estimating transaction fee...")
        fee_estimate = wallet_service.estimate_fee(6)
        print(f"✅ Fee Estimate:")
        print(f"   Blocks: {fee_estimate['blocks']}")
        print(f"   Fee Rate: {fee_estimate['fee_rate']}")
        print(f"   Estimated Fee: {fee_estimate['estimated_fee']} FLOP")

        # Test 9: Get mempool info
        print("\n📦 Getting mempool information...")
        mempool_info = wallet_service.get_mempool_info()
        print(f"✅ Mempool Info:")
        print(f"   Size: {mempool_info['size']} transactions")
        print(f"   Bytes: {mempool_info['bytes']}")
        print(f"   Usage: {mempool_info['usage']}")
        print(f"   Min Fee: {mempool_info['mempool_min_fee']}")

        print("\n🎉 All tests passed! Real Flopcoin integration is working correctly.")

        # Summary
        print("\n📋 Integration Summary:")
        print(f"   ✅ RPC Connection: Working")
        print(f"   ✅ Wallet Operations: Working")
        print(f"   ✅ Address Generation: Working")
        print(f"   ✅ Transaction History: Working")
        print(f"   ✅ Network Info: Working")
        print(f"   ✅ Blockchain Info: Working")
        print(f"   ✅ Fee Estimation: Working")
        print(f"   ✅ Mempool Info: Working")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_wallet_operations():
    """Test specific wallet operations"""
    print("\n🔧 Testing Wallet Operations")
    print("=" * 30)

    try:
        wallet_service = FlopcoinWalletService()

        # Test address validation
        print("🔍 Testing address validation...")
        test_address = wallet_service.get_new_address("validation_test")
        validation = wallet_service._make_rpc_call("validateaddress", [test_address["address"]])
        print(f"✅ Address validation: {validation.get('isvalid', False)}")

        # Test backup (if wallet has funds)
        print("💾 Testing wallet backup...")
        try:
            backup_result = wallet_service.backup_wallet("/tmp/duxos_wallet_backup.dat")
            print(f"✅ Wallet backup: {backup_result['success']}")
        except Exception as e:
            print(f"⚠️ Wallet backup failed (expected if no wallet.dat): {e}")

        return True

    except Exception as e:
        print(f"❌ Wallet operations test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Real Flopcoin Integration Test")
    print("=" * 50)

    # Test basic integration
    integration_success = test_flopcoin_integration()

    # Test wallet operations
    operations_success = test_wallet_operations()

    if integration_success and operations_success:
        print("\n🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("1. The real Flopcoin integration is working")
        print("2. You can now use the wallet API with live transactions")
        print("3. Consider testing with small amounts first")
        print("4. Monitor the blockchain sync status")
    else:
        print("\n❌ Some tests failed. Please check the Flopcoin daemon status.")
        sys.exit(1)
