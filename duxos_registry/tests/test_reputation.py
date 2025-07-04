import pytest
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.registry import NodeRegistryService
from services.reputation import NodeReputationService, ReputationEventType
from api.schemas import ReputationUpdateRequest, ReputationUpdateResponse
from fastapi.testclient import TestClient

# Import app with proper path handling
try:
    from main import app
except ImportError:
    # If running from tests directory, adjust the import
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from duxos_registry.main import app

class TestNodeRegistryService:
    """Test cases for NodeRegistryService reputation functionality."""
    
    def setup_method(self):
        """Set up fresh service instance for each test."""
        self.registry_service = NodeRegistryService()
        # Register a test node
        self.registry_service.register_node("test_node_1", "192.168.1.100:8000", ["compute", "storage"])
    
    def test_update_node_reputation_success(self):
        """Test successful reputation update."""
        result = self.registry_service.update_node_reputation("test_node_1", 10.0)
        
        assert result["success"] is True
        assert result["node_id"] == "test_node_1"
        assert result["old_reputation"] == 0.0
        assert result["new_reputation"] == 10.0
        assert result["delta"] == 10.0
        assert result["clamped"] is False
        
        # Verify the node's reputation was actually updated
        node = self.registry_service.get_node("test_node_1")
        assert node is not None
        assert node["reputation"] == 10.0
    
    def test_update_node_reputation_negative(self):
        """Test negative reputation update."""
        # First set some positive reputation
        self.registry_service.update_node_reputation("test_node_1", 20.0)
        
        # Then apply negative delta
        result = self.registry_service.update_node_reputation("test_node_1", -5.0)
        
        assert result["success"] is True
        assert result["old_reputation"] == 20.0
        assert result["new_reputation"] == 15.0
        assert result["delta"] == -5.0
        assert result["clamped"] is False
    
    def test_update_node_reputation_clamping_upper(self):
        """Test reputation clamping at upper bound (100)."""
        # Set reputation to 95
        self.registry_service.update_node_reputation("test_node_1", 95.0)
        
        # Try to add 10 more (should clamp to 100)
        result = self.registry_service.update_node_reputation("test_node_1", 10.0)
        
        assert result["success"] is True
        assert result["old_reputation"] == 95.0
        assert result["new_reputation"] == 100.0
        assert result["delta"] == 10.0
        assert result["clamped"] is True
    
    def test_update_node_reputation_clamping_lower(self):
        """Test reputation clamping at lower bound (0)."""
        # Try to subtract more than current reputation
        result = self.registry_service.update_node_reputation("test_node_1", -50.0)
        
        assert result["success"] is True
        assert result["old_reputation"] == 0.0
        assert result["new_reputation"] == 0.0
        assert result["delta"] == -50.0
        assert result["clamped"] is True
    
    def test_update_node_reputation_node_not_found(self):
        """Test error handling for non-existent node."""
        with pytest.raises(ValueError, match="Node nonexistent_node not found"):
            self.registry_service.update_node_reputation("nonexistent_node", 10.0)
    
    def test_get_node(self):
        """Test getting a specific node."""
        node = self.registry_service.get_node("test_node_1")
        assert node is not None
        assert node["node_id"] == "test_node_1"
        assert node["address"] == "192.168.1.100:8000"
        assert node["capabilities"] == ["compute", "storage"]
        assert node["reputation"] == 0.0
    
    def test_get_node_not_found(self):
        """Test getting a non-existent node."""
        node = self.registry_service.get_node("nonexistent_node")
        assert node is None


class TestNodeReputationService:
    """Test cases for NodeReputationService."""
    
    def setup_method(self):
        """Set up fresh service instances for each test."""
        self.registry_service = NodeRegistryService()
        self.reputation_service = NodeReputationService(self.registry_service)
        
        # Register test nodes
        self.registry_service.register_node("test_node_1", "192.168.1.100:8000", ["compute"])
        self.registry_service.register_node("test_node_2", "192.168.1.101:8000", ["storage"])
    
    def test_update_reputation_task_success(self):
        """Test reputation update for task success."""
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS)
        
        assert result["success"] is True
        assert result["node_id"] == "test_node_1"
        assert result["old_reputation"] == 0.0
        assert result["new_reputation"] == 10.0
        assert result["delta"] == 10.0
        assert result["event_type"] == "task_success"
        assert result["rule_applied"] is True
    
    def test_update_reputation_task_failure(self):
        """Test reputation update for task failure."""
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_FAILURE)
        
        assert result["success"] is True
        assert result["node_id"] == "test_node_1"
        assert result["old_reputation"] == 0.0
        assert result["new_reputation"] == 0.0  # Clamped to 0
        assert result["delta"] == -5.0
        assert result["event_type"] == "task_failure"
        assert result["rule_applied"] is True
        assert result["clamped"] is True
    
    def test_update_reputation_malicious_behavior(self):
        """Test reputation update for malicious behavior."""
        # First give some positive reputation
        self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS)
        
        # Then apply malicious behavior penalty
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.MALICIOUS_BEHAVIOR)
        
        assert result["success"] is True
        assert result["old_reputation"] == 10.0
        assert result["new_reputation"] == 0.0  # Clamped to 0
        assert result["delta"] == -50.0
        assert result["event_type"] == "malicious_behavior"
        assert result["rule_applied"] is True
        assert result["clamped"] is True
    
    def test_update_reputation_custom_delta(self):
        """Test reputation update with custom delta."""
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS, custom_delta=25.0)
        
        assert result["success"] is True
        assert result["node_id"] == "test_node_1"
        assert result["old_reputation"] == 0.0
        assert result["new_reputation"] == 25.0
        assert result["delta"] == 25.0
        assert result["event_type"] == "task_success"
        assert result["rule_applied"] is False  # Custom delta was used
    
    def test_update_reputation_node_not_found(self):
        """Test error handling for non-existent node."""
        result = self.reputation_service.update_reputation("nonexistent_node", ReputationEventType.TASK_SUCCESS)
        
        assert result["success"] is False
        assert result["error"] == "Node nonexistent_node not found"
        assert result["node_id"] == "nonexistent_node"
        assert result["event_type"] == "task_success"
    
    def test_update_reputation_no_registry_service(self):
        """Test error when registry service is not set."""
        reputation_service = NodeReputationService()
        
        with pytest.raises(ValueError, match="Registry service not set"):
            reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS)
    
    def test_get_reputation_rules(self):
        """Test getting current reputation rules."""
        rules = self.reputation_service.get_reputation_rules()
        
        expected_rules = {
            "task_success": 10.0,
            "task_failure": -5.0,
            "task_timeout": -10.0,
            "malicious_behavior": -50.0,
            "health_milestone": 2.0,
            "uptime_milestone": 5.0,
            "community_contribution": 15.0,
        }
        
        assert rules == expected_rules
    
    def test_add_custom_rule(self):
        """Test adding a custom reputation rule."""
        self.reputation_service.add_custom_rule(ReputationEventType.TASK_SUCCESS, 15.0)
        
        rules = self.reputation_service.get_reputation_rules()
        assert rules["task_success"] == 15.0
        
        # Test that the new rule is applied
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS)
        assert result["new_reputation"] == 15.0
    
    def test_remove_rule(self):
        """Test removing a reputation rule."""
        self.reputation_service.remove_rule(ReputationEventType.TASK_SUCCESS)
        
        rules = self.reputation_service.get_reputation_rules()
        assert rules["task_success"] == 0.0
        
        # Test that the removed rule has no effect
        result = self.reputation_service.update_reputation("test_node_1", ReputationEventType.TASK_SUCCESS)
        assert result["new_reputation"] == 0.0  # No change


class TestReputationAPI:
    """Test cases for the reputation API endpoints."""
    
    def setup_method(self):
        """Set up test client and register test nodes."""
        self.client = TestClient(app)
        
        # Register a test node via the API
        self.client.post("/nodes/register", json={
            "node_id": "api_test_node",
            "address": "192.168.1.200:8000",
            "capabilities": ["compute", "api"]
        })
    
    def test_update_reputation_success(self):
        """Test successful reputation update via API."""
        response = self.client.post("/nodes/reputation", json={
            "node_id": "api_test_node",
            "event_type": "task_success"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["node_id"] == "api_test_node"
        assert data["old_reputation"] == 0.0
        assert data["new_reputation"] == 10.0
        assert data["delta"] == 10.0
        assert data["event_type"] == "task_success"
        assert data["rule_applied"] is True
        assert data["clamped"] is False
    
    def test_update_reputation_custom_delta(self):
        """Test reputation update with custom delta via API."""
        response = self.client.post("/nodes/reputation", json={
            "node_id": "api_test_node",
            "event_type": "task_success",
            "custom_delta": 25.0
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["new_reputation"] == 25.0
        assert data["delta"] == 25.0
        assert data["rule_applied"] is False  # Custom delta was used
    
    def test_update_reputation_invalid_event_type(self):
        """Test error handling for invalid event type."""
        response = self.client.post("/nodes/reputation", json={
            "node_id": "api_test_node",
            "event_type": "invalid_event"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid event_type" in data["detail"]
        assert "Valid types:" in data["detail"]
    
    def test_update_reputation_node_not_found(self):
        """Test error handling for non-existent node."""
        response = self.client.post("/nodes/reputation", json={
            "node_id": "nonexistent_node",
            "event_type": "task_success"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "Node nonexistent_node not found" in data["detail"]
    
    def test_update_reputation_missing_node_id(self):
        """Test error handling for missing node_id."""
        response = self.client.post("/nodes/reputation", json={
            "event_type": "task_success"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_update_reputation_missing_event_type(self):
        """Test error handling for missing event_type."""
        response = self.client.post("/nodes/reputation", json={
            "node_id": "api_test_node"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_all_event_types(self):
        """Test all reputation event types work correctly."""
        event_types = [
            "task_success",
            "task_failure", 
            "task_timeout",
            "malicious_behavior",
            "health_milestone",
            "uptime_milestone",
            "community_contribution"
        ]
        
        for event_type in event_types:
            response = self.client.post("/nodes/reputation", json={
                "node_id": "api_test_node",
                "event_type": event_type
            })
            
            assert response.status_code == 200, f"Failed for event_type: {event_type}"
            data = response.json()
            assert data["success"] is True
            assert data["event_type"] == event_type


class TestReputationSchemas:
    """Test cases for reputation-related Pydantic schemas."""
    
    def test_reputation_update_request_valid(self):
        """Test valid ReputationUpdateRequest."""
        request = ReputationUpdateRequest(
            node_id="test_node",
            event_type="task_success",
            custom_delta=15.0
        )
        
        assert request.node_id == "test_node"
        assert request.event_type == "task_success"
        assert request.custom_delta == 15.0
    
    def test_reputation_update_request_optional_custom_delta(self):
        """Test ReputationUpdateRequest without custom_delta."""
        request = ReputationUpdateRequest(
            node_id="test_node",
            event_type="task_success"
        )
        
        assert request.node_id == "test_node"
        assert request.event_type == "task_success"
        assert request.custom_delta is None
    
    def test_reputation_update_response_valid(self):
        """Test valid ReputationUpdateResponse."""
        response = ReputationUpdateResponse(
            success=True,
            node_id="test_node",
            old_reputation=0.0,
            new_reputation=10.0,
            delta=10.0,
            clamped=False,
            event_type="task_success",
            rule_applied=True,
            error=None
        )
        
        assert response.success is True
        assert response.node_id == "test_node"
        assert response.old_reputation == 0.0
        assert response.new_reputation == 10.0
        assert response.delta == 10.0
        assert response.clamped is False
        assert response.event_type == "task_success"
        assert response.rule_applied is True
        assert response.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 