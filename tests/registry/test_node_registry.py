import os
import tempfile
import pytest
from duxos.registry.models.node import Node, NodeCapabilities
from duxos.registry.services.node_registry import NodeRegistry

@pytest.fixture
def temp_persistence_path():
    """Create a temporary file path for node persistence."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    yield temp_path
    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def sample_node():
    """Create a sample node for testing."""
    return Node(
        wallet_address='test_wallet_123',
        ip_address='192.168.1.100',
        hostname='test-node',
        capabilities=NodeCapabilities(
            cpu_cores=4,
            memory_gb=16.0,
            storage_gb=500.0,
            gpu_enabled=True
        )
    )

def test_node_registry_initialization(temp_persistence_path):
    """Test initializing NodeRegistry with persistence."""
    registry = NodeRegistry(persistence_path=temp_persistence_path)
    assert registry is not None

def test_register_node(sample_node):
    """Test registering a new node."""
    registry = NodeRegistry()
    node_id = registry.register_node(sample_node)
    
    assert node_id is not None
    assert node_id == sample_node.id
    
    retrieved_node = registry.get_node(node_id)
    assert retrieved_node is not None
    assert retrieved_node.wallet_address == sample_node.wallet_address

def test_register_duplicate_node(sample_node):
    """Test registering a node with an existing wallet address."""
    registry = NodeRegistry()
    
    # First registration
    first_node_id = registry.register_node(sample_node)
    
    # Second registration with same wallet address
    second_node = Node(
        wallet_address='test_wallet_123',
        ip_address='192.168.1.101',
        hostname='test-node-2'
    )
    second_node_id = registry.register_node(second_node)
    
    # Should update the existing node
    assert first_node_id == second_node_id
    
    retrieved_node = registry.get_node(first_node_id)
    assert retrieved_node is not None
    assert retrieved_node.ip_address == '192.168.1.101'
    assert retrieved_node.hostname == 'test-node-2'

def test_deregister_node(sample_node):
    """Test deregistering a node."""
    registry = NodeRegistry()
    node_id = registry.register_node(sample_node)
    
    # Deregister the node
    result = registry.deregister_node(node_id)
    assert result is True
    
    # Try to retrieve the node
    retrieved_node = registry.get_node(node_id)
    assert retrieved_node is None

def test_get_node_by_wallet_address(sample_node):
    """Test retrieving a node by wallet address."""
    registry = NodeRegistry()
    registry.register_node(sample_node)
    
    retrieved_node = registry.get_node_by_wallet_address('test_wallet_123')
    assert retrieved_node is not None
    assert retrieved_node.wallet_address == 'test_wallet_123'

def test_update_node_health(sample_node):
    """Test updating node health metrics."""
    registry = NodeRegistry()
    node_id = registry.register_node(sample_node)
    
    # Update health
    result = registry.update_node_health(node_id, 
                                         load_average=1.5, 
                                         memory_usage=50.0, 
                                         disk_usage=30.0)
    assert result is True
    
    updated_node = registry.get_node(node_id)
    assert updated_node is not None
    assert updated_node.health.load_average == 1.5
    assert updated_node.health.memory_usage == 50.0
    assert updated_node.health.disk_usage == 30.0

def test_update_node_reputation(sample_node):
    """Test updating node reputation."""
    registry = NodeRegistry()
    node_id = registry.register_node(sample_node)
    
    # Initial reputation
    initial_reputation = sample_node.reputation_score
    
    # Update reputation with successful task
    result = registry.update_node_reputation(node_id, task_success=True)
    assert result is True
    
    updated_node = registry.get_node(node_id)
    assert updated_node is not None
    assert updated_node.reputation_score > initial_reputation
    assert updated_node.total_tasks_completed == 1

def test_list_nodes(sample_node):
    """Test listing nodes with various filters."""
    registry = NodeRegistry()
    
    # Create multiple nodes with different capabilities
    node1 = sample_node
    node2 = Node(
        wallet_address='test_wallet_456',
        ip_address='192.168.1.101',
        capabilities=NodeCapabilities(
            cpu_cores=2,
            memory_gb=8.0,
            storage_gb=250.0
        )
    )
    
    # Register nodes
    registry.register_node(node1)
    registry.register_node(node2)
    
    # List all nodes
    all_nodes = registry.list_nodes()
    assert len(all_nodes) == 2
    
    # List nodes with minimum capabilities
    min_caps = NodeCapabilities(
        cpu_cores=4,
        memory_gb=16.0,
        storage_gb=500.0
    )
    filtered_nodes = registry.list_nodes(min_capabilities=min_caps)
    assert len(filtered_nodes) == 1
    assert filtered_nodes[0].id == node1.id

def test_persistence(sample_node, temp_persistence_path):
    """Test node registry persistence."""
    # First registry instance
    registry1 = NodeRegistry(persistence_path=temp_persistence_path)
    registry1.register_node(sample_node)
    
    # Second registry instance (should load from persistence)
    registry2 = NodeRegistry(persistence_path=temp_persistence_path)
    
    # Check if node was persisted and loaded
    loaded_node = registry2.get_node_by_wallet_address('test_wallet_123')
    assert loaded_node is not None
    assert loaded_node.wallet_address == sample_node.wallet_address 