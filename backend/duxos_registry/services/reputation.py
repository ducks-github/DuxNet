from enum import Enum
from typing import Any, Dict, Optional


class ReputationEventType(Enum):
    """Types of events that can affect node reputation."""

    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    TASK_TIMEOUT = "task_timeout"
    MALICIOUS_BEHAVIOR = "malicious_behavior"
    HEALTH_MILESTONE = "health_milestone"
    UPTIME_MILESTONE = "uptime_milestone"
    COMMUNITY_CONTRIBUTION = "community_contribution"


class NodeReputationService:
    def __init__(self, registry_service: Optional[Any] = None) -> None:
        """
        Initialize the reputation service.

        Args:
            registry_service: Instance of NodeRegistryService to update node data
        """
        self.registry_service = registry_service

        # Define reputation scoring rules
        self.reputation_rules: Dict[ReputationEventType, float] = {
            ReputationEventType.TASK_SUCCESS: 10.0,
            ReputationEventType.TASK_FAILURE: -5.0,
            ReputationEventType.TASK_TIMEOUT: -10.0,
            ReputationEventType.MALICIOUS_BEHAVIOR: -50.0,
            ReputationEventType.HEALTH_MILESTONE: 2.0,
            ReputationEventType.UPTIME_MILESTONE: 5.0,
            ReputationEventType.COMMUNITY_CONTRIBUTION: 15.0,
        }

    def set_registry_service(self, registry_service: Any) -> None:
        """Set the registry service instance."""
        self.registry_service = registry_service

    def update_reputation(
        self, node_id: str, event_type: ReputationEventType, custom_delta: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Update a node's reputation based on an event.

        Args:
            node_id: The ID of the node to update
            event_type: The type of event that occurred
            custom_delta: Optional custom reputation change (overrides default rules)

        Returns:
            dict: Result of the reputation update

        Raises:
            ValueError: If node_id is not found or registry_service is not set
        """
        if not self.registry_service:
            raise ValueError("Registry service not set. Call set_registry_service() first.")

        # Calculate reputation delta
        if custom_delta is not None:
            delta: float = custom_delta
        else:
            delta = self.reputation_rules.get(event_type, 0.0)

        # Update reputation via registry service
        try:
            result: Dict[str, Any] = self.registry_service.update_node_reputation(node_id, delta)
            result["event_type"] = event_type.value
            result["rule_applied"] = custom_delta is None
            return result
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "node_id": node_id,
                "event_type": event_type.value,
            }

    def get_reputation_rules(self) -> Dict[str, float]:
        """Get the current reputation scoring rules."""
        return {event_type.value: delta for event_type, delta in self.reputation_rules.items()}

    def add_custom_rule(self, event_type: ReputationEventType, delta: float) -> None:
        """Add or update a custom reputation rule."""
        self.reputation_rules[event_type] = delta

    def remove_rule(self, event_type: ReputationEventType) -> None:
        """Remove a reputation rule (sets it to 0)."""
        self.reputation_rules[event_type] = 0.0
