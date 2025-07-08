from enum import Enum
from typing import Any, Dict, List, Optional, Set


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
    FILE_SHARING = "file_sharing"
    MEDIA_PROCESSING = "media_processing"
    SCIENTIFIC_COMPUTING = "scientific_computing"


class NodeCapabilityService:
    """Service for managing node capabilities."""

    def __init__(self, registry_service: Optional[Any] = None) -> None:
        """
        Initialize the capability service.

        Args:
            registry_service: Instance of NodeRegistryService to update node data
        """
        self.registry_service = registry_service
        self.standard_capabilities: Set[str] = {cap.value for cap in CapabilityType}

    def add_capability(self, node_id: str, capability: str) -> Dict[str, Any]:
        """
        Add a capability to a node.

        Args:
            node_id: The ID of the node
            capability: The capability to add

        Returns:
            dict: Result of the operation
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        if node_id not in self.registry_service.nodes:
            return {
                "success": False,
                "error": f"Node {node_id} not found",
                "node_id": node_id,
                "capability": capability,
            }

        node: Dict[str, Any] = self.registry_service.nodes[node_id]
        current_capabilities: Set[str] = set(node["capabilities"])

        if capability in current_capabilities:
            return {
                "success": False,
                "error": f"Capability '{capability}' already exists for node {node_id}",
                "node_id": node_id,
                "capability": capability,
                "current_capabilities": list(current_capabilities),
            }

        # Add the capability
        current_capabilities.add(capability)
        node["capabilities"] = list(current_capabilities)

        return {
            "success": True,
            "node_id": node_id,
            "capability": capability,
            "old_capabilities": list(current_capabilities - {capability}),
            "new_capabilities": list(current_capabilities),
            "message": f"Capability '{capability}' added to node {node_id}",
        }

    def remove_capability(self, node_id: str, capability: str) -> Dict[str, Any]:
        """
        Remove a capability from a node.

        Args:
            node_id: The ID of the node
            capability: The capability to remove

        Returns:
            dict: Result of the operation
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        if node_id not in self.registry_service.nodes:
            return {
                "success": False,
                "error": f"Node {node_id} not found",
                "node_id": node_id,
                "capability": capability,
            }

        node: Dict[str, Any] = self.registry_service.nodes[node_id]
        current_capabilities: Set[str] = set(node["capabilities"])

        if capability not in current_capabilities:
            return {
                "success": False,
                "error": f"Capability '{capability}' not found for node {node_id}",
                "node_id": node_id,
                "capability": capability,
                "current_capabilities": list(current_capabilities),
            }

        # Remove the capability
        current_capabilities.remove(capability)
        node["capabilities"] = list(current_capabilities)

        return {
            "success": True,
            "node_id": node_id,
            "capability": capability,
            "old_capabilities": list(current_capabilities | {capability}),
            "new_capabilities": list(current_capabilities),
            "message": f"Capability '{capability}' removed from node {node_id}",
        }

    def update_capabilities(self, node_id: str, capabilities: List[str]) -> Dict[str, Any]:
        """
        Update all capabilities for a node.

        Args:
            node_id: The ID of the node
            capabilities: The new list of capabilities

        Returns:
            dict: Result of the operation
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        if node_id not in self.registry_service.nodes:
            return {
                "success": False,
                "error": f"Node {node_id} not found",
                "node_id": node_id,
                "capabilities": capabilities,
            }

        node: Dict[str, Any] = self.registry_service.nodes[node_id]
        old_capabilities: List[str] = node["capabilities"]

        # Update capabilities (remove duplicates)
        new_capabilities: List[str] = list(set(capabilities))
        node["capabilities"] = new_capabilities

        return {
            "success": True,
            "node_id": node_id,
            "old_capabilities": old_capabilities,
            "new_capabilities": new_capabilities,
            "message": f"Capabilities updated for node {node_id}",
        }

    def get_nodes_with_capability(self, capability: str) -> List[Dict[str, Any]]:
        """
        Get all nodes that have a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List[Dict]: List of nodes with the capability
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        nodes: List[Dict[str, Any]] = self.registry_service.get_nodes()
        return [node for node in nodes if capability in node["capabilities"]]

    def get_nodes_with_capabilities(
        self, capabilities: List[str], require_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get nodes that have specific capabilities.

        Args:
            capabilities: List of capabilities to search for
            require_all: If True, return nodes that have ALL capabilities. If False, return nodes that have ANY capability.

        Returns:
            List[Dict]: List of nodes matching the criteria
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        nodes: List[Dict[str, Any]] = self.registry_service.get_nodes()

        if require_all:
            # Return nodes that have ALL specified capabilities
            return [
                node for node in nodes if all(cap in node["capabilities"] for cap in capabilities)
            ]
        else:
            # Return nodes that have ANY of the specified capabilities
            return [
                node for node in nodes if any(cap in node["capabilities"] for cap in capabilities)
            ]

    def get_capability_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about capabilities across all nodes.

        Returns:
            dict: Statistics about capabilities
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        nodes: List[Dict[str, Any]] = self.registry_service.get_nodes()
        capability_counts: Dict[str, int] = {}
        total_nodes: int = len(nodes)

        for node in nodes:
            for capability in node["capabilities"]:
                capability_counts[capability] = capability_counts.get(capability, 0) + 1

        # Calculate percentages
        capability_percentages: Dict[str, float] = {}
        for capability, count in capability_counts.items():
            capability_percentages[capability] = (
                (count / total_nodes * 100) if total_nodes > 0 else 0
            )

        return {
            "total_nodes": total_nodes,
            "capability_counts": capability_counts,
            "capability_percentages": capability_percentages,
            "most_common_capabilities": sorted(
                capability_counts.items(), key=lambda x: x[1], reverse=True
            )[:5],
        }

    def validate_capability(self, capability: str) -> Dict[str, Any]:
        """
        Validate if a capability is standard or custom.

        Args:
            capability: The capability to validate

        Returns:
            dict: Validation result
        """
        is_standard: bool = capability in self.standard_capabilities

        return {
            "capability": capability,
            "is_standard": is_standard,
            "standard_capabilities": list(self.standard_capabilities),
            "message": f"Capability '{capability}' is {'standard' if is_standard else 'custom'}",
        }

    def get_standard_capabilities(self) -> List[str]:
        """
        Get list of all standard capabilities.

        Returns:
            List[str]: List of standard capabilities
        """
        return list(self.standard_capabilities)

    def add_standard_capability(self, capability: str) -> Dict[str, Any]:
        """
        Add a new standard capability.

        Args:
            capability: The capability to add as standard

        Returns:
            dict: Result of the operation
        """
        if capability in self.standard_capabilities:
            return {
                "success": False,
                "error": f"Capability '{capability}' is already standard",
                "capability": capability,
            }

        self.standard_capabilities.add(capability)

        return {
            "success": True,
            "capability": capability,
            "message": f"Capability '{capability}' added as standard capability",
        }

    def get_node_capabilities(self, node_id: str) -> Dict[str, Any]:
        """
        Get capabilities for a specific node.

        Args:
            node_id: The ID of the node

        Returns:
            dict: Node capabilities information
        """
        if not self.registry_service:
            raise ValueError("Registry service not set")

        node: Optional[Dict[str, Any]] = self.registry_service.get_node(node_id)
        if not node:
            return {"success": False, "error": f"Node {node_id} not found", "node_id": node_id}

        capabilities: List[str] = node["capabilities"]
        standard_capabilities: List[str] = [
            cap for cap in capabilities if cap in self.standard_capabilities
        ]
        custom_capabilities: List[str] = [
            cap for cap in capabilities if cap not in self.standard_capabilities
        ]

        return {
            "success": True,
            "node_id": node_id,
            "all_capabilities": capabilities,
            "standard_capabilities": standard_capabilities,
            "custom_capabilities": custom_capabilities,
            "capability_count": len(capabilities),
        }
