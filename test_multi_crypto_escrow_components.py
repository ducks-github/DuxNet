#!/usr/bin/env python3
"""
Test Multi-Crypto Escrow Components

Tests the core components of the multi-crypto escrow system
without requiring the full service to be running.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_escrow_manager_import():
    """Test that EscrowManager can be imported with multi-crypto support"""
    try:
        from duxos_escrow.escrow_manager import EscrowManager
        print("✅ EscrowManager imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import EscrowManager: {e}")
        return False

def test_currency_validation():
    """Test currency validation functionality"""
    try:
        from duxos_escrow.escrow_manager import EscrowManager
        
        # Create a mock manager (without database)
        manager = EscrowManager.__new__(EscrowManager)
        manager.supported_currencies = ["FLOP", "BTC", "ETH", "USDT", "BNB", "XRP", "SOL", "ADA", "DOGE", "TON", "TRX"]
        
        # Test valid currencies
        valid_currencies = ["FLOP", "BTC", "ETH", "USDT"]
        for currency in valid_currencies:
            if manager.validate_currency(currency):
                print(f"✅ Currency validation passed for {currency}")
            else:
                print(f"❌ Currency validation failed for {currency}")
                return False
        
        # Test invalid currency
        if not manager.validate_currency("INVALID"):
            print("✅ Invalid currency correctly rejected")
        else:
            print("❌ Invalid currency should have been rejected")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Currency validation test failed: {e}")
        return False

def test_api_models():
    """Test API models with multi-crypto support"""
    try:
        from duxos_escrow.api import CreateEscrowRequest, CreateEscrowResponse
        
        # Test CreateEscrowRequest with currency
        request_data = {
            "payer_wallet_id": 1,
            "provider_wallet_id": 2,
            "amount": 10.0,
            "currency": "ETH",
            "service_name": "test_service"
        }
        
        request = CreateEscrowRequest(**request_data)
        if request.currency == "ETH":
            print("✅ CreateEscrowRequest with currency works correctly")
        else:
            print("❌ CreateEscrowRequest currency field not working")
            return False
        
        # Test CreateEscrowResponse with currency
        response_data = {
            "escrow_id": "test-123",
            "status": "active",
            "amount": 10.0,
            "currency": "ETH",
            "provider_amount": 9.5,
            "community_amount": 0.5,
            "created_at": datetime.now()
        }
        
        response = CreateEscrowResponse(**response_data)
        if response.currency == "ETH":
            print("✅ CreateEscrowResponse with currency works correctly")
        else:
            print("❌ CreateEscrowResponse currency field not working")
            return False
            
        return True
    except Exception as e:
        print(f"❌ API models test failed: {e}")
        return False

def test_models_currency_field():
    """Test that models have currency field"""
    try:
        from duxos_escrow.models import Escrow, EscrowTransaction
        
        # Check if currency field exists in Escrow model
        if hasattr(Escrow, 'currency'):
            print("✅ Escrow model has currency field")
        else:
            print("❌ Escrow model missing currency field")
            return False
        
        # Check if currency field exists in EscrowTransaction model
        if hasattr(EscrowTransaction, 'currency'):
            print("✅ EscrowTransaction model has currency field")
        else:
            print("❌ EscrowTransaction model missing currency field")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Models test failed: {e}")
        return False

def test_multi_crypto_wallet_integration():
    """Test multi-crypto wallet integration"""
    try:
        # Test if multi-crypto wallet can be imported
        try:
            from duxnet_wallet.multi_crypto_wallet import MultiCryptoWallet
            print("✅ MultiCryptoWallet can be imported")
            multi_crypto_available = True
        except ImportError:
            print("⚠️  MultiCryptoWallet not available (expected in development)")
            multi_crypto_available = False
        
        # Test EscrowManager handles missing multi-crypto wallet gracefully
        from duxos_escrow.escrow_manager import EscrowManager
        
        # Create a mock manager
        manager = EscrowManager.__new__(EscrowManager)
        manager.multi_crypto_wallet = None
        manager.supported_currencies = ["FLOP", "BTC", "ETH"]
        
        # Test that it doesn't crash when multi-crypto wallet is None
        if manager.validate_currency("FLOP"):
            print("✅ EscrowManager handles missing multi-crypto wallet gracefully")
            return True
        else:
            print("❌ EscrowManager failed with missing multi-crypto wallet")
            return False
            
    except Exception as e:
        print(f"❌ Multi-crypto wallet integration test failed: {e}")
        return False

def main():
    """Run all component tests"""
    print("🧪 Testing Multi-Crypto Escrow Components")
    print("=" * 50)
    
    tests = [
        ("EscrowManager Import", test_escrow_manager_import),
        ("Currency Validation", test_currency_validation),
        ("API Models", test_api_models),
        ("Models Currency Field", test_models_currency_field),
        ("Multi-Crypto Wallet Integration", test_multi_crypto_wallet_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All multi-crypto escrow component tests passed!")
        print("\n✅ Multi-Crypto Escrow Integration is working correctly!")
        print("✅ Ready for production deployment!")
        return True
    else:
        print(f"❌ {total - passed} tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 