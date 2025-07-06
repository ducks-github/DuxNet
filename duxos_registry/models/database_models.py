from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.database import Base
import json
from typing import List, Dict, Any

# Association table for node-capability many-to-many relationship
node_capabilities = Table(
    'node_capabilities',
    Base.metadata,
    Column('node_id', String, ForeignKey('nodes.node_id'), primary_key=True),
    Column('capability_name', String, ForeignKey('capabilities.name'), primary_key=True)
)

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String, primary_key=True, index=True)
    address = Column(String, nullable=False)
    status = Column(String, default="unknown")  # online, offline, unknown
    reputation = Column(Float, default=0.0)
    node_metadata = Column(Text, default="{}")  # JSON string for additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    capabilities = relationship("Capability", secondary=node_capabilities, back_populates="nodes")
    reputation_events = relationship("ReputationEvent", back_populates="node")

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        try:
            metadata_str = str(self.node_metadata) if self.node_metadata is not None else "{}"
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}

    def set_metadata(self, metadata: Dict[str, Any]):
        """Set metadata from dictionary"""
        setattr(self, 'node_metadata', json.dumps(metadata))

class Capability(Base):
    __tablename__ = "capabilities"

    name = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=True)
    version = Column(String, default="1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    nodes = relationship("Node", secondary=node_capabilities, back_populates="capabilities")

class ReputationEvent(Base):
    __tablename__ = "reputation_events"

    id = Column(String, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)
    event_type = Column(String, nullable=False)  # task_completed, task_failed, etc.
    score_change = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    event_metadata = Column(Text, default="{}")  # JSON string for additional event data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    node = relationship("Node", back_populates="reputation_events")

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        try:
            metadata_str = str(self.event_metadata) if self.event_metadata is not None else "{}"
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}

    def set_metadata(self, metadata: Dict[str, Any]):
        """Set metadata from dictionary"""
        setattr(self, 'event_metadata', json.dumps(metadata))


# Wallet-related models
class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False, unique=True)
    wallet_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    wallet_type = Column(String, default="flopcoin")  # flopcoin, bitcoin, etc.
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="wallet")
    node = relationship("Node", backref="wallet")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    txid = Column(String, nullable=False, unique=True)
    recipient_address = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, default="send")  # send, receive, internal
    status = Column(String, default="pending")  # pending, confirmed, failed
    fee = Column(Float, default=0.0)
    block_height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")


class WalletCapability(Base):
    __tablename__ = "wallet_capabilities"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)
    capability_name = Column(String, default="wallet")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    node = relationship("Node", backref="wallet_capabilities") 