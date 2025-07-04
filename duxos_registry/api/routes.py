from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from duxos_registry.api.schemas import NodeRegisterRequest, NodeRegisterResponse, NodeListResponse, NodeInfo
from duxos_registry.services.registry import NodeRegistryService

router = APIRouter()

# Singleton service instance for in-memory storage
registry_service = NodeRegistryService()

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