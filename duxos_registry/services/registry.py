from typing import List, Dict, Set, Optional
from enum import Enum

class CapabilityType(Enum):
    """Standard capability types for nodes."""
    COMPUTE = "compute"
    STORAGE = "storage"
    GPU = "gpu"
    NETWORK = "network"
    SECURITY = "security"
    AI_ML = "ai_ml"
    BLOCKCHAIN = "blockchain"
    DATABASE = "database"
    WEB_SERVER = "web_server"
    CUSTOM = "custom"

class NodeRegistryService:
    def __init__(self):
        self.nodes = {}
        # Track all capabilities across all nodes for quick lookups
        self.capability_index = {}  # capability -> set of node_ids
        # Standard capabilities that are pre-defined
        self.standard_capabilities = {cap.value for cap in CapabilityType}
    
    def register_node(self, node_id: str, address: str, capabilities: list[str]):
        """Register a new node with its capabilities."""
        # Validate capabilities
        validated_capabilities = self._validate_capabilities(capabilities)
        
        self.nodes[node_id] = {
            "node_id": node_id,
            "address": address,
            "capabilities": validated_capabilities,
            "status": "active",
            "reputation": 0.0
        }
        
        # Update capability index
        self._update_capability_index(node_id, validated_capabilities)
        
        return {"success": True, "message": f"Node {node_id} registered."}
    
    def add_node_capabilities(self, node_id: str, new_capabilities: list[str]) -> dict:
        """
        Add new capabilities to an existing node.
        
        Args:
            node_id: The ID of the node to update
            new_capabilities: List of new capabilities to add
            
        Returns:
            dict: Update result with old and new capabilities
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        # Validate new capabilities
        validated_new_capabilities = self._validate_capabilities(new_capabilities)
        
        # Get current capabilities
        current_capabilities = set(self.nodes[node_id]["capabilities"])
        old_capabilities = list(current_capabilities)
        
        # Add new capabilities (avoid duplicates)
        current_capabilities.update(validated_new_capabilities)
        updated_capabilities = list(current_capabilities)
        
        # Update node
        self.nodes[node_id]["capabilities"] = updated_capabilities
        
        # Update capability index
        self._update_capability_index(node_id, updated_capabilities)
        
        return {
            "success": True,
            "node_id": node_id,
            "old_capabilities": old_capabilities,
            "new_capabilities": updated_capabilities,
            "added_capabilities": list(set(validated_new_capabilities) - set(old_capabilities))
        }
    
    def remove_node_capabilities(self, node_id: str, capabilities_to_remove: list[str]) -> dict:
        """
        Remove capabilities from an existing node.
        
        Args:
            node_id: The ID of the node to update
            capabilities_to_remove: List of capabilities to remove
            
        Returns:
            dict: Update result with old and new capabilities
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        # Get current capabilities
        current_capabilities = set(self.nodes[node_id]["capabilities"])
        old_capabilities = list(current_capabilities)
        
        # Remove specified capabilities
        current_capabilities.difference_update(capabilities_to_remove)
        updated_capabilities = list(current_capabilities)
        
        # Update node
        self.nodes[node_id]["capabilities"] = updated_capabilities
        
        # Update capability index
        self._update_capability_index(node_id, updated_capabilities)
        
        return {
            "success": True,
            "node_id": node_id,
            "old_capabilities": old_capabilities,
            "new_capabilities": updated_capabilities,
            "removed_capabilities": list(set(capabilities_to_remove) & set(old_capabilities))
        }
    
    def update_node_capabilities(self, node_id: str, new_capabilities: list[str]) -> dict:
        """
        Replace all capabilities of a node with new ones.
        
        Args:
            node_id: The ID of the node to update
            new_capabilities: List of new capabilities to set
            
        Returns:
            dict: Update result with old and new capabilities
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        # Validate new capabilities
        validated_new_capabilities = self._validate_capabilities(new_capabilities)
        
        # Get current capabilities
        old_capabilities = list(self.nodes[node_id]["capabilities"])
        
        # Update node
        self.nodes[node_id]["capabilities"] = validated_new_capabilities
        
        # Update capability index
        self._update_capability_index(node_id, validated_new_capabilities)
        
        return {
            "success": True,
            "node_id": node_id,
            "old_capabilities": old_capabilities,
            "new_capabilities": validated_new_capabilities
        }
    
    def get_nodes_by_capability(self, capability: str) -> List[dict]:
        """
        Get all nodes that have a specific capability.
        
        Args:
            capability: The capability to search for
            
        Returns:
            List[dict]: List of nodes with the specified capability
        """
        if capability not in self.capability_index:
            return []
        
        node_ids = self.capability_index[capability]
        return [self.nodes[node_id] for node_id in node_ids if node_id in self.nodes]
    
    def get_nodes_by_capabilities(self, capabilities: list[str], match_all: bool = False) -> List[dict]:
        """
        Get nodes that have specific capabilities.
        
        Args:
            capabilities: List of capabilities to search for
            match_all: If True, return nodes that have ALL capabilities. If False, return nodes that have ANY capability.
            
        Returns:
            List[dict]: List of nodes matching the criteria
        """
        if not capabilities:
            return []
        
        if match_all:
            # Find nodes that have ALL specified capabilities
            matching_node_ids = None
            for capability in capabilities:
                if capability not in self.capability_index:
                    return []  # No nodes have this capability
                
                node_ids = self.capability_index[capability]
                if matching_node_ids is None:
                    matching_node_ids = node_ids
                else:
                    matching_node_ids = matching_node_ids & node_ids
        else:
            # Find nodes that have ANY of the specified capabilities
            matching_node_ids = set()
            for capability in capabilities:
                if capability in self.capability_index:
                    matching_node_ids.update(self.capability_index[capability])
        
        if not matching_node_ids:
            return []
        
        return [self.nodes[node_id] for node_id in matching_node_ids if node_id in self.nodes]
    
    def get_capability_statistics(self) -> dict:
        """
        Get statistics about capabilities across all nodes.
        
        Returns:
            dict: Statistics including total nodes, capability counts, etc.
        """
        total_nodes = len(self.nodes)
        capability_counts = {}
        
        # Count nodes per capability
        for capability, node_ids in self.capability_index.items():
            capability_counts[capability] = len(node_ids)
        
        # Get most common capabilities
        sorted_capabilities = sorted(capability_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_nodes": total_nodes,
            "total_capabilities": len(capability_counts),
            "capability_counts": capability_counts,
            "most_common_capabilities": sorted_capabilities[:5],  # Top 5
            "standard_capabilities": list(self.standard_capabilities),
            "custom_capabilities": [cap for cap in capability_counts.keys() if cap not in self.standard_capabilities]
        }
    
    def get_available_capabilities(self) -> List[str]:
        """
        Get all available capabilities across all nodes.
        
        Returns:
            List[str]: List of all unique capabilities
        """
        return list(self.capability_index.keys())
    
    def validate_capability(self, capability: str) -> bool:
        """
        Validate if a capability is well-formed.
        
        Args:
            capability: The capability to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not capability or not isinstance(capability, str):
            return False
        
        # Check if it's a standard capability
        if capability in self.standard_capabilities:
            return True
        
        # For custom capabilities, ensure they follow naming conventions
        # Allow alphanumeric, hyphens, and underscores
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', capability))
    
    def _validate_capabilities(self, capabilities: list[str]) -> list[str]:
        """
        Validate a list of capabilities and return valid ones.
        
        Args:
            capabilities: List of capabilities to validate
            
        Returns:
            list[str]: List of valid capabilities
        """
        if not capabilities:
            return []
        
        valid_capabilities = []
        for capability in capabilities:
            if self.validate_capability(capability):
                valid_capabilities.append(capability)
        
        return valid_capabilities
    
    def _update_capability_index(self, node_id: str, capabilities: list[str]):
        """
        Update the capability index when node capabilities change.
        
        Args:
            node_id: The ID of the node
            capabilities: The node's current capabilities
        """
        # Remove node from all capability indices first
        for capability_nodes in self.capability_index.values():
            capability_nodes.discard(node_id)
        
        # Add node to capability indices for its current capabilities
        for capability in capabilities:
            if capability not in self.capability_index:
                self.capability_index[capability] = set()
            self.capability_index[capability].add(node_id)
    
    def get_nodes(self) -> List[dict]:
        return list(self.nodes.values())
    
    def update_node_reputation(self, node_id: str, delta: float) -> dict:
        """
        Update a node's reputation by the given delta.
        
        Args:
            node_id: The ID of the node to update
            delta: The reputation change (positive or negative)
            
        Returns:
            dict: Updated node info or error message
            
        Raises:
            ValueError: If node_id is not found
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        # Update reputation
        current_reputation = self.nodes[node_id]["reputation"]
        new_reputation = current_reputation + delta
        
        # Clamp reputation to reasonable bounds (0-100)
        clamped_reputation = max(0.0, min(100.0, new_reputation))
        
        # Update the node's reputation
        self.nodes[node_id]["reputation"] = clamped_reputation
        
        return {
            "success": True,
            "node_id": node_id,
            "old_reputation": current_reputation,
            "new_reputation": clamped_reputation,
            "delta": delta,
            "clamped": clamped_reputation != new_reputation
        }
    
    def get_node(self, node_id: str) -> dict | None:
        """
        Get a specific node by ID.
        
        Args:
            node_id: The ID of the node to retrieve
            
        Returns:
            dict | None: Node info or None if not found
        """
        return self.nodes.get(node_id) 