from typing import List

class NodeRegistryService:
    def __init__(self):
        self.nodes = {}

    def register_node(self, node_id: str, address: str, capabilities: list[str]):
        self.nodes[node_id] = {
            "node_id": node_id,
            "address": address,
            "capabilities": capabilities,
            "status": "active",
            "reputation": 0.0
        }
        return {"success": True, "message": f"Node {node_id} registered."}

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