"""
Tests for Governance Manager
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from duxos_escrow.governance_manager import GovernanceManager
from duxos_escrow.models import (
    Proposal, Vote, ProposalStatus, ProposalCategory, VoteType,
    Escrow, Dispute, CommunityFund, EscrowTransaction
)
from duxos_escrow.exceptions import (
    GovernanceError, ProposalNotFoundError, VotingNotActiveError,
    AlreadyVotedError, InsufficientVotingPowerError, ProposalExecutionError
)

# Test database setup
@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create all tables
    from duxos_escrow.models import Base
    Base.metadata.create_all(engine)
    
    yield session
    
    session.close()

@pytest.fixture
def governance_manager(db_session):
    """Create a governance manager instance"""
    return GovernanceManager(db_session)

@pytest.fixture
def sample_proposal_data():
    """Sample proposal data for testing"""
    return {
        "title": "Test Proposal",
        "description": "This is a test proposal for governance testing",
        "category": ProposalCategory.COMMUNITY_FUND,
        "proposer_wallet_id": 1,
        "required_quorum": 100.0,
        "voting_period_days": 7,
        "estimated_cost": 50.0,
        "funding_source": "community_fund"
    }

class TestGovernanceManager:
    """Test cases for GovernanceManager"""
    
    def test_create_proposal_success(self, governance_manager, sample_proposal_data):
        """Test successful proposal creation"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        
        assert proposal.id is not None
        assert proposal.title == sample_proposal_data["title"]
        assert proposal.description == sample_proposal_data["description"]
        assert proposal.category == sample_proposal_data["category"]
        assert proposal.status == ProposalStatus.DRAFT
        assert proposal.proposer_wallet_id == sample_proposal_data["proposer_wallet_id"]
        assert proposal.required_quorum == sample_proposal_data["required_quorum"]
    
    def test_create_proposal_validation_errors(self, governance_manager, sample_proposal_data):
        """Test proposal creation validation errors"""
        # Test short title
        with pytest.raises(GovernanceError, match="title must be at least 5 characters"):
            governance_manager.create_proposal(**{**sample_proposal_data, "title": "Hi"})
        
        # Test short description
        with pytest.raises(GovernanceError, match="description must be at least 20 characters"):
            governance_manager.create_proposal(**{**sample_proposal_data, "description": "Short"})
        
        # Test invalid quorum
        with pytest.raises(GovernanceError, match="Required quorum must be positive"):
            governance_manager.create_proposal(**{**sample_proposal_data, "required_quorum": 0})
        
        # Test invalid voting period
        with pytest.raises(GovernanceError, match="Voting period must be between 1 and 30 days"):
            governance_manager.create_proposal(**{**sample_proposal_data, "voting_period_days": 0})
        
        with pytest.raises(GovernanceError, match="Voting period must be between 1 and 30 days"):
            governance_manager.create_proposal(**{**sample_proposal_data, "voting_period_days": 31})
    
    def test_activate_proposal_success(self, governance_manager, sample_proposal_data):
        """Test successful proposal activation"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        activated_proposal = governance_manager.activate_proposal(proposal.id)
        
        assert activated_proposal.status == ProposalStatus.ACTIVE
        assert activated_proposal.voting_started_at is not None
        assert activated_proposal.voting_ends_at is not None
        assert activated_proposal.voting_ends_at > activated_proposal.voting_started_at
    
    def test_activate_proposal_wrong_status(self, governance_manager, sample_proposal_data):
        """Test activating proposal in wrong status"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        # Try to activate again
        with pytest.raises(GovernanceError, match="Cannot activate proposal in active status"):
            governance_manager.activate_proposal(proposal.id)
    
    def test_get_proposal_success(self, governance_manager, sample_proposal_data):
        """Test getting proposal by ID"""
        created_proposal = governance_manager.create_proposal(**sample_proposal_data)
        retrieved_proposal = governance_manager.get_proposal(created_proposal.id)
        
        assert retrieved_proposal.id == created_proposal.id
        assert retrieved_proposal.title == created_proposal.title
    
    def test_get_proposal_not_found(self, governance_manager):
        """Test getting non-existent proposal"""
        with pytest.raises(ProposalNotFoundError, match="Proposal .* not found"):
            governance_manager.get_proposal("non-existent-id")
    
    def test_cast_vote_success(self, governance_manager, sample_proposal_data):
        """Test successful vote casting"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        vote = governance_manager.cast_vote(
            proposal_id=proposal.id,
            voter_wallet_id=2,
            vote_type=VoteType.YES,
            voting_power=50.0,
            reason="I support this proposal"
        )
        
        assert vote.id is not None
        assert vote.proposal_id == proposal.id
        assert vote.voter_wallet_id == 2
        assert vote.vote_type == VoteType.YES
        assert vote.voting_power == 50.0
        assert vote.reason == "I support this proposal"
    
    def test_cast_vote_voting_not_active(self, governance_manager, sample_proposal_data):
        """Test casting vote when voting is not active"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        # Don't activate the proposal
        
        with pytest.raises(VotingNotActiveError, match="Voting is not active"):
            governance_manager.cast_vote(
                proposal_id=proposal.id,
                voter_wallet_id=2,
                vote_type=VoteType.YES,
                voting_power=50.0
            )
    
    def test_cast_vote_already_voted(self, governance_manager, sample_proposal_data):
        """Test casting vote when already voted"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        # Cast first vote
        governance_manager.cast_vote(
            proposal_id=proposal.id,
            voter_wallet_id=2,
            vote_type=VoteType.YES,
            voting_power=50.0
        )
        
        # Try to vote again
        with pytest.raises(AlreadyVotedError, match="has already voted"):
            governance_manager.cast_vote(
                proposal_id=proposal.id,
                voter_wallet_id=2,
                vote_type=VoteType.NO,
                voting_power=30.0
            )
    
    def test_cast_vote_invalid_power(self, governance_manager, sample_proposal_data):
        """Test casting vote with invalid voting power"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        with pytest.raises(InsufficientVotingPowerError, match="Voting power must be positive"):
            governance_manager.cast_vote(
                proposal_id=proposal.id,
                voter_wallet_id=2,
                vote_type=VoteType.YES,
                voting_power=0.0
            )
    
    def test_get_vote_results_no_votes(self, governance_manager, sample_proposal_data):
        """Test getting vote results with no votes"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        results = governance_manager.get_vote_results(proposal.id)
        
        assert results["proposal_id"] == proposal.id
        assert results["total_votes"] == 0
        assert results["total_voting_power"] == 0
        assert results["yes_votes"] == 0
        assert results["no_votes"] == 0
        assert results["abstain_votes"] == 0
        assert results["quorum_met"] == False
        assert results["outcome"] == "pending"
        assert results["voting_active"] == True
    
    def test_get_vote_results_with_votes(self, governance_manager, sample_proposal_data):
        """Test getting vote results with votes"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        # Cast votes
        governance_manager.cast_vote(proposal.id, 1, VoteType.YES, 60.0)
        governance_manager.cast_vote(proposal.id, 2, VoteType.NO, 30.0)
        governance_manager.cast_vote(proposal.id, 3, VoteType.ABSTAIN, 10.0)
        
        results = governance_manager.get_vote_results(proposal.id)
        
        assert results["total_votes"] == 3
        assert results["total_voting_power"] == 100.0
        assert results["yes_votes"] == 1
        assert results["no_votes"] == 1
        assert results["abstain_votes"] == 1
        assert results["yes_power"] == 60.0
        assert results["no_power"] == 30.0
        assert results["abstain_power"] == 10.0
        assert results["yes_percentage"] == 60.0
        assert results["no_percentage"] == 30.0
        assert results["abstain_percentage"] == 10.0
        assert results["quorum_met"] == True  # 100 >= 100
        assert results["outcome"] == "pending"  # Still active
    
    def test_finalize_proposal_success(self, governance_manager, sample_proposal_data):
        """Test successful proposal finalization"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        # Cast votes to pass
        governance_manager.cast_vote(proposal.id, 1, VoteType.YES, 60.0)
        governance_manager.cast_vote(proposal.id, 2, VoteType.NO, 30.0)
        
        # Mock the proposal to be expired
        with patch.object(proposal, 'has_expired', return_value=True):
            finalized_proposal = governance_manager.finalize_proposal(proposal.id)
            assert finalized_proposal.status == ProposalStatus.PASSED
    
    def test_finalize_proposal_not_active(self, governance_manager, sample_proposal_data):
        """Test finalizing proposal that's not active"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        # Don't activate
        
        with pytest.raises(GovernanceError, match="Cannot finalize proposal in draft status"):
            governance_manager.finalize_proposal(proposal.id)
    
    def test_finalize_proposal_not_expired(self, governance_manager, sample_proposal_data):
        """Test finalizing proposal that hasn't expired"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        with pytest.raises(GovernanceError, match="Cannot finalize proposal before voting period ends"):
            governance_manager.finalize_proposal(proposal.id)
    
    def test_execute_proposal_success(self, governance_manager, sample_proposal_data):
        """Test successful proposal execution"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        # Cast votes and finalize to pass
        governance_manager.cast_vote(proposal.id, 1, VoteType.YES, 60.0)
        governance_manager.cast_vote(proposal.id, 2, VoteType.NO, 30.0)
        
        with patch.object(proposal, 'has_expired', return_value=True):
            governance_manager.finalize_proposal(proposal.id)
        
        executed_proposal = governance_manager.execute_proposal(proposal.id, 5)
        
        assert executed_proposal.status == ProposalStatus.EXECUTED
        assert executed_proposal.executed_at is not None
        assert executed_proposal.executed_by == 5
    
    def test_execute_proposal_not_passed(self, governance_manager, sample_proposal_data):
        """Test executing proposal that hasn't passed"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        with pytest.raises(ProposalExecutionError, match="Cannot execute proposal in active status"):
            governance_manager.execute_proposal(proposal.id, 5)
    
    def test_get_voter_history(self, governance_manager, sample_proposal_data):
        """Test getting voter history"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        governance_manager.cast_vote(proposal.id, 1, VoteType.YES, 50.0)
        governance_manager.cast_vote(proposal.id, 2, VoteType.NO, 30.0)
        
        history = governance_manager.get_voter_history(1)
        assert len(history) == 1
        assert history[0].voter_wallet_id == 1
        assert history[0].vote_type == VoteType.YES
    
    def test_get_proposal_votes(self, governance_manager, sample_proposal_data):
        """Test getting all votes for a proposal"""
        proposal = governance_manager.create_proposal(**sample_proposal_data)
        governance_manager.activate_proposal(proposal.id)
        
        governance_manager.cast_vote(proposal.id, 1, VoteType.YES, 50.0)
        governance_manager.cast_vote(proposal.id, 2, VoteType.NO, 30.0)
        
        votes = governance_manager.get_proposal_votes(proposal.id)
        assert len(votes) == 2
        assert all(vote.proposal_id == proposal.id for vote in votes)
    
    def test_get_governance_stats(self, governance_manager, sample_proposal_data):
        """Test getting governance statistics"""
        # Create multiple proposals
        proposal1 = governance_manager.create_proposal(**sample_proposal_data)
        proposal2 = governance_manager.create_proposal(**{**sample_proposal_data, "title": "Proposal 2"})
        
        governance_manager.activate_proposal(proposal1.id)
        governance_manager.cast_vote(proposal1.id, 1, VoteType.YES, 50.0)
        
        stats = governance_manager.get_governance_stats()
        
        assert stats["total_proposals"] == 2
        assert stats["active_proposals"] == 1
        assert stats["total_votes"] == 1
        assert stats["total_voting_power"] == 50.0 