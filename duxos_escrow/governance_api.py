"""
Governance API for DuxOS Escrow System
Handles proposal creation, voting, and execution endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .governance_manager import GovernanceManager
from .models import ProposalStatus, ProposalCategory, VoteType
from .security import rate_limiter, api_key_auth

router = APIRouter(prefix="/governance", tags=["governance"])

# Pydantic models for request/response
class ProposalCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200, description="Proposal title")
    description: str = Field(..., min_length=20, max_length=5000, description="Proposal description")
    category: ProposalCategory = Field(..., description="Proposal category")
    proposer_wallet_id: int = Field(..., description="Wallet ID of the proposer")
    required_quorum: float = Field(..., gt=0, description="Minimum voting power required")
    voting_period_days: int = Field(7, ge=1, le=30, description="Voting period in days")
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated cost in FLOP")
    funding_source: Optional[str] = Field(None, description="Source of funding")
    execution_data: Optional[Dict[str, Any]] = Field(None, description="Execution parameters")

class ProposalResponse(BaseModel):
    id: str
    title: str
    description: str
    category: ProposalCategory
    status: ProposalStatus
    proposer_wallet_id: int
    required_quorum: float
    voting_period_days: int
    estimated_cost: Optional[float]
    funding_source: Optional[str]
    created_at: datetime
    voting_started_at: Optional[datetime]
    voting_ends_at: Optional[datetime]
    executed_at: Optional[datetime]
    executed_by: Optional[int]

    class Config:
        from_attributes = True

class VoteRequest(BaseModel):
    proposal_id: str = Field(..., description="Proposal ID to vote on")
    voter_wallet_id: int = Field(..., description="Wallet ID of the voter")
    vote_type: VoteType = Field(..., description="Type of vote")
    voting_power: float = Field(..., gt=0, description="Voting power (amount of FLOP)")
    reason: Optional[str] = Field(None, max_length=1000, description="Optional reason for vote")

class VoteResponse(BaseModel):
    id: str
    proposal_id: str
    voter_wallet_id: int
    vote_type: VoteType
    voting_power: float
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class VoteResultsResponse(BaseModel):
    proposal_id: str
    total_votes: int
    total_voting_power: float
    yes_votes: int
    no_votes: int
    abstain_votes: int
    yes_power: float
    no_power: float
    abstain_power: float
    yes_percentage: float
    no_percentage: float
    abstain_percentage: float
    required_quorum: float
    quorum_met: bool
    outcome: str
    voting_active: bool
    voting_ends_at: Optional[datetime]

class GovernanceStatsResponse(BaseModel):
    total_proposals: int
    active_proposals: int
    passed_proposals: int
    executed_proposals: int
    total_votes: int
    total_voting_power: float

# Global governance manager (would be initialized with proper dependencies)
governance_manager = None

def get_governance_manager():
    """Dependency to get governance manager"""
    if governance_manager is None:
        raise HTTPException(status_code=500, detail="Governance manager not initialized")
    return governance_manager

# API endpoints
@router.post("/proposals", response_model=ProposalResponse, dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def create_proposal(
    request: ProposalCreateRequest,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Create a new governance proposal"""
    try:
        proposal = manager.create_proposal(
            title=request.title,
            description=request.description,
            category=request.category,
            proposer_wallet_id=request.proposer_wallet_id,
            required_quorum=request.required_quorum,
            voting_period_days=request.voting_period_days,
            estimated_cost=request.estimated_cost,
            funding_source=request.funding_source,
            execution_data=request.execution_data
        )
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/proposals", response_model=List[ProposalResponse], dependencies=[Depends(rate_limiter)])
async def get_proposals(
    status: Optional[ProposalStatus] = None,
    category: Optional[ProposalCategory] = None,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get proposals with optional filtering"""
    if status:
        proposals = manager.get_proposals_by_status(status)
    elif category:
        proposals = manager.get_proposals_by_category(category)
    else:
        proposals = manager.get_active_proposals()
    
    return proposals

@router.get("/proposals/{proposal_id}", response_model=ProposalResponse, dependencies=[Depends(rate_limiter)])
async def get_proposal(
    proposal_id: str,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get a specific proposal by ID"""
    try:
        proposal = manager.get_proposal(proposal_id)
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/proposals/{proposal_id}/activate", response_model=ProposalResponse, dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def activate_proposal(
    proposal_id: str,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Activate a proposal for voting"""
    try:
        proposal = manager.activate_proposal(proposal_id)
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/proposals/{proposal_id}/vote", response_model=VoteResponse, dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def cast_vote(
    request: VoteRequest,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Cast a vote on a proposal"""
    try:
        vote = manager.cast_vote(
            proposal_id=request.proposal_id,
            voter_wallet_id=request.voter_wallet_id,
            vote_type=request.vote_type,
            voting_power=request.voting_power,
            reason=request.reason
        )
        return vote
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/proposals/{proposal_id}/results", response_model=VoteResultsResponse, dependencies=[Depends(rate_limiter)])
async def get_vote_results(
    proposal_id: str,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get voting results for a proposal"""
    try:
        results = manager.get_vote_results(proposal_id)
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/proposals/{proposal_id}/finalize", response_model=ProposalResponse, dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def finalize_proposal(
    proposal_id: str,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Finalize a proposal based on voting results"""
    try:
        proposal = manager.finalize_proposal(proposal_id)
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/proposals/{proposal_id}/execute", response_model=ProposalResponse, dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def execute_proposal(
    proposal_id: str,
    executor_wallet_id: int,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Execute a passed proposal"""
    try:
        proposal = manager.execute_proposal(proposal_id, executor_wallet_id)
        return proposal
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/votes/history/{voter_wallet_id}", response_model=List[VoteResponse], dependencies=[Depends(rate_limiter)])
async def get_voter_history(
    voter_wallet_id: int,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get voting history for a wallet"""
    votes = manager.get_voter_history(voter_wallet_id)
    return votes

@router.get("/proposals/{proposal_id}/votes", response_model=List[VoteResponse], dependencies=[Depends(rate_limiter)])
async def get_proposal_votes(
    proposal_id: str,
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get all votes for a proposal"""
    try:
        votes = manager.get_proposal_votes(proposal_id)
        return votes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/stats", response_model=GovernanceStatsResponse, dependencies=[Depends(rate_limiter)])
async def get_governance_stats(
    manager: GovernanceManager = Depends(get_governance_manager)
):
    """Get governance statistics"""
    stats = manager.get_governance_stats()
    return stats 