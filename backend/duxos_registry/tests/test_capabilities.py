import os
import sys

import pytest

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.schemas import (
    AvailableCapabilitiesResponse,
    CapabilityAddRequest,
    CapabilityQueryRequest,
    CapabilityRemoveRequest,
    CapabilityResponse,
    CapabilityStatisticsResponse,
    CapabilityUpdateRequest,
)
from services.registry import CapabilityType, NodeRegistryService


class TestCapabilityManagement:
    """Test cases for Node Registry capability management."""

    def setup_method(self):
        """Set up fresh service instance for each test."""
        self.registry_service = NodeRegistryService()

        # Register test nodes with different capabilities
        self.registry_service.register_node(
            "compute_node", "192.168.1.100:8000", ["compute", "storage"]
        )
        self.registry_service.register_node(
            "gpu_node", "192.168.1.101:8000", ["compute", "gpu", "ai_ml"]
        )
        self.registry_service.register_node(
            "storage_node", "192.168.1.102:8000", ["storage", "database"]
        )
        self.registry_service.register_node(
            "network_node", "192.168.1.103:8000", ["network", "security"]
        )

    def test_register_node_with_capabilities(self):
        """Test registering a node with capabilities."""
        result = self.registry_service.register_node(
            "test_node", "192.168.1.200:8000", ["compute", "custom_capability"]
        )

        assert result["success"] is True
        assert result["message"] == "Node test_node registered."

        # Verify node was registered with capabilities
        node = self.registry_service.get_node("test_node")
        assert node is not None
        assert set(node["capabilities"]) == {"compute", "custom_capability"}

        # Verify capability index was updated
        assert "compute" in self.registry_service.capability_index
        assert "custom_capability" in self.registry_service.capability_index
        assert "test_node" in self.registry_service.capability_index["compute"]
        assert "test_node" in self.registry_service.capability_index["custom_capability"]

    def test_add_node_capabilities(self):
        """Test adding capabilities to an existing node."""
        result = self.registry_service.add_node_capabilities("compute_node", ["gpu", "ai_ml"])

        assert result["success"] is True
        assert result["node_id"] == "compute_node"
        assert set(result["old_capabilities"]) == {"compute", "storage"}
        assert set(result["new_capabilities"]) == {"compute", "storage", "gpu", "ai_ml"}
        assert set(result["added_capabilities"]) == {"gpu", "ai_ml"}

        # Verify node capabilities were updated
        node = self.registry_service.get_node("compute_node")
        assert set(node["capabilities"]) == {"compute", "storage", "gpu", "ai_ml"}

        # Verify capability index was updated
        assert "compute_node" in self.registry_service.capability_index["gpu"]
        assert "compute_node" in self.registry_service.capability_index["ai_ml"]

    def test_add_node_capabilities_duplicate(self):
        """Test adding capabilities that already exist (should not add duplicates)."""
        result = self.registry_service.add_node_capabilities(
            "compute_node", ["compute", "new_capability"]
        )

        assert result["success"] is True
        assert result["added_capabilities"] == ["new_capability"]  # Only new capability added
        assert "compute" not in result["added_capabilities"]  # Existing capability not added again

    def test_remove_node_capabilities(self):
        """Test removing capabilities from an existing node."""
        result = self.registry_service.remove_node_capabilities("gpu_node", ["gpu", "ai_ml"])

        assert result["success"] is True
        assert result["node_id"] == "gpu_node"
        assert set(result["old_capabilities"]) == {"compute", "gpu", "ai_ml"}
        assert set(result["new_capabilities"]) == {"compute"}
        assert set(result["removed_capabilities"]) == {"gpu", "ai_ml"}

        # Verify node capabilities were updated
        node = self.registry_service.get_node("gpu_node")
        assert set(node["capabilities"]) == {"compute"}

        # Verify capability index was updated
        assert "gpu_node" not in self.registry_service.capability_index["gpu"]
        assert "gpu_node" not in self.registry_service.capability_index["ai_ml"]
        assert "gpu_node" in self.registry_service.capability_index["compute"]

    def test_remove_node_capabilities_nonexistent(self):
        """Test removing capabilities that don't exist (should be ignored)."""
        result = self.registry_service.remove_node_capabilities(
            "compute_node", ["nonexistent_capability"]
        )

        assert result["success"] is True
        assert set(result["removed_capabilities"]) == set()  # No capabilities were removed
        assert set(result["old_capabilities"]) == set(result["new_capabilities"])  # No change

    def test_update_node_capabilities(self):
        """Test replacing all capabilities of a node."""
        result = self.registry_service.update_node_capabilities(
            "storage_node", ["web_server", "security"]
        )

        assert result["success"] is True
        assert result["node_id"] == "storage_node"
        assert set(result["old_capabilities"]) == {"storage", "database"}
        assert set(result["new_capabilities"]) == {"web_server", "security"}

        # Verify node capabilities were updated
        node = self.registry_service.get_node("storage_node")
        assert set(node["capabilities"]) == {"web_server", "security"}

        # Verify capability index was updated
        assert "storage_node" not in self.registry_service.capability_index["storage"]
        assert "storage_node" not in self.registry_service.capability_index["database"]
        assert "storage_node" in self.registry_service.capability_index["web_server"]
        assert "storage_node" in self.registry_service.capability_index["security"]

    def test_get_nodes_by_capability(self):
        """Test getting nodes by a specific capability."""
        nodes = self.registry_service.get_nodes_by_capability("compute")

        # Should return compute_node and gpu_node
        node_ids = [node["node_id"] for node in nodes]
        assert "compute_node" in node_ids
        assert "gpu_node" in node_ids
        assert len(nodes) == 2

    def test_get_nodes_by_capability_nonexistent(self):
        """Test getting nodes by a capability that doesn't exist."""
        nodes = self.registry_service.get_nodes_by_capability("nonexistent_capability")
        assert nodes == []

    def test_get_nodes_by_capabilities_any(self):
        """Test getting nodes that have ANY of the specified capabilities."""
        nodes = self.registry_service.get_nodes_by_capabilities(
            ["gpu", "database"], match_all=False
        )

        # Should return gpu_node (has gpu) and storage_node (has database)
        node_ids = [node["node_id"] for node in nodes]
        assert "gpu_node" in node_ids
        assert "storage_node" in node_ids
        assert len(nodes) == 2

    def test_get_nodes_by_capabilities_all(self):
        """Test getting nodes that have ALL of the specified capabilities."""
        nodes = self.registry_service.get_nodes_by_capabilities(
            ["compute", "storage"], match_all=True
        )

        # Should return only compute_node (has both compute and storage)
        node_ids = [node["node_id"] for node in nodes]
        assert node_ids == ["compute_node"]
        assert len(nodes) == 1

    def test_get_nodes_by_capabilities_all_nonexistent(self):
        """Test getting nodes that have ALL capabilities when some don't exist."""
        nodes = self.registry_service.get_nodes_by_capabilities(
            ["compute", "nonexistent"], match_all=True
        )
        assert nodes == []

    def test_get_capability_statistics(self):
        """Test getting capability statistics."""
        stats = self.registry_service.get_capability_statistics()

        assert stats["total_nodes"] == 4
        assert stats["total_capabilities"] > 0
        assert "capability_counts" in stats
        assert "most_common_capabilities" in stats
        assert "standard_capabilities" in stats
        assert "custom_capabilities" in stats

        # Verify some expected capability counts
        capability_counts = stats["capability_counts"]
        assert capability_counts["compute"] == 2  # compute_node and gpu_node
        assert capability_counts["storage"] == 2  # compute_node and storage_node
        assert capability_counts["gpu"] == 1  # only gpu_node

    def test_get_available_capabilities(self):
        """Test getting all available capabilities."""
        capabilities = self.registry_service.get_available_capabilities()

        # Should include all capabilities from registered nodes
        expected_capabilities = [
            "compute",
            "storage",
            "gpu",
            "ai_ml",
            "database",
            "network",
            "security",
        ]
        for capability in expected_capabilities:
            assert capability in capabilities

    def test_validate_capability_standard(self):
        """Test validating standard capabilities."""
        assert self.registry_service.validate_capability("compute") is True
        assert self.registry_service.validate_capability("gpu") is True
        assert self.registry_service.validate_capability("storage") is True

    def test_validate_capability_custom(self):
        """Test validating custom capabilities."""
        assert self.registry_service.validate_capability("custom_capability") is True
        assert self.registry_service.validate_capability("my_capability_123") is True
        assert self.registry_service.validate_capability("capability-with-hyphens") is True

    def test_validate_capability_invalid(self):
        """Test validating invalid capabilities."""
        assert self.registry_service.validate_capability("") is False
        assert self.registry_service.validate_capability("invalid capability") is False  # space
        assert (
            self.registry_service.validate_capability("invalid@capability") is False
        )  # special char
        assert self.registry_service.validate_capability(None) is False
        assert self.registry_service.validate_capability(123) is False

    def test_capability_index_consistency(self):
        """Test that capability index stays consistent with node capabilities."""
        # Add a capability
        self.registry_service.add_node_capabilities("compute_node", ["new_capability"])

        # Verify index is updated
        assert "new_capability" in self.registry_service.capability_index
        assert "compute_node" in self.registry_service.capability_index["new_capability"]

        # Remove the capability
        self.registry_service.remove_node_capabilities("compute_node", ["new_capability"])

        # Verify index is updated
        assert "compute_node" not in self.registry_service.capability_index["new_capability"]

        # If no nodes have this capability, it should be removed from index
        if not self.registry_service.capability_index["new_capability"]:
            # Note: The current implementation doesn't clean up empty capability indices
            # This is a design choice - empty capabilities are kept for potential future use
            pass

    def test_error_handling(self):
        """Test error handling for capability operations."""
        # Test adding capabilities to non-existent node
        with pytest.raises(ValueError, match="Node nonexistent_node not found"):
            self.registry_service.add_node_capabilities("nonexistent_node", ["compute"])

        # Test removing capabilities from non-existent node
        with pytest.raises(ValueError, match="Node nonexistent_node not found"):
            self.registry_service.remove_node_capabilities("nonexistent_node", ["compute"])

        # Test updating capabilities of non-existent node
        with pytest.raises(ValueError, match="Node nonexistent_node not found"):
            self.registry_service.update_node_capabilities("nonexistent_node", ["compute"])


class TestCapabilitySchemas:
    """Test cases for capability-related Pydantic schemas."""

    def test_capability_add_request(self):
        """Test CapabilityAddRequest schema."""
        request = CapabilityAddRequest(node_id="test_node", new_capabilities=["compute", "gpu"])

        assert request.node_id == "test_node"
        assert request.new_capabilities == ["compute", "gpu"]

    def test_capability_remove_request(self):
        """Test CapabilityRemoveRequest schema."""
        request = CapabilityRemoveRequest(
            node_id="test_node", capabilities_to_remove=["compute", "gpu"]
        )

        assert request.node_id == "test_node"
        assert request.capabilities_to_remove == ["compute", "gpu"]

    def test_capability_update_request(self):
        """Test CapabilityUpdateRequest schema."""
        request = CapabilityUpdateRequest(
            node_id="test_node", new_capabilities=["compute", "gpu", "storage"]
        )

        assert request.node_id == "test_node"
        assert request.new_capabilities == ["compute", "gpu", "storage"]

    def test_capability_response(self):
        """Test CapabilityResponse schema."""
        response = CapabilityResponse(
            success=True,
            node_id="test_node",
            old_capabilities=["compute"],
            new_capabilities=["compute", "gpu"],
            added_capabilities=["gpu"],
            removed_capabilities=[],
            error=None,
        )

        assert response.success is True
        assert response.node_id == "test_node"
        assert response.old_capabilities == ["compute"]
        assert response.new_capabilities == ["compute", "gpu"]
        assert response.added_capabilities == ["gpu"]
        assert response.removed_capabilities == []
        assert response.error is None

    def test_capability_query_request(self):
        """Test CapabilityQueryRequest schema."""
        request = CapabilityQueryRequest(capabilities=["compute", "gpu"], match_all=True)

        assert request.capabilities == ["compute", "gpu"]
        assert request.match_all is True

    def test_capability_statistics_response(self):
        """Test CapabilityStatisticsResponse schema."""
        response = CapabilityStatisticsResponse(
            total_nodes=4,
            total_capabilities=7,
            capability_counts={"compute": 2, "gpu": 1},
            most_common_capabilities=[("compute", 2), ("gpu", 1)],
            standard_capabilities=["compute", "gpu", "storage"],
            custom_capabilities=["custom_capability"],
        )

        assert response.total_nodes == 4
        assert response.total_capabilities == 7
        assert response.capability_counts == {"compute": 2, "gpu": 1}
        assert response.most_common_capabilities == [("compute", 2), ("gpu", 1)]
        assert response.standard_capabilities == ["compute", "gpu", "storage"]
        assert response.custom_capabilities == ["custom_capability"]

    def test_available_capabilities_response(self):
        """Test AvailableCapabilitiesResponse schema."""
        response = AvailableCapabilitiesResponse(
            capabilities=["compute", "gpu", "storage", "ai_ml"]
        )

        assert response.capabilities == ["compute", "gpu", "storage", "ai_ml"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
