#!/usr/bin/env python3
"""
Integration Test for DuxOS Desktop Advanced Features

Tests the integration of:
- Multi-cryptocurrency wallet management
- Escrow management and monitoring
- Task engine management
- Daemon management
- Desktop GUI integration
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
    "store_url": "http://localhost:8000",
    "task_engine_url": "http://localhost:8001",
    "registry_url": "http://localhost:8002",
    "wallet_url": "http://localhost:8003",
    "escrow_url": "http://localhost:8004",
    "daemon_url": "http://localhost:8003",  # Daemon manager runs on wallet port
    "timeout": 30
}

class DesktopAdvancedIntegrationTest:
    """Integration test for desktop advanced features"""
    
    def __init__(self):
        self.results = []
        self.services = {}
        self.test_data = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log test message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        self.results.append({"timestamp": timestamp, "level": level, "message": message})
    
    def test_service_health(self) -> bool:
        """Test all services are running and healthy"""
        self.log("Testing service health...")
        
        services = {
            "Store": TEST_CONFIG["store_url"],
            "Task Engine": TEST_CONFIG["task_engine_url"],
            "Registry": TEST_CONFIG["registry_url"],
            "Wallet": TEST_CONFIG["wallet_url"],
            "Escrow": TEST_CONFIG["escrow_url"]
        }
        
        all_healthy = True
        for name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    self.log(f"✓ {name} service is healthy")
                else:
                    self.log(f"✗ {name} service returned status {response.status_code}", "ERROR")
                    all_healthy = False
            except Exception as e:
                self.log(f"✗ {name} service is not responding: {e}", "ERROR")
                all_healthy = False
        
        return all_healthy
    
    def test_multi_crypto_wallet(self) -> bool:
        """Test multi-cryptocurrency wallet functionality"""
        self.log("Testing multi-cryptocurrency wallet...")
        
        try:
            # Test getting all balances
            response = requests.get(f"{TEST_CONFIG['wallet_url']}/balances", timeout=TEST_CONFIG["timeout"])
            if response.status_code == 200:
                balances = response.json()
                self.log(f"✓ Retrieved balances for {len(balances)} currencies")
                
                # Test individual currency balance
                for currency in ["BTC", "ETH", "FLOP"]:
                    response = requests.get(f"{TEST_CONFIG['wallet_url']}/balance/{currency}", timeout=TEST_CONFIG["timeout"])
                    if response.status_code == 200:
                        balance_data = response.json()
                        self.log(f"✓ {currency} balance: {balance_data.get('balance', 0):.8f}")
                    else:
                        self.log(f"✗ Failed to get {currency} balance", "ERROR")
                        return False
                
                # Test new address generation
                for currency in ["BTC", "ETH", "FLOP"]:
                    response = requests.get(f"{TEST_CONFIG['wallet_url']}/new-address/{currency}", timeout=TEST_CONFIG["timeout"])
                    if response.status_code == 200:
                        address_data = response.json()
                        self.log(f"✓ Generated new {currency} address: {address_data.get('address', 'unknown')[:20]}...")
                    else:
                        self.log(f"✗ Failed to generate {currency} address", "ERROR")
                        return False
                
                return True
            else:
                self.log(f"✗ Failed to get balances: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Multi-crypto wallet test failed: {e}", "ERROR")
            return False
    
    def test_escrow_management(self) -> bool:
        """Test escrow management functionality"""
        self.log("Testing escrow management...")
        
        try:
            # Test getting active escrows
            response = requests.get(f"{TEST_CONFIG['escrow_url']}/escrows", timeout=TEST_CONFIG["timeout"])
            if response.status_code == 200:
                escrows = response.json()
                self.log(f"✓ Retrieved {len(escrows)} active escrows")
                
                # Test community fund info
                response = requests.get(f"{TEST_CONFIG['escrow_url']}/community-fund", timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    fund_info = response.json()
                    self.log(f"✓ Community fund balance: {fund_info.get('balance', 0):.8f} FLOP")
                    self.log(f"✓ Airdrop threshold: {fund_info.get('airdrop_threshold', 0):.8f} FLOP")
                else:
                    self.log(f"✗ Failed to get community fund info", "ERROR")
                    return False
                
                # Test creating a test escrow
                test_escrow = {
                    "service_name": "test_service",
                    "amount": 1.0,
                    "provider_address": "test_provider_123"
                }
                response = requests.post(f"{TEST_CONFIG['escrow_url']}/escrows", json=test_escrow, timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    escrow_data = response.json()
                    self.log(f"✓ Created test escrow: {escrow_data.get('id', 'unknown')}")
                    
                    # Store escrow ID for cleanup
                    self.test_data["test_escrow_id"] = escrow_data.get('id')
                else:
                    self.log(f"✗ Failed to create test escrow: {response.status_code}", "ERROR")
                    return False
                
                return True
            else:
                self.log(f"✗ Failed to get escrows: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Escrow management test failed: {e}", "ERROR")
            return False
    
    def test_task_engine(self) -> bool:
        """Test task engine functionality"""
        self.log("Testing task engine...")
        
        try:
            # Test getting tasks
            response = requests.get(f"{TEST_CONFIG['task_engine_url']}/tasks", timeout=TEST_CONFIG["timeout"])
            if response.status_code == 200:
                tasks = response.json()
                self.log(f"✓ Retrieved {len(tasks)} tasks")
                
                # Test getting statistics
                response = requests.get(f"{TEST_CONFIG['task_engine_url']}/statistics", timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    stats = response.json()
                    self.log(f"✓ Task engine statistics:")
                    self.log(f"  - Total tasks: {stats.get('total_tasks', 0)}")
                    self.log(f"  - Active tasks: {stats.get('active_tasks', 0)}")
                    self.log(f"  - Completed tasks: {stats.get('completed_tasks', 0)}")
                    self.log(f"  - Success rate: {stats.get('success_rate', 0):.1f}%")
                else:
                    self.log(f"✗ Failed to get task statistics", "ERROR")
                    return False
                
                # Test submitting a simple task
                test_task = {
                    "task_type": "API_CALL",
                    "service_name": "test_service",
                    "code": "print('Hello, World!')",
                    "payment_amount": 0.1
                }
                response = requests.post(f"{TEST_CONFIG['task_engine_url']}/tasks", json=test_task, timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    task_data = response.json()
                    self.log(f"✓ Submitted test task: {task_data.get('task_id', 'unknown')}")
                    
                    # Store task ID for cleanup
                    self.test_data["test_task_id"] = task_data.get('task_id')
                else:
                    self.log(f"✗ Failed to submit test task: {response.status_code}", "ERROR")
                    return False
                
                return True
            else:
                self.log(f"✗ Failed to get tasks: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Task engine test failed: {e}", "ERROR")
            return False
    
    def test_daemon_management(self) -> bool:
        """Test daemon management functionality"""
        self.log("Testing daemon management...")
        
        try:
            # Test getting daemon status
            response = requests.get(f"{TEST_CONFIG['daemon_url']}/daemons/status", timeout=TEST_CONFIG["timeout"])
            if response.status_code == 200:
                daemons = response.json()
                self.log(f"✓ Retrieved status for {len(daemons)} daemons")
                
                for daemon in daemons:
                    self.log(f"  - {daemon.get('name', 'unknown')}: {daemon.get('status', 'unknown')}")
                
                # Test daemon configuration
                test_config = {
                    "config_path": "/tmp/test_config.conf",
                    "data_dir": "/tmp/test_data",
                    "rpc_port": 8332
                }
                response = requests.post(f"{TEST_CONFIG['daemon_url']}/daemons/config", json=test_config, timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    self.log("✓ Daemon configuration saved")
                else:
                    self.log(f"✗ Failed to save daemon configuration: {response.status_code}", "ERROR")
                    return False
                
                return True
            else:
                self.log(f"✗ Failed to get daemon status: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"✗ Daemon management test failed: {e}", "ERROR")
            return False
    
    def test_desktop_gui_integration(self) -> bool:
        """Test desktop GUI integration with advanced features"""
        self.log("Testing desktop GUI integration...")
        
        try:
            # Test that the desktop GUI can be imported
            import sys
            import os
            
            # Add the desktop module to path
            desktop_path = os.path.join(os.getcwd(), "duxnet_desktop")
            if desktop_path not in sys.path:
                sys.path.insert(0, desktop_path)
            
            # Test importing advanced features
            from ui.advanced_features import (
                MultiCryptoWalletWidget,
                EscrowManagementWidget,
                TaskEngineWidget,
                DaemonManagerWidget,
                AdvancedFeaturesTab
            )
            
            self.log("✓ Successfully imported advanced features modules")
            
            # Test client classes
            from ui.advanced_features import EscrowClient, TaskClient, DaemonClient
            
            escrow_client = EscrowClient()
            task_client = TaskClient()
            daemon_client = DaemonClient()
            
            self.log("✓ Successfully created client instances")
            
            return True
            
        except Exception as e:
            self.log(f"✗ Desktop GUI integration test failed: {e}", "ERROR")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        self.log("Cleaning up test data...")
        
        try:
            # Clean up test escrow
            if "test_escrow_id" in self.test_data:
                escrow_id = self.test_data["test_escrow_id"]
                response = requests.delete(f"{TEST_CONFIG['escrow_url']}/escrows/{escrow_id}", timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    self.log(f"✓ Cleaned up test escrow: {escrow_id}")
                else:
                    self.log(f"✗ Failed to clean up test escrow: {escrow_id}", "WARNING")
            
            # Clean up test task
            if "test_task_id" in self.test_data:
                task_id = self.test_data["test_task_id"]
                response = requests.post(f"{TEST_CONFIG['task_engine_url']}/tasks/{task_id}/cancel", timeout=TEST_CONFIG["timeout"])
                if response.status_code == 200:
                    self.log(f"✓ Cancelled test task: {task_id}")
                else:
                    self.log(f"✗ Failed to cancel test task: {task_id}", "WARNING")
                    
        except Exception as e:
            self.log(f"✗ Cleanup failed: {e}", "WARNING")
    
    def run_all_tests(self) -> bool:
        """Run all integration tests"""
        self.log("=" * 60)
        self.log("Starting DuxOS Desktop Advanced Features Integration Test")
        self.log("=" * 60)
        
        test_results = []
        
        # Test 1: Service Health
        self.log("\n1. Testing Service Health")
        test_results.append(("Service Health", self.test_service_health()))
        
        # Test 2: Multi-Crypto Wallet
        self.log("\n2. Testing Multi-Cryptocurrency Wallet")
        test_results.append(("Multi-Crypto Wallet", self.test_multi_crypto_wallet()))
        
        # Test 3: Escrow Management
        self.log("\n3. Testing Escrow Management")
        test_results.append(("Escrow Management", self.test_escrow_management()))
        
        # Test 4: Task Engine
        self.log("\n4. Testing Task Engine")
        test_results.append(("Task Engine", self.test_task_engine()))
        
        # Test 5: Daemon Management
        self.log("\n5. Testing Daemon Management")
        test_results.append(("Daemon Management", self.test_daemon_management()))
        
        # Test 6: Desktop GUI Integration
        self.log("\n6. Testing Desktop GUI Integration")
        test_results.append(("Desktop GUI Integration", self.test_desktop_gui_integration()))
        
        # Cleanup
        self.log("\n7. Cleanup")
        self.cleanup_test_data()
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("Integration Test Summary")
        self.log("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✓ PASSED" if result else "✗ FAILED"
            self.log(f"{test_name}: {status}")
            if result:
                passed += 1
        
        self.log(f"\nOverall Result: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! Desktop advanced features are working correctly.")
        else:
            self.log("⚠️  Some tests failed. Please check the logs above for details.")
        
        return passed == total
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a detailed test report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "test_config": TEST_CONFIG,
            "results": self.results,
            "test_data": self.test_data
        }


def main():
    """Main test runner"""
    print("DuxOS Desktop Advanced Features Integration Test")
    print("=" * 60)
    
    # Check if services are running
    print("Checking if required services are running...")
    
    test = DesktopAdvancedIntegrationTest()
    success = test.run_all_tests()
    
    # Generate report
    report = test.generate_report()
    
    # Save report
    with open("desktop_advanced_integration_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved to: desktop_advanced_integration_report.json")
    
    if success:
        print("\n✅ Integration test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 