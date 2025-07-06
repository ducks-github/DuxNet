"""
Database models for the DuxOS Escrow System
"""

from sqlalchemy import Column, String, Float, DateTime, Boolean, Text, ForeignKey, Integer, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import json
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

# Import base from registry (we'll need to create a shared base)
try:
    from duxos_registry.db.database import Base
except ImportError:
    # Fallback for standalone development
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

class EscrowStatus(PyEnum):
    """Escrow contract status"""
    PENDING = "pending"
    ACTIVE = "active"
    RELEASED = "released"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    RESOLVED = "resolved"

class DisputeStatus(PyEnum):
    """Dispute resolution status"""
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"

class ProposalStatus(PyEnum):
    """Proposal status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"

class ProposalCategory(PyEnum):
    """Proposal categories"""
    COMMUNITY_FUND = "community_fund"
    ESCROW_PARAMS = "escrow_params"
    GOVERNANCE = "governance"
    FEATURE_REQUEST = "feature_request"
    BUG_FIX = "bug_fix"
    OTHER = "other"

class VoteType(PyEnum):
    """Vote types"""
    YES = "yes"
    NO = "no"
    ABSTAIN = "abstain"

class Escrow(Base):
    """Escrow contract for API transactions"""
    __tablename__ = "escrows"

    # Type annotations for SQLAlchemy 2.0 compatibility
    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    payer_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    provider_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[EscrowStatus] = mapped_column(Enum(EscrowStatus), default=EscrowStatus.PENDING, nullable=False)
    
    # Task/API information
    task_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Link to Task Engine
    api_call_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Link to API call
    service_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "image_upscaler_v1"
    
    # Validation and security
    result_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Hash of expected result
    provider_signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Provider's signature
    payer_signature: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Payer's signature
    
    # Financial tracking
    provider_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Amount to provider (95%)
    community_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Amount to community (5%)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Dispute handling - removed foreign key, will use relationship
    
    # Metadata
    escrow_metadata: Mapped[str] = mapped_column(Text, default="{}")  # JSON string for additional data
    
    # Relationships
    payer_wallet = relationship("Wallet", foreign_keys=[payer_wallet_id])
    provider_wallet = relationship("Wallet", foreign_keys=[provider_wallet_id])
    dispute = relationship("Dispute", back_populates="escrow")

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        try:
            metadata_str = str(self.escrow_metadata) if self.escrow_metadata is not None else "{}"
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata from dictionary"""
        self.escrow_metadata = json.dumps(metadata)  # type: ignore

    def calculate_distribution(self) -> None:
        """Calculate provider and community amounts"""
        self.provider_amount = self.amount * 0.95  # 95% to provider
        self.community_amount = self.amount * 0.05  # 5% to community

class Dispute(Base):
    """Dispute resolution for escrow contracts"""
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    escrow_id: Mapped[str] = mapped_column(String, ForeignKey("escrows.id"), nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    
    # Dispute details
    reason: Mapped[str] = mapped_column(String, nullable=False)  # Reason for dispute
    evidence: Mapped[str] = mapped_column(Text, default="{}")  # JSON string for evidence
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Resolution details
    
    # Parties
    initiator_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    respondent_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    escrow = relationship("Escrow", back_populates="dispute")
    initiator_wallet = relationship("Wallet", foreign_keys=[initiator_wallet_id])
    respondent_wallet = relationship("Wallet", foreign_keys=[respondent_wallet_id])

    def get_evidence(self) -> Dict[str, Any]:
        """Get evidence as dictionary"""
        try:
            evidence_str = str(self.evidence) if self.evidence is not None else "{}"
            return json.loads(evidence_str)
        except json.JSONDecodeError:
            return {}

    def set_evidence(self, evidence: Dict[str, Any]) -> None:
        """Set evidence from dictionary"""
        self.evidence = json.dumps(evidence)  # type: ignore

class CommunityFund(Base):
    """Community fund for airdrops and governance"""
    __tablename__ = "community_fund"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Airdrop configuration
    airdrop_threshold: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)  # Trigger airdrop at 100 FLOP
    last_airdrop_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_airdrop_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Governance
    governance_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_vote_threshold: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)  # 10% of total supply
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

class EscrowTransaction(Base):
    """Audit trail for all escrow-related transactions"""
    __tablename__ = "escrow_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    escrow_id: Mapped[str] = mapped_column(String, ForeignKey("escrows.id"), nullable=False)
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(String, nullable=False)  # create, release, refund, dispute
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    from_wallet_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=True)
    to_wallet_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=True)
    
    # Blockchain transaction
    blockchain_txid: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Flopcoin transaction ID
    blockchain_status: Mapped[str] = mapped_column(String, default="pending")  # pending, confirmed, failed
    
    # Metadata
    transaction_metadata: Mapped[str] = mapped_column(Text, default="{}")  # JSON string for additional data
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    escrow = relationship("Escrow")
    from_wallet = relationship("Wallet", foreign_keys=[from_wallet_id])
    to_wallet = relationship("Wallet", foreign_keys=[to_wallet_id])

    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        try:
            metadata_str = str(self.transaction_metadata) if self.transaction_metadata is not None else "{}"
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            return {}

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set metadata from dictionary"""
        self.transaction_metadata = json.dumps(metadata)  # type: ignore

class Proposal(Base):
    """Governance proposal for community voting"""
    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ProposalCategory] = mapped_column(Enum(ProposalCategory), nullable=False)
    status: Mapped[ProposalStatus] = mapped_column(Enum(ProposalStatus), default=ProposalStatus.DRAFT, nullable=False)
    
    # Proposal details
    proposer_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    required_quorum: Mapped[float] = mapped_column(Float, nullable=False)  # Minimum votes required
    voting_period_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)  # Days to vote
    
    # Financial impact
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Estimated cost in FLOP
    funding_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # community_fund, treasury, etc.
    
    # Execution details
    execution_data: Mapped[str] = mapped_column(Text, default="{}")  # JSON string for execution parameters
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    voting_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    voting_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    proposer_wallet = relationship("Wallet", foreign_keys=[proposer_wallet_id])
    executor_wallet = relationship("Wallet", foreign_keys=[executed_by])
    votes = relationship("Vote", back_populates="proposal")

    def get_execution_data(self) -> Dict[str, Any]:
        """Get execution data as dictionary"""
        try:
            data_str = str(self.execution_data) if self.execution_data is not None else "{}"
            return json.loads(data_str)
        except json.JSONDecodeError:
            return {}

    def set_execution_data(self, data: Dict[str, Any]) -> None:
        """Set execution data from dictionary"""
        self.execution_data = json.dumps(data)  # type: ignore

    def is_voting_active(self) -> bool:
        """Check if voting is currently active"""
        if not self.voting_started_at or not self.voting_ends_at:
            return False
        now = datetime.now()
        return self.voting_started_at <= now <= self.voting_ends_at

    def has_expired(self) -> bool:
        """Check if proposal has expired"""
        if not self.voting_ends_at:
            return False
        return datetime.now() > self.voting_ends_at

class Vote(Base):
    """Individual vote on a proposal"""
    __tablename__ = "votes"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    proposal_id: Mapped[str] = mapped_column(String, ForeignKey("proposals.id"), nullable=False)
    voter_wallet_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallets.id"), nullable=False)
    
    # Vote details
    vote_type: Mapped[VoteType] = mapped_column(Enum(VoteType), nullable=False)
    voting_power: Mapped[float] = mapped_column(Float, nullable=False)  # Amount of FLOP used for voting
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Optional reason for vote
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    proposal = relationship("Proposal", back_populates="votes")
    voter_wallet = relationship("Wallet", foreign_keys=[voter_wallet_id])

    def __repr__(self) -> str:
        return f"<Vote(id={self.id}, proposal_id={self.proposal_id}, vote_type={self.vote_type}, voting_power={self.voting_power})>" 