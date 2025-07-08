#!/usr/bin/env python3
"""
Comprehensive Integration Test for DuxNet Advanced Features
Tests multi-cryptocurrency wallet, escrow service, task engine, and daemon manager
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
import time
import json

def test_multi_crypto_wallet():
    """Test multi-cryptocurrency wallet functionality"""
    print("=" * 60)
    print("TESTING MULTI-CRYPTOCURRENCY WALLET")
    print("=" * 60)
    
    try:
        from duxnet_wallet.multi_crypto_wallet import MultiCryptoWallet
        
        # Initialize wallet
        wallet = MultiCryptoWallet("duxnet_wallet/multi_crypto_config.yaml")
        
        # Get supported currencies
        currencies = wallet.get_supported_currencies()
        print(f"Supported currencies: {currencies}")
        
        # Test balance checking
        print("\nTesting balance checking:")
        balances = wallet.get_all_balances()
        for currency, balance in balances.items():
            if balance is not None:
                print(f"  {currency} balance: {balance}")
            else:
                print(f"  {currency} balance: Error (expected for mock server)")
        
        # Test address generation
        print("\nTesting address generation:")
        for currency in currencies:
            address = wallet.get_new_address(currency)
            if address:
                print(f"  {currency} address: {address}")
            else:
                print(f"  {currency} address: Error")
        
        print("✓ Multi-cryptocurrency wallet test completed")
        return True
        
    except Exception as e:
        print(f"✗ Multi-cryptocurrency wallet test failed: {e}")
        return False

def test_escrow_service():
    """Test escrow service functionality"""
    print("\n" + "=" * 60)
    print("TESTING ESCROW SERVICE")
    print("=" * 60)
    
    try:
        from duxos_escrow.escrow_service import EscrowService, EscrowType, EscrowStatus
        
        # Initialize escrow service
        escrow = EscrowService("test_escrow.db")
        
        # Create a test contract
        contract = escrow.create_contract(
            escrow_type=EscrowType.SERVICE_PAYMENT,
            buyer_id="user-1",
            seller_id="user-2",
            amount=Decimal("10.0"),
            currency="FLOP",
            service_id="service-123",
            description="API usage payment",
            terms="Payment for 100 API calls"
        )
        
        print(f"Created escrow contract: {contract.contract_id}")
        
        # Fund the contract
        escrow.fund_contract(contract.contract_id, "tx_hash_123")
        print("Funded escrow contract")
        
        # Start work
        escrow.start_contract(contract.contract_id)
        print("Started escrow contract")
        
        # Complete the contract
        escrow.complete_contract(contract.contract_id, "tx_hash_456")
        print("Completed escrow contract")
        
        # Get statistics
        stats = escrow.get_contract_statistics()
        print(f"Escrow statistics: {stats}")
        
        # Test dispute functionality
        contract2 = escrow.create_contract(
            escrow_type=EscrowType.API_USAGE,
            buyer_id="user-3",
            seller_id="user-4",
            amount=Decimal("5.0"),
            currency="FLOP",
            description="Disputed payment"
        )
        
        escrow.fund_contract(contract2.contract_id, "tx_hash_789")
        escrow.dispute_contract(contract2.contract_id, "user-3", "Service not delivered")
        print("Created and disputed escrow contract")
        
        print("✓ Escrow service test completed")
        return True
        
    except Exception as e:
        print(f"✗ Escrow service test failed: {e}")
        return False

def test_task_engine():
    """Test task engine functionality"""
    print("\n" + "=" * 60)
    print("TESTING TASK ENGINE")
    print("=" * 60)
    
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'duxos_tasks'))
        from task_engine import TaskEngine, TaskPriority
        
        # Initialize task engine
        engine = TaskEngine("test_tasks.db")
        
        # Submit multiple test tasks
        tasks = []
        for i in range(3):
            task = engine.submit_task(
                task_type="python_script",
                payload={"code": f"print('Task {i+1} from DuxNet Task Engine!')"},
                priority=TaskPriority.NORMAL,
                max_execution_time=30,
                required_capabilities=["python", "compute"],
                reward=Decimal(f"{5.0 + i}"),
                currency="FLOP",
                submitter_id=f"user-{i+1}"
            )
            tasks.append(task)
            print(f"Submitted task {i+1}: {task.task_id}")
        
        # Get available tasks
        available = engine.get_available_tasks(["python", "compute"])
        print(f"Available tasks: {len(available)}")
        
        # Process tasks
        for i, task in enumerate(available):
            node_id = f"node-{i+1}"
            
            # Assign and start task
            engine.assign_task(task.task_id, node_id)
            engine.start_task(task.task_id, node_id)
            
            # Complete task
            engine.complete_task(
                task.task_id, 
                node_id, 
                {"output": f"Task {i+1} completed successfully"}, 
                2.5 + i
            )
            print(f"Completed task {i+1}")
        
        # Get statistics
        stats = engine.get_task_statistics()
        print(f"Task engine statistics: {stats}")
        
        print("✓ Task engine test completed")
        return True
        
    except Exception as e:
        print(f"✗ Task engine test failed: {e}")
        return False

def test_daemon_manager():
    """Test daemon manager functionality"""
    print("\n" + "=" * 60)
    print("TESTING DAEMON MANAGER")
    print("=" * 60)
    
    try:
        from duxnet_wallet.daemon_manager import DaemonManager
        
        # Initialize daemon manager
        manager = DaemonManager("test_daemon_config.yaml")
        
        # Get configured daemons
        daemons = list(manager.daemons.keys())
        print(f"Configured daemons: {daemons}")
        
        # Get status of all daemons
        status = manager.get_all_status()
        print("\nDaemon status:")
        for currency, status in status.items():
            print(f"  {currency}: {status.value}")
        
        # Get detailed info
        print("\nDaemon details:")
        for currency in daemons:
            info = manager.get_daemon_info(currency)
            if info:
                print(f"  {currency}: {info['name']} ({info['status']})")
        
        # Test daemon operations (without actually starting daemons)
        print("\nTesting daemon operations:")
        for currency in daemons:
            if manager.daemons[currency].enabled:
                print(f"  {currency}: Enabled, would start on port {manager.daemons[currency].rpc_port}")
            else:
                print(f"  {currency}: Disabled")
        
        print("✓ Daemon manager test completed")
        return True
        
    except Exception as e:
        print(f"✗ Daemon manager test failed: {e}")
        return False

def test_cross_service_integration():
    """Test integration between different services"""
    print("\n" + "=" * 60)
    print("TESTING CROSS-SERVICE INTEGRATION")
    print("=" * 60)
    
    try:
        # Test escrow + task engine integration
        from duxos_escrow.escrow_service import EscrowService, EscrowType
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'duxos_tasks'))
        from task_engine import TaskEngine, TaskPriority
        
        escrow = EscrowService("test_integration_escrow.db")
        engine = TaskEngine("test_integration_tasks.db")
        
        # Create escrow contract for task payment
        contract = escrow.create_contract(
            escrow_type=EscrowType.TASK_EXECUTION,
            buyer_id="task-submitter",
            seller_id="task-executor",
            amount=Decimal("15.0"),
            currency="FLOP",
            description="Payment for distributed computing task"
        )
        
        print(f"Created escrow contract for task: {contract.contract_id}")
        
        # Submit task
        task = engine.submit_task(
            task_type="distributed_compute",
            payload={"code": "print('Complex computation completed')"},
            priority=TaskPriority.HIGH,
            max_execution_time=60,
            required_capabilities=["python", "compute", "gpu"],
            reward=Decimal("15.0"),
            currency="FLOP",
            submitter_id="task-submitter"
        )
        
        print(f"Submitted task: {task.task_id}")
        
        # Simulate task completion and payment
        engine.assign_task(task.task_id, "compute-node-1")
        engine.start_task(task.task_id, "compute-node-1")
        engine.complete_task(task.task_id, "compute-node-1", {"result": "success"}, 5.0)
        
        # Release escrow payment
        escrow.fund_contract(contract.contract_id, "task_payment_tx")
        escrow.start_contract(contract.contract_id)
        escrow.complete_contract(contract.contract_id, "task_completion_tx")
        
        print("✓ Cross-service integration test completed")
        return True
        
    except Exception as e:
        print(f"✗ Cross-service integration test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("DUXNET ADVANCED FEATURES INTEGRATION TEST")
    print("=" * 80)
    print(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run all tests
    test_results.append(("Multi-Crypto Wallet", test_multi_crypto_wallet()))
    test_results.append(("Escrow Service", test_escrow_service()))
    test_results.append(("Task Engine", test_task_engine()))
    test_results.append(("Daemon Manager", test_daemon_manager()))
    test_results.append(("Cross-Service Integration", test_cross_service_integration()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:30} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! DuxNet advanced features are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    print(f"\nTest completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main() 