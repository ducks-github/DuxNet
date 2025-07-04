from typing import List
from pydantic import BaseModel

class Node(BaseModel):
    node_id: str
    address: str
    capabilities: List[str]
    status: str = "unknown"
    reputation: float = 0.0 