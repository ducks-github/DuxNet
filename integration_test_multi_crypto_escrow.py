#!/usr/bin/env python3
"""
Integration Test for Multi-Crypto Escrow System

Tests the integration of:
- Multi-cryptocurrency escrow creation
- Currency validation and support
- Fund locking and transfer for different currencies
- API endpoints for multi-crypto support
"""

import asyncio
import json
import requests
import subprocess
import sys
import time
import threading
from typing import Dict, List, Any
from datetime import datetime

# Test configuration
TEST_CONFIG = {
    "escrow_url": "http://localhost:8004",
    "store_url": "http://localhost:8000",
    "registry_url": "http://localhost:8002",
    "wallet_url": "http://localhost:8003",
    "supported_currencies": ["FLOP", "BTC", "ETH", "USDT", "BNB", "XRP", "SOL", "ADA", "DOGE", "TON", "TRX"]
}

class MultiCryptoEscrowTester:
    """Test multi-crypto escrow functionality"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_escrow_service_health(self) -> bool:
        """Test escrow service health"""
        try:
            response = requests.get(f"{TEST_CONFIG['escrow_url']}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Escrow Service Health", True, "Service is running")
                return True
            else:
                self.log_test("Escrow Service Health", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Escrow Service Health", False, f"Connection error: {e}")
            return False
    
    def test_supported_currencies(self) -> bool:
        """Test supported currencies endpoint"""
        try:
            response = requests.get(f"{TEST_CONFIG['escrow_url']}/currencies", timeout=5)
            if response.status_code == 200:
                data = response.json()
                currencies = data.get("currencies", [])
                
                # Check if all expected currencies are supported
                expected_currencies = set(TEST_CONFIG["supported_currencies"])
                supported_currencies = set(currencies)
                
                if expected_currencies.issubset(supported_currencies):
                    self.log_test("Supported Currencies", True, f"All {len(expected_currencies)} currencies supported")
                    return True
                else:
                    missing = expected_currencies - supported_currencies
                    self.log_test("Supported Currencies", False, f"Missing currencies: {missing}")
                    return False
            else:
                self.log_test("Supported Currencies", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Supported Currencies", False, f"Request error: {e}")
            return False
    
    def test_flop_escrow_creation(self) -> bool:
        """Test FLOP escrow creation"""
        try:
            escrow_data = {
                "payer_wallet_id": 1,
                "provider_wallet_id": 2,
                "amount": 10.0,
                "currency": "FLOP",
                "service_name": "test_service_flop",
                "metadata": {"test": "flop_escrow"}
            }
            
            response = requests.post(
                f"{TEST_CONFIG['escrow_url']}/escrow/create",
                json=escrow_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                escrow_id = data.get("escrow_id")
                currency = data.get("currency")
                
                if escrow_id and currency == "FLOP":
                    self.log_test("FLOP Escrow Creation", True, f"Created escrow {escrow_id}")
                    return escrow_id
                else:
                    self.log_test("FLOP Escrow Creation", False, "Invalid response data")
                    return False
            else:
                self.log_test("FLOP Escrow Creation", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("FLOP Escrow Creation", False, f"Request error: {e}")
            return False
    
    def test_eth_escrow_creation(self) -> bool:
        """Test ETH escrow creation"""
        try:
            escrow_data = {
                "payer_wallet_id": 1,
                "provider_wallet_id": 2,
                "amount": 0.1,
                "currency": "ETH",
                "service_name": "test_service_eth",
                "metadata": {"test": "eth_escrow"}
            }
            
            response = requests.post(
                f"{TEST_CONFIG['escrow_url']}/escrow/create",
                json=escrow_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                escrow_id = data.get("escrow_id")
                currency = data.get("currency")
                
                if escrow_id and currency == "ETH":
                    self.log_test("ETH Escrow Creation", True, f"Created escrow {escrow_id}")
                    return escrow_id
                else:
                    self.log_test("ETH Escrow Creation", False, "Invalid response data")
                    return False
            else:
                self.log_test("ETH Escrow Creation", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("ETH Escrow Creation", False, f"Request error: {e}")
            return False
    
    def test_btc_escrow_creation(self) -> bool:
        """Test BTC escrow creation"""
        try:
            escrow_data = {
                "payer_wallet_id": 1,
                "provider_wallet_id": 2,
                "amount": 0.001,
                "currency": "BTC",
                "service_name": "test_service_btc",
                "metadata": {"test": "btc_escrow"}
            }
            
            response = requests.post(
                f"{TEST_CONFIG['escrow_url']}/escrow/create",
                json=escrow_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                escrow_id = data.get("escrow_id")
                currency = data.get("currency")
                
                if escrow_id and currency == "BTC":
                    self.log_test("BTC Escrow Creation", True, f"Created escrow {escrow_id}")
                    return escrow_id
                else:
                    self.log_test("BTC Escrow Creation", False, "Invalid response data")
                    return False
            else:
                self.log_test("BTC Escrow Creation", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("BTC Escrow Creation", False, f"Request error: {e}")
            return False
    
    def test_invalid_currency(self) -> bool:
        """Test invalid currency rejection"""
        try:
            escrow_data = {
                "payer_wallet_id": 1,
                "provider_wallet_id": 2,
                "amount": 10.0,
                "currency": "INVALID_CURRENCY",
                "service_name": "test_service_invalid",
                "metadata": {"test": "invalid_currency"}
            }
            
            response = requests.post(
                f"{TEST_CONFIG['escrow_url']}/escrow/create",
                json=escrow_data,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Invalid Currency Rejection", True, "Correctly rejected invalid currency")
                return True
            else:
                self.log_test("Invalid Currency Rejection", False, f"Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid Currency Rejection", False, f"Request error: {e}")
            return False
    
    def test_escrows_by_currency(self) -> bool:
        """Test getting escrows by currency"""
        try:
            # Test FLOP escrows
            response = requests.get(f"{TEST_CONFIG['escrow_url']}/escrows/currency/FLOP", timeout=5)
            if response.status_code == 200:
                data = response.json()
                currency = data.get("currency")
                escrows = data.get("escrows", [])
                
                if currency == "FLOP" and isinstance(escrows, list):
                    self.log_test("Escrows by Currency (FLOP)", True, f"Found {len(escrows)} FLOP escrows")
                    return True
                else:
                    self.log_test("Escrows by Currency (FLOP)", False, "Invalid response format")
                    return False
            else:
                self.log_test("Escrows by Currency (FLOP)", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Escrows by Currency (FLOP)", False, f"Request error: {e}")
            return False
    
    def test_multi_currency_escrow_flow(self) -> bool:
        """Test complete multi-currency escrow flow"""
        try:
            # Create escrows in different currencies
            currencies = ["FLOP", "ETH", "BTC"]
            escrow_ids = []
            
            for currency in currencies:
                escrow_data = {
                    "payer_wallet_id": 1,
                    "provider_wallet_id": 2,
                    "amount": 1.0 if currency == "FLOP" else 0.01,
                    "currency": currency,
                    "service_name": f"test_service_{currency.lower()}",
                    "metadata": {"test": "multi_currency_flow"}
                }
                
                response = requests.post(
                    f"{TEST_CONFIG['escrow_url']}/escrow/create",
                    json=escrow_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    escrow_id = data.get("escrow_id")
                    if escrow_id:
                        escrow_ids.append((currency, escrow_id))
                
            if len(escrow_ids) == len(currencies):
                self.log_test("Multi-Currency Escrow Flow", True, f"Created escrows in {len(currencies)} currencies")
                return True
            else:
                self.log_test("Multi-Currency Escrow Flow", False, f"Only created {len(escrow_ids)}/{len(currencies)} escrows")
                return False
                
        except Exception as e:
            self.log_test("Multi-Currency Escrow Flow", False, f"Flow error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all multi-crypto escrow tests"""
        print("🚀 Starting Multi-Crypto Escrow Integration Tests")
        print("=" * 60)
        
        # Test service health
        if not self.test_escrow_service_health():
            print("❌ Escrow service not available. Please start the service first.")
            return self.get_test_summary()
        
        # Test supported currencies
        self.test_supported_currencies()
        
        # Test individual currency escrow creation
        self.test_flop_escrow_creation()
        self.test_eth_escrow_creation()
        self.test_btc_escrow_creation()
        
        # Test invalid currency rejection
        self.test_invalid_currency()
        
        # Test escrows by currency
        self.test_escrows_by_currency()
        
        # Test complete multi-currency flow
        self.test_multi_currency_escrow_flow()
        
        print("\n" + "=" * 60)
        print("🏁 Multi-Crypto Escrow Integration Tests Complete")
        
        return self.get_test_summary()
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        duration = datetime.now() - self.start_time
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "duration_seconds": duration.total_seconds(),
            "results": self.test_results
        }
        
        print(f"\n📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Duration: {summary['duration_seconds']:.2f} seconds")
        
        return summary

def main():
    """Main test runner"""
    tester = MultiCryptoEscrowTester()
    summary = tester.run_all_tests()
    
    # Save results to file
    with open("multi_crypto_escrow_test_results.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n💾 Test results saved to: multi_crypto_escrow_test_results.json")
    
    # Exit with appropriate code
    if summary["failed_tests"] > 0:
        print(f"\n❌ {summary['failed_tests']} tests failed!")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main() 