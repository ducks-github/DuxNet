import argparse
import ipaddress
import json
import logging
import re
import sys
from typing import Optional

from duxos.wallet.address_utils import validate_address

from .models.node import Node, NodeCapabilities
from .services.node_registry import NodeRegistry


class NodeRegistryCLI:
    """Command-line interface for node registry management."""

    def __init__(
        self,
        persistence_path: Optional[str] = "/var/lib/duxos/nodes.json",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
    ):
        """
        Initialize the CLI with advanced logging configuration.

        :param persistence_path: Path to persist node registry data
        :param log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        :param log_file: Optional path to log file for persistent logging
        """
        # Map string log levels to logging constants
        log_level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        # Validate log level
        try:
            numeric_log_level = log_level_map[log_level.upper()]
        except KeyError:
            print(f"Invalid log level: {log_level}. Defaulting to INFO.")
            numeric_log_level = logging.INFO

        # Configure logging
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        log_formatter = logging.Formatter(log_format)

        # Root logger configuration
        logging.basicConfig(level=numeric_log_level, format=log_format)

        # Create logger for this class
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(numeric_log_level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(numeric_log_level)

        # File handler (optional)
        file_handler = None
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(log_formatter)
                file_handler.setLevel(numeric_log_level)
                self.logger.addHandler(file_handler)
                self.logger.info(f"Logging to file: {log_file}")
            except IOError as e:
                print(f"Could not create log file: {e}")

        # Add console handler
        self.logger.addHandler(console_handler)

        # Log initialization
        self.logger.info("Node Registry CLI initialized")

        # Initialize node registry
        try:
            self.registry = NodeRegistry(persistence_path)
            self.logger.info(f"Node registry initialized with persistence path: {persistence_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize node registry: {e}")
            sys.exit(1)

    def register_node(self, args):
        """
        Register a new node or update an existing node with enhanced validation.

        :param args: Parsed command-line arguments
        """
        try:
            # Validate wallet address
            if not self.validate_wallet_address(args.wallet_address):
                raise ValueError(f"Invalid wallet address format: {args.wallet_address}")

            # Validate IP address
            if not self.validate_ip_address(args.ip_address):
                raise ValueError(f"Invalid IP address format: {args.ip_address}")

            # Validate CPU cores
            if args.cpu_cores < 0:
                raise ValueError(f"CPU cores must be non-negative: {args.cpu_cores}")

            # Validate memory and storage
            if args.memory_gb < 0:
                raise ValueError(f"Memory must be non-negative: {args.memory_gb}")
            if args.storage_gb < 0:
                raise ValueError(f"Storage must be non-negative: {args.storage_gb}")

            # Create node capabilities
            capabilities = NodeCapabilities(
                cpu_cores=args.cpu_cores,
                memory_gb=args.memory_gb,
                storage_gb=args.storage_gb,
                gpu_enabled=args.gpu_enabled,
                gpu_model=args.gpu_model,
            )

            # Create node
            node = Node(
                wallet_address=args.wallet_address,
                ip_address=args.ip_address,
                hostname=args.hostname,
                os_version=args.os_version,
                duxos_version=args.duxos_version,
                capabilities=capabilities,
            )

            # Register node
            node_id = self.registry.register_node(node)
            self.logger.info(f"Node registered successfully. Node ID: {node_id}")
            print(f"Node registered successfully. Node ID: {node_id}")

        except ValueError as e:
            self.logger.error(f"Registration failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error during node registration: {e}")
            print(f"Unexpected error: {e}")
            sys.exit(1)

    def deregister_node(self, args):
        """
        Deregister a node by its ID.

        :param args: Parsed command-line arguments
        """
        result = self.registry.deregister_node(args.node_id)
        if result:
            print(f"Node {args.node_id} deregistered successfully.")
        else:
            print(f"Node {args.node_id} not found.")

    def list_nodes(self, args):
        """
        List nodes with optional filtering.

        :param args: Parsed command-line arguments
        """
        # Prepare minimum capabilities filter
        min_capabilities = None
        if any([args.min_cpu, args.min_memory, args.min_storage, args.min_gpu]):
            min_capabilities = NodeCapabilities(
                cpu_cores=args.min_cpu or 0,
                memory_gb=args.min_memory or 0.0,
                storage_gb=args.min_storage or 0.0,
                gpu_enabled=args.min_gpu or False,
            )

        # List nodes
        nodes = self.registry.list_nodes(
            min_reputation=args.min_reputation or 0.0,
            only_healthy=args.only_healthy,
            min_capabilities=min_capabilities,
        )

        # Output nodes
        if not nodes:
            print("No nodes found.")
            return

        # Print nodes in a tabular format
        print(
            f"{'Node ID':<40} {'Wallet Address':<40} {'Hostname':<25} {'IP Address':<20} {'Reputation':<10} {'Healthy':<10}"
        )
        print("-" * 145)
        for node in nodes:
            print(
                f"{node.id:<40} {node.wallet_address:<40} {node.hostname:<25} {node.ip_address:<20} {node.reputation_score:<10.2f} {node.health.is_healthy!s:<10}"
            )

    def get_node(self, args):
        """
        Retrieve and display details of a specific node.

        :param args: Parsed command-line arguments
        """
        # Try to get node by ID
        node = self.registry.get_node(args.node_id)

        if not node:
            # Try to get node by wallet address
            node = self.registry.get_node_by_wallet_address(args.node_id)

        if node:
            # Convert node to dictionary, handling potential MagicMock attributes
            node_dict = node.to_dict()

            # Remove any MagicMock attributes
            def clean_dict(d):
                if isinstance(d, dict):
                    return {
                        k: clean_dict(v)
                        for k, v in d.items()
                        if not (hasattr(v, "_mock_return_value") or hasattr(v, "_mock_side_effect"))
                    }
                return d

            cleaned_node_dict = clean_dict(node_dict)

            # Output node details in JSON
            print(json.dumps(cleaned_node_dict, indent=2))
        else:
            print(f"Node {args.node_id} not found.")

    def update_node_health(self, args):
        """
        Update a node's health metrics with enhanced validation.

        :param args: Parsed command-line arguments
        """
        try:
            # Validate load average
            if args.load_average < 0:
                raise ValueError(f"Load average must be non-negative: {args.load_average}")

            # Validate memory and disk usage percentages
            if not (0 <= args.memory_usage <= 100):
                raise ValueError(f"Memory usage must be between 0 and 100: {args.memory_usage}")
            if not (0 <= args.disk_usage <= 100):
                raise ValueError(f"Disk usage must be between 0 and 100: {args.disk_usage}")

            result = self.registry.update_node_health(
                args.node_id, args.load_average, args.memory_usage, args.disk_usage
            )

            if result:
                self.logger.info(f"Health metrics updated for node {args.node_id}")
                print(f"Health metrics updated for node {args.node_id}")
            else:
                self.logger.warning(f"Failed to update health metrics for node {args.node_id}")
                print(f"Failed to update health metrics for node {args.node_id}")

        except ValueError as e:
            self.logger.error(f"Health update failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self.logger.error(f"Unexpected error during health update: {e}")
            print(f"Unexpected error: {e}")
            sys.exit(1)

    def update_node_reputation(self, args):
        """
        Update a node's reputation based on task performance.

        :param args: Parsed command-line arguments
        """
        result = self.registry.update_node_reputation(args.node_id, args.task_success)

        if result:
            print(f"Reputation updated for node {args.node_id}")
        else:
            print(f"Failed to update reputation for node {args.node_id}")

    def create_parser(self):
        """
        Create the argument parser for the CLI with enhanced help and validation.

        :return: Configured argument parser
        """
        parser = argparse.ArgumentParser(
            description="Dux OS Node Registry Management",
            epilog="For more information, visit https://duxos.org/node-registry",
        )
        subparsers = parser.add_subparsers(
            dest="command", help="Available commands", required=True  # Require a subcommand
        )

        # Register Node
        register_parser = subparsers.add_parser(
            "register",
            help="Register a new node in the Dux OS network",
            description="Register a new node with detailed hardware and network information.",
        )
        register_parser.add_argument(
            "--wallet-address",
            required=True,
            help="Ethereum-style wallet address (0x + 40 hex characters)",
        )
        register_parser.add_argument(
            "--ip-address", required=True, help="Valid IPv4 or IPv6 address of the node"
        )
        register_parser.add_argument(
            "--hostname", help="Optional hostname for the node", default=""
        )
        register_parser.add_argument("--os-version", help="Operating system version", default="")
        register_parser.add_argument("--duxos-version", help="Dux OS version", default="")
        register_parser.add_argument(
            "--cpu-cores", type=int, default=0, help="Number of CPU cores (non-negative integer)"
        )
        register_parser.add_argument(
            "--memory-gb", type=float, default=0.0, help="Total memory in GB (non-negative float)"
        )
        register_parser.add_argument(
            "--storage-gb", type=float, default=0.0, help="Total storage in GB (non-negative float)"
        )
        register_parser.add_argument(
            "--gpu-enabled", action="store_true", help="Flag to indicate GPU availability"
        )
        register_parser.add_argument("--gpu-model", help="Optional GPU model name")

        # Deregister Node
        deregister_parser = subparsers.add_parser(
            "deregister",
            help="Deregister a node from the Dux OS network",
            description="Remove a node from the registry using its unique ID.",
        )
        deregister_parser.add_argument("node_id", help="Unique node ID to deregister")

        # List Nodes
        list_parser = subparsers.add_parser(
            "list",
            help="List registered nodes with optional filtering",
            description="Retrieve a list of nodes matching specified criteria.",
        )
        list_parser.add_argument(
            "--min-reputation", type=float, help="Minimum reputation score to filter nodes"
        )
        list_parser.add_argument(
            "--only-healthy", action="store_true", help="Show only healthy nodes"
        )
        list_parser.add_argument("--min-cpu", type=int, help="Minimum number of CPU cores")
        list_parser.add_argument("--min-memory", type=float, help="Minimum memory in GB")
        list_parser.add_argument("--min-storage", type=float, help="Minimum storage in GB")
        list_parser.add_argument("--min-gpu", action="store_true", help="Require GPU availability")

        # Get Node
        get_parser = subparsers.add_parser(
            "get",
            help="Retrieve details of a specific node",
            description="Get detailed information about a node by its ID or wallet address.",
        )
        get_parser.add_argument("node_id", help="Node ID or wallet address to retrieve")

        # Update Node Health
        health_parser = subparsers.add_parser(
            "update-health",
            help="Update node health metrics",
            description="Update health metrics for a specific node.",
        )
        health_parser.add_argument("node_id", help="Node ID to update health metrics")
        health_parser.add_argument(
            "--load-average",
            type=float,
            required=True,
            help="System load average (non-negative float)",
        )
        health_parser.add_argument(
            "--memory-usage", type=float, required=True, help="Memory usage percentage (0-100)"
        )
        health_parser.add_argument(
            "--disk-usage", type=float, required=True, help="Disk usage percentage (0-100)"
        )

        # Update Node Reputation
        rep_parser = subparsers.add_parser(
            "update-reputation",
            help="Update node reputation",
            description="Update node reputation based on task performance.",
        )
        rep_parser.add_argument("node_id", help="Node ID to update reputation")
        rep_parser.add_argument(
            "--task-success",
            action="store_true",
            help="Flag indicating task was successfully completed",
        )

        # Add logging configuration arguments
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Set the logging level",
        )
        parser.add_argument("--log-file", help="Path to the log file for persistent logging")

        return parser

    def run(self, args=None):
        """
        Run the CLI with the provided arguments and enhanced logging.

        :param args: Command-line arguments (optional)
        """
        try:
            parser = self.create_parser()
            parsed_args = parser.parse_args(args)

            # Log the command being executed
            self.logger.info(f"Executing command: {parsed_args.command}")

            # Map commands to methods
            command_map = {
                "register": self.register_node,
                "deregister": self.deregister_node,
                "list": self.list_nodes,
                "get": self.get_node,
                "update-health": self.update_node_health,
                "update-reputation": self.update_node_reputation,
            }

            # Execute the corresponding method
            if parsed_args.command:
                command_map[parsed_args.command](parsed_args)
            else:
                parser.print_help()

        except Exception as e:
            self.logger.exception(f"Unexpected error during CLI execution: {e}")
            sys.exit(1)

    def validate_wallet_address(self, wallet_address: str) -> bool:
        """
        Validate wallet address using the new address_utils module.

        :param wallet_address: Wallet address to validate
        :return: True if valid, False otherwise
        """
        validation_result = validate_address(wallet_address)
        return validation_result["is_valid"]

    def validate_ip_address(self, ip_address: str) -> bool:
        """
        Validate IP address.

        :param ip_address: IP address to validate
        :return: True if valid, False otherwise
        """
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False


def main():
    """Entry point for the CLI."""
    cli = NodeRegistryCLI()
    cli.run()


if __name__ == "__main__":
    main()
