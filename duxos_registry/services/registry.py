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