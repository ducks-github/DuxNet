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