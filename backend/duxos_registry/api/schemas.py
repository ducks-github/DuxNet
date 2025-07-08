from typing import List

from pydantic import BaseModel


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


# Wallet Management Schemas
class WalletCreateRequest(BaseModel):
    node_id: str
    wallet_name: str
    auth_data: dict | None = None


class WalletCreateResponse(BaseModel):
    success: bool
    message: str
    wallet: dict | None = None


class WalletInfo(BaseModel):
    id: int
    node_id: str
    wallet_name: str
    address: str
    wallet_type: str
    balance: float
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None


class WalletBalanceResponse(BaseModel):
    success: bool
    node_id: str
    wallet_name: str
    address: str
    balance: float
    currency: str
    message: str | None = None


class TransactionSendRequest(BaseModel):
    node_id: str
    recipient_address: str
    amount: float
    auth_data: dict | None = None


class TransactionSendResponse(BaseModel):
    success: bool
    txid: str | None = None
    amount: float | None = None
    recipient: str | None = None
    transaction: dict | None = None
    message: str | None = None


class TransactionInfo(BaseModel):
    id: int
    wallet_id: int
    txid: str
    recipient_address: str
    amount: float
    transaction_type: str
    status: str
    created_at: str | None = None


class TransactionHistoryResponse(BaseModel):
    success: bool
    node_id: str
    wallet_name: str
    transactions: list[TransactionInfo]
    message: str | None = None


class NewAddressResponse(BaseModel):
    success: bool
    node_id: str
    new_address: str | None = None
    wallet_name: str | None = None
    message: str | None = None
