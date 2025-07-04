import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.registry import NodeRegistryService
from services.reputation import NodeReputationService, ReputationEventType
from api.schemas import ReputationUpdateRequest, ReputationUpdateResponse


class TestReputationIntegration:
    """Integration tests for the complete reputation system."""
    
    def setup_method(self):
        """Set up fresh service instances for each test."""
        self.registry_service = NodeRegistryService()
        self.reputation_service = NodeReputationService(self.registry_service)
    
    def test_complete_reputation_workflow(self):
        """Test a complete reputation workflow from registration to multiple updates."""
        # 1. Register a node
        register_result = self.registry_service.register_node(
            "integration_test_node", 
            "192.168.1.200:8000", 
            ["compute", "storage", "gpu"]
        )
        assert register_result["success"] is True
        
        # 2. Verify initial reputation is 0
        node = self.registry_service.get_node("integration_test_node")
        assert node is not None
        assert node["reputation"] == 0.0
        
        # 3. Update reputation for successful task
        result1 = self.reputation_service.update_reputation(
            "integration_test_node", 
            ReputationEventType.TASK_SUCCESS
        )
        assert result1["success"] is True
        assert result1["new_reputation"] == 10.0
        assert result1["event_type"] == "task_success"
        
        # 4. Update reputation for health milestone
        result2 = self.reputation_service.update_reputation(
            "integration_test_node", 
            ReputationEventType.HEALTH_MILESTONE
        )
        assert result2["success"] is True
        assert result2["old_reputation"] == 10.0
        assert result2["new_reputation"] == 12.0
        assert result2["event_type"] == "health_milestone"
        
        # 5. Update reputation for task failure
        result3 = self.reputation_service.update_reputation(
            "integration_test_node", 
            ReputationEventType.TASK_FAILURE
        )
        assert result3["success"] is True
        assert result3["old_reputation"] == 12.0
        assert result3["new_reputation"] == 7.0
        assert result3["event_type"] == "task_failure"
        
        # 6. Verify final state
        final_node = self.registry_service.get_node("integration_test_node")
        assert final_node is not None
        assert final_node["reputation"] == 7.0
    
    def test_reputation_clamping_scenarios(self):
        """Test reputation clamping in various scenarios."""
        # Register a node
        self.registry_service.register_node("clamp_test_node", "192.168.1.201:8000", ["compute"])
        
        # Test upper clamping
        self.reputation_service.update_reputation("clamp_test_node", ReputationEventType.TASK_SUCCESS, custom_delta=95.0)
        result1 = self.reputation_service.update_reputation("clamp_test_node", ReputationEventType.TASK_SUCCESS, custom_delta=10.0)
        assert result1["clamped"] is True
        assert result1["new_reputation"] == 100.0
        
        # Test lower clamping - need to subtract more than current reputation to test clamping
        self.reputation_service.update_reputation("clamp_test_node", ReputationEventType.TASK_SUCCESS, custom_delta=50.0)
        result2 = self.reputation_service.update_reputation("clamp_test_node", ReputationEventType.MALICIOUS_BEHAVIOR, custom_delta=-200.0)
        assert result2["clamped"] is True
        assert result2["new_reputation"] == 0.0
    
    def test_custom_reputation_rules(self):
        """Test custom reputation rule management."""
        # Register a node
        self.registry_service.register_node("custom_rule_node", "192.168.1.202:8000", ["compute"])
        
        # Get initial rules
        initial_rules = self.reputation_service.get_reputation_rules()
        assert initial_rules["task_success"] == 10.0
        
        # Add custom rule
        self.reputation_service.add_custom_rule(ReputationEventType.TASK_SUCCESS, 25.0)
        updated_rules = self.reputation_service.get_reputation_rules()
        assert updated_rules["task_success"] == 25.0
        
        # Test custom rule is applied
        result = self.reputation_service.update_reputation("custom_rule_node", ReputationEventType.TASK_SUCCESS)
        assert result["new_reputation"] == 25.0
        
        # Remove rule
        self.reputation_service.remove_rule(ReputationEventType.TASK_SUCCESS)
        final_rules = self.reputation_service.get_reputation_rules()
        assert final_rules["task_success"] == 0.0
    
    def test_multiple_nodes_reputation(self):
        """Test reputation management for multiple nodes."""
        # Register multiple nodes
        nodes = ["node_1", "node_2", "node_3"]
        for i, node_id in enumerate(nodes):
            self.registry_service.register_node(
                node_id, 
                f"192.168.1.{210+i}:8000", 
                ["compute"]
            )
        
        # Update reputation for each node with different events
        events = [
            ReputationEventType.TASK_SUCCESS,
            ReputationEventType.HEALTH_MILESTONE,
            ReputationEventType.COMMUNITY_CONTRIBUTION
        ]
        
        for i, (node_id, event) in enumerate(zip(nodes, events)):
            result = self.reputation_service.update_reputation(node_id, event)
            assert result["success"] is True
            assert result["node_id"] == node_id
            assert result["event_type"] == event.value
        
        # Verify all nodes have different reputations
        final_nodes = [self.registry_service.get_node(node_id) for node_id in nodes]
        reputations = [node["reputation"] for node in final_nodes if node is not None]
        
        # Should have different reputations: 10.0, 2.0, 15.0
        assert reputations == [10.0, 2.0, 15.0]
    
    def test_error_handling_integration(self):
        """Test error handling in the integrated system."""
        # Test updating reputation for non-existent node
        result = self.reputation_service.update_reputation("nonexistent_node", ReputationEventType.TASK_SUCCESS)
        assert result["success"] is False
        assert "not found" in result["error"]
        
        # Test with uninitialized reputation service
        empty_reputation_service = NodeReputationService()
        with pytest.raises(ValueError, match="Registry service not set"):
            empty_reputation_service.update_reputation("any_node", ReputationEventType.TASK_SUCCESS)
    
    def test_schema_validation(self):
        """Test Pydantic schema validation."""
        # Test valid request
        valid_request = ReputationUpdateRequest(
            node_id="test_node",
            event_type="task_success",
            custom_delta=15.0
        )
        assert valid_request.node_id == "test_node"
        assert valid_request.event_type == "task_success"
        assert valid_request.custom_delta == 15.0
        
        # Test valid response
        valid_response = ReputationUpdateResponse(
            success=True,
            node_id="test_node",
            old_reputation=0.0,
            new_reputation=15.0,
            delta=15.0,
            clamped=False,
            event_type="task_success",
            rule_applied=False,
            error=None
        )
        assert valid_response.success is True
        assert valid_response.new_reputation == 15.0
    
    def test_reputation_persistence_simulation(self):
        """Test that reputation changes persist across service operations."""
        # Register node
        self.registry_service.register_node("persistence_node", "192.168.1.220:8000", ["compute"])
        
        # Make multiple reputation updates
        updates = [
            (ReputationEventType.TASK_SUCCESS, 10.0),
            (ReputationEventType.HEALTH_MILESTONE, 12.0),
            (ReputationEventType.UPTIME_MILESTONE, 17.0),
            (ReputationEventType.TASK_FAILURE, 12.0),
            (ReputationEventType.COMMUNITY_CONTRIBUTION, 27.0)
        ]
        
        expected_reputation = 0.0
        for event_type, expected in updates:
            result = self.reputation_service.update_reputation("persistence_node", event_type)
            assert result["success"] is True
            assert result["new_reputation"] == expected
            
            # Verify persistence by getting the node
            node = self.registry_service.get_node("persistence_node")
            assert node is not None
            assert node["reputation"] == expected
            expected_reputation = expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 