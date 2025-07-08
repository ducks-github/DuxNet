# DuxOS Node Registry Module

## Overview

The Node Registry module is a critical component of the Dux OS ecosystem, responsible for managing node information, health tracking, and reputation scoring across the decentralized network.

## Key Features

- 🌐 Node Registration and Discovery
- 📊 Health Monitoring
- 🏆 Reputation Scoring
- 💾 Persistent Storage
- 🔍 Advanced Node Filtering

## Core Components

### 1. Node Model
Represents a node in the Dux OS network with:
- Unique Identifier
- Wallet Address
- IP Address
- Computational Capabilities
- Health Metrics
- Reputation Score

### 2. Node Registry Service
Manages node lifecycle and provides advanced querying capabilities:
- Register/Deregister Nodes
- Update Node Health
- Track Node Reputation
- Filter Nodes by Capabilities

## Usage Examples

### Basic Node Registration

```python
from duxnet.registry.models.node import Node, NodeCapabilities
from duxnet.registry.services.node_registry import NodeRegistry

# Create a node registry
registry = NodeRegistry(persistence_path='/var/lib/duxnet/nodes.json')

# Create a node
node = Node(
    wallet_address='your_wallet_address',
    ip_address='192.168.1.100',
    capabilities=NodeCapabilities(
        cpu_cores=4,
        memory_gb=16.0,
        storage_gb=500.0,
        gpu_enabled=True
    )
)

# Register the node
node_id = registry.register_node(node)
```

### Node Health Monitoring

```python
# Update node health metrics
registry.update_node_health(
    node_id, 
    load_average=1.5, 
    memory_usage=50.0, 
    disk_usage=30.0
)
```

### Node Discovery and Filtering

```python
# List all healthy nodes with minimum capabilities
min_capabilities = NodeCapabilities(
    cpu_cores=4,
    memory_gb=8.0,
    storage_gb=250.0
)

suitable_nodes = registry.list_nodes(
    min_reputation=3.0,  # Minimum reputation score
    only_healthy=True,   # Only return healthy nodes
    min_capabilities=min_capabilities
)
```

## Configuration

### Persistence
- Nodes can be persisted to a JSON file
- Automatically loads nodes on initialization
- Supports manual saving and loading

### Health Thresholds
- Configurable health criteria
- Tracks load average, memory, and disk usage
- Automatic health status determination

## Security Considerations

- Unique node identification
- Reputation scoring to discourage malicious behavior
- Persistent storage with optional encryption

## Performance

- O(1) node lookup by ID
- O(n) node filtering with reputation and capability checks
- Efficient memory usage with lazy loading

## Future Enhancements

- Distributed node discovery
- Enhanced anti-Sybil mechanisms
- Machine learning-based reputation scoring
- Encrypted node metadata

## Contributing

1. Improve node discovery algorithms
2. Enhance reputation scoring mechanisms
3. Add more comprehensive health checks
4. Implement advanced filtering capabilities

## Dependencies

- Python 3.9+
- `dataclasses`
- `typing`
- `uuid`
- `logging`

## License

Part of the Dux OS project. See project LICENSE for details. 