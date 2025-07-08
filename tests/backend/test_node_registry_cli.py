import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from duxos.registry.cli import NodeRegistryCLI
from duxos.registry.models.node import Node, NodeCapabilities
from duxos.registry.services.node_registry import NodeRegistry


class TestNodeRegistryCLI:
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

    def test_register_node(self, cli, capsys):
        """Test registering a new node via CLI."""
        args = MagicMock()
        args.wallet_address = "0x1234abcd"
        args.ip_address = "192.168.1.100"
        args.hostname = "test-node"
        args.cpu_cores = 4
        args.memory_gb = 16.0
        args.storage_gb = 500.0
        args.gpu_enabled = True
        args.gpu_model = "NVIDIA GTX"
        args.os_version = "Linux 6.8.0"
        args.duxos_version = "0.1.0"

        cli.register_node(args)
        captured = capsys.readouterr()
        assert "Node registered successfully" in captured.out

    def test_deregister_node(self, cli, capsys):
        """Test deregistering a node via CLI."""
        # First, register a node
        register_args = MagicMock()
        register_args.wallet_address = "0x5678efgh"
        register_args.ip_address = "192.168.1.101"
        register_args.hostname = "test-node-2"
        register_args.cpu_cores = 2
        register_args.memory_gb = 8.0
        register_args.storage_gb = 250.0
        register_args.gpu_enabled = False
        register_args.os_version = "Linux 6.8.0"
        register_args.duxos_version = "0.1.0"

        cli.register_node(register_args)

        # Get the node ID from the output
        captured = capsys.readouterr()
        node_id = captured.out.split("Node ID: ")[1].strip()

        # Now deregister the node
        deregister_args = MagicMock()
        deregister_args.node_id = node_id

        cli.deregister_node(deregister_args)
        captured = capsys.readouterr()
        assert f"Node {node_id} deregistered successfully" in captured.out

    def test_list_nodes(self, cli, capsys):
        """Test listing nodes with various filters."""
        # Register multiple nodes
        nodes_data = [
            {
                "wallet_address": "0x1111aaaa",
                "ip_address": "192.168.1.102",
                "hostname": "high-performance-node",
                "cpu_cores": 16,
                "memory_gb": 64.0,
                "storage_gb": 2000.0,
                "gpu_enabled": True,
            },
            {
                "wallet_address": "0x2222bbbb",
                "ip_address": "192.168.1.103",
                "hostname": "low-performance-node",
                "cpu_cores": 2,
                "memory_gb": 4.0,
                "storage_gb": 100.0,
                "gpu_enabled": False,
            },
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
        list_args.min_storage = 1000.0  # Use a concrete value instead of MagicMock
        list_args.min_gpu = True
        list_args.min_reputation = None
        list_args.only_healthy = False

        cli.list_nodes(list_args)
        captured = capsys.readouterr()

        # Verify that only high-performance node is listed
        assert "high-performance-node" in captured.out
        assert "low-performance-node" not in captured.out

    def test_update_node_health(self, cli, capsys):
        """Test updating node health metrics."""
        # Register a node first
        register_args = MagicMock()
        register_args.wallet_address = "0x9999cccc"
        register_args.ip_address = "192.168.1.104"
        register_args.hostname = "health-test-node"
        register_args.cpu_cores = 4
        register_args.memory_gb = 16.0
        register_args.storage_gb = 500.0
        register_args.gpu_enabled = False
        register_args.os_version = "Linux 6.8.0"
        register_args.duxos_version = "0.1.0"

        cli.register_node(register_args)

        # Get the node ID
        captured = capsys.readouterr()
        node_id = captured.out.split("Node ID: ")[1].strip()

        # Update health
        health_args = MagicMock()
        health_args.node_id = node_id
        health_args.load_average = 1.5
        health_args.memory_usage = 50.0
        health_args.disk_usage = 30.0

        cli.update_node_health(health_args)
        captured = capsys.readouterr()
        assert f"Health metrics updated for node {node_id}" in captured.out

    def test_update_node_reputation(self, cli, capsys):
        """Test updating node reputation."""
        # Register a node first
        register_args = MagicMock()
        register_args.wallet_address = "0x7777dddd"
        register_args.ip_address = "192.168.1.105"
        register_args.hostname = "reputation-test-node"
        register_args.cpu_cores = 4
        register_args.memory_gb = 16.0
        register_args.storage_gb = 500.0
        register_args.gpu_enabled = False
        register_args.os_version = "Linux 6.8.0"
        register_args.duxos_version = "0.1.0"

        cli.register_node(register_args)

        # Get the node ID
        captured = capsys.readouterr()
        node_id = captured.out.split("Node ID: ")[1].strip()

        # Update reputation
        rep_args = MagicMock()
        rep_args.node_id = node_id
        rep_args.task_success = True

        cli.update_node_reputation(rep_args)
        captured = capsys.readouterr()
        assert f"Reputation updated for node {node_id}" in captured.out
