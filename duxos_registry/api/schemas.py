from pydantic import BaseModel
from typing import List

class NodeRegisterRequest(BaseModel):
    node_id: str
    address: str
    capabilities: list[str]

class NodeRegisterResponse(BaseModel):
    success: bool
    message: str

class NodeInfo(BaseModel):
    node_id: str
    address: str
    capabilities: list[str]
    status: str
    reputation: float

class NodeListResponse(BaseModel):
    nodes: List[NodeInfo]

class ReputationUpdateRequest(BaseModel):
    node_id: str
    event_type: str
    custom_delta: float | None = None

class ReputationUpdateResponse(BaseModel):
    success: bool
    node_id: str
    old_reputation: float | None = None
    new_reputation: float | None = None
    delta: float | None = None
    clamped: bool | None = None
    event_type: str | None = None
    rule_applied: bool | None = None
    error: str | None = None

# Capability Management Schemas
class CapabilityAddRequest(BaseModel):
    node_id: str
    new_capabilities: list[str]

class CapabilityRemoveRequest(BaseModel):
    node_id: str
    capabilities_to_remove: list[str]

class CapabilityUpdateRequest(BaseModel):
    node_id: str
    new_capabilities: list[str]

class CapabilityResponse(BaseModel):
    success: bool
    node_id: str
    old_capabilities: list[str] | None = None
    new_capabilities: list[str] | None = None
    added_capabilities: list[str] | None = None
    removed_capabilities: list[str] | None = None
    error: str | None = None

class CapabilityQueryRequest(BaseModel):
    capabilities: list[str]
    match_all: bool = False

class CapabilityStatisticsResponse(BaseModel):
    total_nodes: int
    total_capabilities: int
    capability_counts: dict[str, int]
    most_common_capabilities: list[tuple[str, int]]
    standard_capabilities: list[str]
    custom_capabilities: list[str]

class AvailableCapabilitiesResponse(BaseModel):
    capabilities: list[str] 