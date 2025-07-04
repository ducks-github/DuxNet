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