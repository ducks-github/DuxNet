from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
from ..db.repository import NodeRepository, CapabilityRepository, ReputationRepository
from ..db.database import get_db
from ..models.database_models import Node, Capability, ReputationEvent
import uuid
from datetime import datetime

class DatabaseNodeRegistryService:
    """Database-backed node registry service using repository pattern"""
    
    def __init__(self, db: Session):
        self.db = db
        self.node_repo = NodeRepository(db)
        self.capability_repo = CapabilityRepository(db)
        self.reputation_repo = ReputationRepository(db)
    
    def register_node(self, node_id: str, address: str, capabilities: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> Dict:
        """Register a new node with its capabilities."""
        try:
            # Check if node already exists
            existing_node = self.node_repo.get_node(node_id)
            if existing_node:
                return {"success": False, "message": f"Node {node_id} already exists"}
            
            # Create the node
            node = self.node_repo.create_node(node_id, address, capabilities, metadata)
            
            return {
                "success": True, 
                "message": f"Node {node_id} registered successfully",
                "node": self._node_to_dict(node)
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error registering node: {str(e)}"}
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get a node by ID"""
        node = self.node_repo.get_node(node_id)
        return self._node_to_dict(node) if node else None
    
    def get_all_nodes(self, active_only: bool = True) -> List[Dict]:
        """Get all nodes"""
        nodes = self.node_repo.get_all_nodes(active_only)
        result = [self._node_to_dict(node) for node in nodes]
        return [node for node in result if node is not None]
    
    def update_node_status(self, node_id: str, status: str) -> Dict:
        """Update node status"""
        try:
            node = self.node_repo.update_node_status(node_id, status)
            if node:
                return {
                    "success": True,
                    "message": f"Node {node_id} status updated to {status}",
                    "node": self._node_to_dict(node)
                }
            else:
                return {"success": False, "message": f"Node {node_id} not found"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error updating node status: {str(e)}"}
    
    def update_node_heartbeat(self, node_id: str) -> Dict:
        """Update node heartbeat"""
        try:
            node = self.node_repo.update_node_heartbeat(node_id)
            if node:
                return {
                    "success": True,
                    "message": f"Node {node_id} heartbeat updated",
                    "node": self._node_to_dict(node)
                }
            else:
                return {"success": False, "message": f"Node {node_id} not found"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error updating heartbeat: {str(e)}"}
    
    def add_node_capabilities(self, node_id: str, new_capabilities: List[str]) -> Dict:
        """Add capabilities to a node"""
        try:
            node = self.node_repo.get_node(node_id)
            if not node:
                return {"success": False, "message": f"Node {node_id} not found"}
            
            old_capabilities = [cap.name for cap in node.capabilities]
            added_capabilities = []
            
            for capability_name in new_capabilities:
                if capability_name not in old_capabilities:
                    updated_node = self.node_repo.add_capability_to_node(node_id, capability_name)
                    if updated_node:
                        added_capabilities.append(capability_name)
            
            # Get updated node
            updated_node = self.node_repo.get_node(node_id)
            if updated_node is None:
                return {"success": False, "message": f"Node {node_id} not found after update"}
            
            new_capabilities_list = [cap.name for cap in updated_node.capabilities]
            
            return {
                "success": True,
                "node_id": node_id,
                "old_capabilities": old_capabilities,
                "new_capabilities": new_capabilities_list,
                "added_capabilities": added_capabilities,
                "node": self._node_to_dict(updated_node)
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error adding capabilities: {str(e)}"}
    
    def remove_node_capabilities(self, node_id: str, capabilities_to_remove: List[str]) -> Dict:
        """Remove capabilities from a node"""
        try:
            node = self.node_repo.get_node(node_id)
            if not node:
                return {"success": False, "message": f"Node {node_id} not found"}
            
            old_capabilities = [cap.name for cap in node.capabilities]
            removed_capabilities = []
            
            for capability_name in capabilities_to_remove:
                if capability_name in old_capabilities:
                    updated_node = self.node_repo.remove_capability_from_node(node_id, capability_name)
                    if updated_node:
                        removed_capabilities.append(capability_name)
            
            # Get updated node
            updated_node = self.node_repo.get_node(node_id)
            if updated_node is None:
                return {"success": False, "message": f"Node {node_id} not found after update"}
            
            new_capabilities_list = [cap.name for cap in updated_node.capabilities]
            
            return {
                "success": True,
                "node_id": node_id,
                "old_capabilities": old_capabilities,
                "new_capabilities": new_capabilities_list,
                "removed_capabilities": removed_capabilities,
                "node": self._node_to_dict(updated_node)
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error removing capabilities: {str(e)}"}
    
    def get_nodes_by_capability(self, capability: str) -> List[Dict]:
        """Get all nodes with a specific capability"""
        nodes = self.node_repo.get_nodes_by_capability(capability)
        result = [self._node_to_dict(node) for node in nodes]
        return [node for node in result if node is not None]
    
    def get_nodes_by_capabilities(self, capabilities: List[str], match_all: bool = False) -> List[Dict]:
        """Get nodes with specific capabilities"""
        if not capabilities:
            return []
        
        if match_all:
            # Find nodes that have ALL specified capabilities
            common_node_ids: Optional[Set[str]] = None
            for capability in capabilities:
                nodes_with_cap = self.node_repo.get_nodes_by_capability(capability)
                node_ids = {str(node.node_id) for node in nodes_with_cap}
                
                if common_node_ids is None:
                    common_node_ids = node_ids
                else:
                    common_node_ids = common_node_ids & node_ids
                
                if not common_node_ids:
                    return []
            
            # Get full node objects for matching IDs
            all_nodes = self.node_repo.get_all_nodes()
            if common_node_ids is not None:
                result = [self._node_to_dict(node) for node in all_nodes if str(node.node_id) in common_node_ids]
                return [node for node in result if node is not None]
            return []
        else:
            # Find nodes that have ANY of the specified capabilities
            any_node_ids: Set[str] = set()
            for capability in capabilities:
                nodes_with_cap = self.node_repo.get_nodes_by_capability(capability)
                any_node_ids.update([str(node.node_id) for node in nodes_with_cap])
            
            # Get full node objects for matching IDs
            all_nodes = self.node_repo.get_all_nodes()
            result = [self._node_to_dict(node) for node in all_nodes if str(node.node_id) in any_node_ids]
            return [node for node in result if node is not None]
    
    def get_available_capabilities(self) -> List[str]:
        """Get all available capabilities"""
        capabilities = self.capability_repo.get_all_capabilities()
        return [str(cap.name) for cap in capabilities]
    
    def get_capability_statistics(self) -> Dict:
        """Get statistics about capabilities"""
        capabilities = self.capability_repo.get_all_capabilities()
        stats = {}
        
        for capability in capabilities:
            capability_name = str(capability.name)
            nodes_with_cap = self.node_repo.get_nodes_by_capability(capability_name)
            stats[capability_name] = {
                "description": capability.description,
                "version": capability.version,
                "node_count": len(nodes_with_cap),
                "active_nodes": len([n for n in nodes_with_cap if bool(n.is_active)])
            }
        
        return stats
    
    def update_node_reputation(self, node_id: str, delta: float) -> Dict:
        """Update node reputation"""
        try:
            node = self.node_repo.get_node(node_id)
            if not node:
                return {"success": False, "message": f"Node {node_id} not found"}
            
            # Convert SQLAlchemy column to float
            current_reputation = float(str(node.reputation))
            new_reputation = max(0.0, min(100.0, current_reputation + delta))
            updated_node = self.node_repo.update_node_reputation(node_id, new_reputation)
            
            return {
                "success": True,
                "node_id": node_id,
                "old_reputation": current_reputation,
                "new_reputation": new_reputation,
                "delta": delta,
                "node": self._node_to_dict(updated_node)
            }
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error updating reputation: {str(e)}"}
    
    def delete_node(self, node_id: str) -> Dict:
        """Soft delete a node"""
        try:
            success = self.node_repo.delete_node(node_id)
            if success:
                return {"success": True, "message": f"Node {node_id} deleted successfully"}
            else:
                return {"success": False, "message": f"Node {node_id} not found"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Error deleting node: {str(e)}"}
    
    def _node_to_dict(self, node: Optional[Node]) -> Optional[Dict]:
        """Convert Node model to dictionary"""
        if not node:
            return None
        
        return {
            "node_id": node.node_id,
            "address": node.address,
            "status": node.status,
            "reputation": node.reputation,
            "capabilities": [cap.name for cap in node.capabilities],
            "metadata": node.get_metadata(),
            "created_at": node.created_at.isoformat() if node.created_at is not None else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at is not None else None,
            "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat is not None else None,
            "is_active": node.is_active
        } 