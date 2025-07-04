import os
import tempfile
import json
import pytest
from unittest.mock import MagicMock

from duxos.registry.cli import NodeRegistryCLI

class TestNodeRegistryCLIIntegration:
    @pytest.fixture
    def temp_persistence_path(self):
        """Create a temporary file path for node registry persistence."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        yield temp_path
        # Clean up the temporary file after the test
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def cli(self, temp_persistence_path):
        """Create a NodeRegistryCLI instance with a temporary persistence path."""
        return NodeRegistryCLI(persistence_path=temp_persistence_path)

    def test_register_node_integration(self, cli, capsys):
        """Test registering a node via CLI."""
        # Prepare arguments
        args = MagicMock()
        args.wallet_address = "FLOP12345ABCDE"
        args.ip_address = "192.168.1.100"
        args.hostname = "test-node"
        args.cpu_cores = 4
        args.memory_gb = 16.0
        args.storage_gb = 500.0
        args.gpu_enabled = True
        args.gpu_model = "NVIDIA GTX"
        args.os_version = "Linux 6.8.0"
        args.duxos_version = "0.1.0"

        # Register node
        cli.register_node(args)
        captured = capsys.readouterr()
        
        # Verify registration
        assert "Node registered successfully" in captured.out
        assert "Node ID:" in captured.out

    def test_list_nodes_integration(self, cli, capsys):
        """Test listing nodes via CLI."""
        # Register multiple nodes
        nodes_data = [
            {
                "wallet_address": "FLOP11111AAAAA",
                "ip_address": "192.168.1.102",
                "hostname": "high-performance-node",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "storage_gb": 2000.0,
                "gpu_enabled": True
            },
            {
                "wallet_address": "FLOP22222BBBBB",
                "ip_address": "192.168.1.103",
                "hostname": "low-performance-node",
                "cpu_cores": 2,
                "memory_gb": 4.0,
                "storage_gb": 100.0,
                "gpu_enabled": False
            }
        ]

        for node_info in nodes_data:
            args = MagicMock()
            args.wallet_address = node_info["wallet_address"]
            args.ip_address = node_info["ip_address"]
            args.hostname = node_info["hostname"]
            args.cpu_cores = node_info["cpu_cores"]
            args.memory_gb = node_info["memory_gb"]
            args.storage_gb = node_info["storage_gb"]
            args.gpu_enabled = node_info["gpu_enabled"]
            args.os_version = "Linux 6.8.0"
            args.duxos_version = "0.1.0"

            cli.register_node(args)

        # Test listing with filters
        list_args = MagicMock()
        list_args.min_cpu = 8
        list_args.min_memory = 32.0
        list_args.min_storage = 1000.0
        list_args.min_gpu = True
        list_args.min_reputation = None
        list_args.only_healthy = False

        cli.list_nodes(list_args)
        captured = capsys.readouterr()
        
        # Verify that only high-performance node is listed
        assert "high-performance-node" in captured.out
        assert "low-performance-node" not in captured.out

    def test_get_node_integration(self, cli, capsys):
        """Test retrieving a node via CLI."""
        # Register a node
        register_args = MagicMock()
        register_args.wallet_address = "FLOP99999CCCCC"
        register_args.ip_address = "192.168.1.104"
        register_args.hostname = "get-test-node"
        register_args.cpu_cores = 4
        register_args.memory_gb = 16.0
        register_args.storage_gb = 500.0
        register_args.gpu_enabled = False
        register_args.os_version = "Linux 6.8.0"
        register_args.duxos_version = "0.1.0"

        cli.register_node(register_args)
        
        # Get the node ID from the output
        captured = capsys.readouterr()
        node_id = captured.out.split("Node ID: ")[1].strip()

        # Get node details
        get_args = MagicMock()
        get_args.node_id = node_id

        cli.get_node(get_args)
        captured = capsys.readouterr()
        
        # Verify node details
        node_data = json.loads(captured.out)
        assert node_data['wallet_address'] == 'FLOP99999CCCCC'
        assert node_data['ip_address'] == '192.168.1.104'
        assert node_data['hostname'] == 'get-test-node'

    def test_update_node_health_integration(self, cli, capsys):
        """Test updating node health via CLI."""
        # Register a node
        register_args = MagicMock()
        register_args.wallet_address = "FLOP77777DDDDD"
        register_args.ip_address = "192.168.1.105"
        register_args.hostname = "health-test-node"
        register_args.cpu_cores = 4
        register_args.memory_gb = 16.0
        register_args.storage_gb = 500.0
        register_args.gpu_enabled = False
        register_args.os_version = "Linux 6.8.0"
        register_args.duxos_version = "0.1.0"

        cli.register_node(register_args)
        
        # Get the node ID from the output
        captured = capsys.readouterr()
        node_id = captured.out.split("Node ID: ")[1].strip()

        # Update node health
        health_args = MagicMock()
        health_args.node_id = node_id
        health_args.load_average = 0.5
        health_args.memory_usage = 65.5
        health_args.disk_usage = 45.2

        cli.update_node_health(health_args)
        captured = capsys.readouterr()
        
        # Verify health update
        assert f"Health metrics updated for node {node_id}" in captured.out 