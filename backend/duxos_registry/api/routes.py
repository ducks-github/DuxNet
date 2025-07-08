from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..services.capability import NodeCapabilityService
from ..services.registry import NodeRegistryService
from ..services.reputation import NodeReputationService, ReputationEventType
from .schemas import (
    AvailableCapabilitiesResponse,
    CapabilityAddRequest,
    CapabilityQueryRequest,
    CapabilityRemoveRequest,
    CapabilityResponse,
    CapabilityStatisticsResponse,
    CapabilityUpdateRequest,
    NodeInfo,
    NodeListResponse,
    NodeRegisterRequest,
    NodeRegisterResponse,
    ReputationUpdateRequest,
    ReputationUpdateResponse,
)

router = APIRouter()

# Singleton service instances for in-memory storage
registry_service = NodeRegistryService()
reputation_service = NodeReputationService(registry_service)
capability_service = NodeCapabilityService(registry_service)


# Simple health check endpoint
@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/register", response_model=NodeRegisterResponse)
def register_node(request: NodeRegisterRequest):
    """Register a new node with its capabilities."""
    try:
        result = registry_service.register_node(
            request.node_id, request.address, request.capabilities
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/nodes", response_model=NodeListResponse)
def get_nodes():
    """Get all registered nodes."""
    nodes = registry_service.get_nodes()
    return NodeListResponse(nodes=[NodeInfo(**node) for node in nodes])


@router.get("/nodes/{node_id}", response_model=NodeInfo)
def get_node(node_id: str):
    """Get a specific node by ID."""
    node = registry_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    return node


@router.post("/nodes/reputation", response_model=ReputationUpdateResponse)
def update_node_reputation(request: ReputationUpdateRequest):
    """Update a node's reputation based on an event."""
    try:
        # Validate event type
        valid_event_types = [event.value for event in ReputationEventType]
        if request.event_type not in valid_event_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type: {request.event_type}. Valid types: {valid_event_types}",
            )

        # Convert string to enum
        event_type = ReputationEventType(request.event_type)

        # Update reputation
        result = reputation_service.update_reputation(
            request.node_id, event_type, request.custom_delta
        )

        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Capability Management Endpoints


@router.post("/nodes/capabilities/add", response_model=CapabilityResponse)
def add_node_capabilities(request: CapabilityAddRequest):
    """Add new capabilities to an existing node."""
    try:
        result = registry_service.add_node_capabilities(request.node_id, request.new_capabilities)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes/capabilities/remove", response_model=CapabilityResponse)
def remove_node_capabilities(request: CapabilityRemoveRequest):
    """Remove capabilities from an existing node."""
    try:
        result = registry_service.remove_node_capabilities(
            request.node_id, request.capabilities_to_remove
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nodes/capabilities/update", response_model=CapabilityResponse)
def update_node_capabilities(request: CapabilityUpdateRequest):
    """Replace all capabilities of a node with new ones."""
    try:
        result = registry_service.update_node_capabilities(
            request.node_id, request.new_capabilities
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/capability/{capability}", response_model=NodeListResponse)
def get_nodes_by_capability(capability: str):
    """Get all nodes that have a specific capability."""
    nodes = registry_service.get_nodes_by_capability(capability)
    return NodeListResponse(nodes=[NodeInfo(**node) for node in nodes])


@router.post("/nodes/capabilities/query", response_model=NodeListResponse)
def query_nodes_by_capabilities(request: CapabilityQueryRequest):
    """Get nodes that have specific capabilities."""
    nodes = registry_service.get_nodes_by_capabilities(request.capabilities, request.match_all)
    return NodeListResponse(nodes=[NodeInfo(**node) for node in nodes])


@router.get("/capabilities/statistics", response_model=CapabilityStatisticsResponse)
def get_capability_statistics():
    """Get statistics about capabilities across all nodes."""
    stats = registry_service.get_capability_statistics()
    return stats


@router.get("/capabilities/available", response_model=AvailableCapabilitiesResponse)
def get_available_capabilities():
    """Get all available capabilities across all nodes."""
    capabilities = registry_service.get_available_capabilities()
    return AvailableCapabilitiesResponse(capabilities=capabilities)


@router.get("/capabilities/validate/{capability}")
def validate_capability(capability: str):
    """Validate if a capability is well-formed."""
    is_valid = registry_service.validate_capability(capability)
    return {
        "capability": capability,
        "is_valid": is_valid,
        "is_standard": capability in registry_service.standard_capabilities,
    }
