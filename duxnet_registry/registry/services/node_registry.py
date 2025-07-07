from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
import logging

from ..models.node import Node, NodeCapabilities

class NodeRegistry:
    """
    Manages node registration, discovery, and health tracking in the Dux OS network.
    
    Key Responsibilities:
    - Node registration and deregistration
    - Health monitoring
    - Reputation tracking
    - Node discovery and filtering
    """
    
    def __init__(self, persistence_path: Optional[str] = None):
        """
        Initialize the node registry.
        
        :param persistence_path: Optional path to persist node registry data
        """
        self._nodes: Dict[str, Node] = {}
        self._persistence_path = persistence_path
        
        # Logging setup
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        
        # Load persisted nodes if path is provided
        if persistence_path:
            self._load_nodes()
    
    def register_node(self, node: Node) -> str:
        """
        Register a new node in the network.
        
        :param node: Node to register
        :return: Node ID
        """
        # Validate node
        if not node.wallet_address or not node.ip_address:
            raise ValueError("Node must have a wallet address and IP address")
        
        # Check for existing node with same wallet address
        existing_node = self.get_node_by_wallet_address(node.wallet_address)
        if existing_node:
            self._logger.warning(f"Node with wallet {node.wallet_address} already exists. Updating.")
            node.id = existing_node.id
        
        # Store node
        self._nodes[node.id] = node
        self._logger.info(f"Node registered: {node.id}")
        
        # Persist if persistence is enabled
        self._save_nodes()
        
        return node.id
    
    def deregister_node(self, node_id: str) -> bool:
        """
        Remove a node from the registry.
        
        :param node_id: ID of the node to remove
        :return: Whether node was successfully removed
        """
        if node_id in self._nodes:
            del self._nodes[node_id]
            self._logger.info(f"Node deregistered: {node_id}")
            self._save_nodes()
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Retrieve a node by its ID.
        
        :param node_id: ID of the node
        :return: Node or None
        """
        return self._nodes.get(node_id)
    
    def get_node_by_wallet_address(self, wallet_address: str) -> Optional[Node]:
        """
        Find a node by its wallet address.
        
        :param wallet_address: Wallet address to search for
        :return: Node or None
        """
        for node in self._nodes.values():
            if node.wallet_address == wallet_address:
                return node
        return None
    
    def update_node_health(self, node_id: str, 
                            load_average: float, 
                            memory_usage: float, 
                            disk_usage: float) -> bool:
        """
        Update a node's health metrics.
        
        :param node_id: ID of the node
        :param load_average: System load average
        :param memory_usage: Memory usage percentage
        :param disk_usage: Disk usage percentage
        :return: Whether update was successful
        """
        node = self.get_node(node_id)
        if node:
            node.update_health(load_average, memory_usage, disk_usage)
            self._save_nodes()
            return True
        return False
    
    def update_node_reputation(self, node_id: str, task_success: bool) -> bool:
        """
        Update a node's reputation based on task performance.
        
        :param node_id: ID of the node
        :param task_success: Whether the task was completed successfully
        :return: Whether update was successful
        """
        node = self.get_node(node_id)
        if node:
            node.update_reputation(task_success)
            self._save_nodes()
            return True
        return False
    
    def list_nodes(self, 
                   min_reputation: float = 0.0, 
                   only_healthy: bool = False,
                   min_capabilities: Optional[NodeCapabilities] = None) -> List[Node]:
        """
        List nodes with optional filtering.
        
        :param min_reputation: Minimum reputation score
        :param only_healthy: Only return healthy nodes
        :param min_capabilities: Minimum node capabilities required
        :return: List of matching nodes
        """
        filtered_nodes = [
            node for node in self._nodes.values()
            if (node.reputation_score >= min_reputation and
                (not only_healthy or node.health.is_healthy) and
                (not min_capabilities or self._meets_capabilities(node, min_capabilities)))
        ]
        
        # Sort by reputation in descending order
        return sorted(filtered_nodes, key=lambda n: n.reputation_score, reverse=True)
    
    def _meets_capabilities(self, node: Node, min_capabilities: NodeCapabilities) -> bool:
        """
        Check if a node meets minimum capability requirements.
        
        :param node: Node to check
        :param min_capabilities: Minimum capabilities required
        :return: Whether node meets requirements
        """
        return (
            node.capabilities.cpu_cores >= min_capabilities.cpu_cores and
            node.capabilities.memory_gb >= min_capabilities.memory_gb and
            node.capabilities.storage_gb >= min_capabilities.storage_gb and
            (not min_capabilities.gpu_enabled or node.capabilities.gpu_enabled)
        )
    
    def _save_nodes(self):
        """
        Persist nodes to storage if persistence is enabled.
        """
        if not self._persistence_path:
            return
        
        try:
            import json
            nodes_data = {node_id: node.to_dict() for node_id, node in self._nodes.items()}
            with open(self._persistence_path, 'w') as f:
                json.dump(nodes_data, f, indent=2)
        except Exception as e:
            self._logger.error(f"Failed to save nodes: {e}")
    
    def _load_nodes(self):
        """
        Load persisted nodes from storage.
        """
        if not self._persistence_path:
            return
        
        try:
            import json
            import os
            
            if not os.path.exists(self._persistence_path):
                return
            
            with open(self._persistence_path, 'r') as f:
                nodes_data = json.load(f)
            
            self._nodes = {
                node_id: Node.from_dict(node_data) 
                for node_id, node_data in nodes_data.items()
            }
        except Exception as e:
            self._logger.error(f"Failed to load nodes: {e}")
            self._nodes = {} 