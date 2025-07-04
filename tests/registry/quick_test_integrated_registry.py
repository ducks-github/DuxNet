"""
Quick Test Script for Integrated Registry Service

A simple script to quickly verify the integrated registry works.
"""

import asyncio
import logging
import os
import tempfile
from duxos_registry.services.integrated_registry import IntegratedNodeRegistry
from duxos_registry.db.database import SessionLocal
from duxos_registry.db.init_db import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def quick_test():
    """Quick test of integrated registry functionality"""
    print("🚀 Quick Test: Integrated Registry Service")
    print("-" * 50)
    
    try:
        # Initialize database
        init_database()
        db = SessionLocal()
        
        print("✅ Database initialized")
        
        # Create integrated registry
        registry = IntegratedNodeRegistry(
            node_id="quick_test_node",
            db_session=db,
            p2p_listen_port=9338,
            p2p_broadcast_port=9339
        )
        
        print("✅ Registry created successfully")
        
        # Test basic registration without starting P2P
        result = registry.register_node(
            node_id="test_node_001",
            address="192.168.1.100:8080",
            capabilities=["gpu_compute", "storage"]
        )
        
        if result["success"]:
            print("✅ Node registration successful")
        else:
            print(f"❌ Node registration failed: {result['message']}")
            return False
        
        # Test node retrieval
        node = registry.get_node("test_node_001")
        if node:
            print(f"✅ Node retrieved: {node['node_id']} at {node['address']}")
            print(f"   Capabilities: {node['capabilities']}")
        else:
            print("❌ Node retrieval failed")
            return False
        
        # Test network stats
        stats = registry.get_network_stats()
        print(f"✅ Network stats: {stats['total_nodes']} total nodes")
        
        # Test capability statistics
        cap_stats = registry.get_capability_statistics()
        print(f"✅ Capability stats: {len(cap_stats)} capabilities")
        
        # Test status update
        status_result = registry.update_node_status("test_node_001", "busy")
        if status_result["success"]:
            print("✅ Status update successful")
        else:
            print(f"❌ Status update failed: {status_result['message']}")
        
        # Test reputation update
        rep_result = registry.update_node_reputation("test_node_001", 10.5)
        if rep_result["success"]:
            print("✅ Reputation update successful")
        else:
            print(f"❌ Reputation update failed: {rep_result['message']}")
        
        # Verify updates
        updated_node = registry.get_node("test_node_001")
        if updated_node:
            print(f"✅ Updated node - Status: {updated_node['status']}, Reputation: {updated_node['reputation']}")
        
        db.close()
        print("\n🎉 Quick test completed successfully!")
        print("The integrated registry service is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(quick_test())
