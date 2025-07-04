from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from duxos_registry.api.schemas import NodeRegisterRequest, NodeRegisterResponse, NodeListResponse, NodeInfo, ReputationUpdateRequest, ReputationUpdateResponse
from duxos_registry.services.registry import NodeRegistryService
from duxos_registry.services.reputation import NodeReputationService, ReputationEventType

router = APIRouter()

# Singleton service instances for in-memory storage
registry_service = NodeRegistryService()
reputation_service = NodeReputationService(registry_service)

# Simple health check endpoint
@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/register", response_model=NodeRegisterResponse)
def register_node(request: NodeRegisterRequest):
    result = registry_service.register_node(
        node_id=request.node_id,
        address=request.address,
        capabilities=request.capabilities
    )
    return result

@router.get("/", response_model=NodeListResponse)
def list_nodes(
    capability: Optional[str] = Query(None, description="Filter by capability"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    nodes = registry_service.get_nodes()
    if capability:
        nodes = [n for n in nodes if capability in n["capabilities"]]
    if status:
        nodes = [n for n in nodes if n["status"] == status]
    return NodeListResponse(nodes=[NodeInfo(**n) for n in nodes])

@router.post("/reputation", response_model=ReputationUpdateResponse)
def update_node_reputation(request: ReputationUpdateRequest):
    """
    Update a node's reputation based on an event.
    
    Valid event types:
    - task_success: +10 points
    - task_failure: -5 points
    - task_timeout: -10 points
    - malicious_behavior: -50 points
    - health_milestone: +2 points
    - uptime_milestone: +5 points
    - community_contribution: +15 points
    """
    try:
        # Convert string event type to enum
        try:
            event_type = ReputationEventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid event_type: {request.event_type}. Valid types: {[e.value for e in ReputationEventType]}"
            )
        
        # Update reputation
        result = reputation_service.update_reputation(
            node_id=request.node_id,
            event_type=event_type,
            custom_delta=request.custom_delta
        )
        
        return ReputationUpdateResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 