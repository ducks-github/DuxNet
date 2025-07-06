"""
Tests for Governance API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from duxos_escrow.governance_api import router
from duxos_escrow.models import (
    Proposal, Vote, ProposalStatus, ProposalCategory, VoteType,
    Base
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
    Base.metadata.create_all(engine)
    
    yield session
    
    session.close()

@pytest.fixture
def mock_governance_manager():
    """Create a mock governance manager"""
    return Mock()

@pytest.fixture
def client(mock_governance_manager):
    """Create a test client with mocked dependencies"""
    from duxos_escrow.governance_api import governance_manager, get_governance_manager
    
    # Set the global governance manager
    governance_manager = mock_governance_manager
    
    # Patch the dependency
    with patch('duxos_escrow.governance_api.get_governance_manager', return_value=mock_governance_manager):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

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

@pytest.fixture
def sample_proposal(sample_proposal_data):
    """Create a sample proposal object"""
    proposal = Mock()
    proposal.id = "test-proposal-id"
    proposal.title = sample_proposal_data["title"]
    proposal.description = sample_proposal_data["description"]
    proposal.category = sample_proposal_data["category"]
    proposal.status = ProposalStatus.DRAFT
    proposal.proposer_wallet_id = sample_proposal_data["proposer_wallet_id"]
    proposal.required_quorum = sample_proposal_data["required_quorum"]
    proposal.voting_period_days = sample_proposal_data["voting_period_days"]
    proposal.estimated_cost = sample_proposal_data["estimated_cost"]
    proposal.funding_source = sample_proposal_data["funding_source"]
    proposal.created_at = "2024-01-01T00:00:00Z"
    proposal.voting_started_at = None
    proposal.voting_ends_at = None
    proposal.executed_at = None
    proposal.executed_by = None
    return proposal

@pytest.fixture
def sample_vote():
    """Create a sample vote object"""
    vote = Mock()
    vote.id = "test-vote-id"
    vote.proposal_id = "test-proposal-id"
    vote.voter_wallet_id = 2
    vote.vote_type = VoteType.YES
    vote.voting_power = 50.0
    vote.reason = "I support this proposal"
    vote.created_at = "2024-01-01T00:00:00Z"
    return vote

class TestGovernanceAPI:
    """Test cases for Governance API endpoints"""
    
    def test_create_proposal_success(self, client, mock_governance_manager, sample_proposal_data, sample_proposal):
        """Test successful proposal creation"""
        mock_governance_manager.create_proposal.return_value = sample_proposal
        
        response = client.post(
            "/governance/proposals",
            json=sample_proposal_data,
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_proposal.id
        assert data["title"] == sample_proposal_data["title"]
        assert data["category"] == sample_proposal_data["category"]
        
        mock_governance_manager.create_proposal.assert_called_once()
    
    def test_create_proposal_missing_api_key(self, client, sample_proposal_data):
        """Test proposal creation without API key"""
        response = client.post("/governance/proposals", json=sample_proposal_data)
        
        assert response.status_code == 401
        assert "Invalid or missing API key" in response.json()["detail"]
    
    def test_create_proposal_validation_error(self, client, mock_governance_manager, sample_proposal_data):
        """Test proposal creation with validation error"""
        mock_governance_manager.create_proposal.side_effect = GovernanceError("Invalid title")
        
        response = client.post(
            "/governance/proposals",
            json=sample_proposal_data,
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 400
        assert "Invalid title" in response.json()["detail"]
    
    def test_get_proposals_active(self, client, mock_governance_manager, sample_proposal):
        """Test getting active proposals"""
        mock_governance_manager.get_active_proposals.return_value = [sample_proposal]
        
        response = client.get("/governance/proposals")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_proposal.id
        
        mock_governance_manager.get_active_proposals.assert_called_once()
    
    def test_get_proposals_by_status(self, client, mock_governance_manager, sample_proposal):
        """Test getting proposals by status"""
        mock_governance_manager.get_proposals_by_status.return_value = [sample_proposal]
        
        response = client.get("/governance/proposals?status=draft")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        mock_governance_manager.get_proposals_by_status.assert_called_once_with(ProposalStatus.DRAFT)
    
    def test_get_proposals_by_category(self, client, mock_governance_manager, sample_proposal):
        """Test getting proposals by category"""
        mock_governance_manager.get_proposals_by_category.return_value = [sample_proposal]
        
        response = client.get("/governance/proposals?category=community_fund")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        
        mock_governance_manager.get_proposals_by_category.assert_called_once_with(ProposalCategory.COMMUNITY_FUND)
    
    def test_get_proposal_success(self, client, mock_governance_manager, sample_proposal):
        """Test getting a specific proposal"""
        mock_governance_manager.get_proposal.return_value = sample_proposal
        
        response = client.get("/governance/proposals/test-proposal-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_proposal.id
        assert data["title"] == sample_proposal.title
        
        mock_governance_manager.get_proposal.assert_called_once_with("test-proposal-id")
    
    def test_get_proposal_not_found(self, client, mock_governance_manager):
        """Test getting non-existent proposal"""
        mock_governance_manager.get_proposal.side_effect = ProposalNotFoundError("Proposal not found")
        
        response = client.get("/governance/proposals/non-existent-id")
        
        assert response.status_code == 404
        assert "Proposal not found" in response.json()["detail"]
    
    def test_activate_proposal_success(self, client, mock_governance_manager, sample_proposal):
        """Test successful proposal activation"""
        mock_governance_manager.activate_proposal.return_value = sample_proposal
        
        response = client.post(
            "/governance/proposals/test-proposal-id/activate",
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_proposal.id
        
        mock_governance_manager.activate_proposal.assert_called_once_with("test-proposal-id")
    
    def test_activate_proposal_error(self, client, mock_governance_manager):
        """Test proposal activation error"""
        mock_governance_manager.activate_proposal.side_effect = GovernanceError("Cannot activate")
        
        response = client.post(
            "/governance/proposals/test-proposal-id/activate",
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 400
        assert "Cannot activate" in response.json()["detail"]
    
    def test_cast_vote_success(self, client, mock_governance_manager, sample_vote):
        """Test successful vote casting"""
        mock_governance_manager.cast_vote.return_value = sample_vote
        
        vote_data = {
            "proposal_id": "test-proposal-id",
            "voter_wallet_id": 2,
            "vote_type": "yes",
            "voting_power": 50.0,
            "reason": "I support this proposal"
        }
        
        response = client.post(
            "/governance/proposals/test-proposal-id/vote",
            json=vote_data,
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_vote.id
        assert data["vote_type"] == "yes"
        assert data["voting_power"] == 50.0
        
        mock_governance_manager.cast_vote.assert_called_once()
    
    def test_cast_vote_already_voted(self, client, mock_governance_manager):
        """Test casting vote when already voted"""
        mock_governance_manager.cast_vote.side_effect = AlreadyVotedError("Already voted")
        
        vote_data = {
            "proposal_id": "test-proposal-id",
            "voter_wallet_id": 2,
            "vote_type": "yes",
            "voting_power": 50.0
        }
        
        response = client.post(
            "/governance/proposals/test-proposal-id/vote",
            json=vote_data,
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 400
        assert "Already voted" in response.json()["detail"]
    
    def test_get_vote_results_success(self, client, mock_governance_manager):
        """Test getting vote results"""
        results = {
            "proposal_id": "test-proposal-id",
            "total_votes": 2,
            "total_voting_power": 100.0,
            "yes_votes": 1,
            "no_votes": 1,
            "abstain_votes": 0,
            "yes_power": 60.0,
            "no_power": 40.0,
            "abstain_power": 0.0,
            "yes_percentage": 60.0,
            "no_percentage": 40.0,
            "abstain_percentage": 0.0,
            "required_quorum": 100.0,
            "quorum_met": True,
            "outcome": "pending",
            "voting_active": True,
            "voting_ends_at": "2024-01-08T00:00:00Z"
        }
        
        mock_governance_manager.get_vote_results.return_value = results
        
        response = client.get("/governance/proposals/test-proposal-id/results")
        
        assert response.status_code == 200
        data = response.json()
        assert data["proposal_id"] == "test-proposal-id"
        assert data["total_votes"] == 2
        assert data["quorum_met"] == True
        
        mock_governance_manager.get_vote_results.assert_called_once_with("test-proposal-id")
    
    def test_get_vote_results_not_found(self, client, mock_governance_manager):
        """Test getting vote results for non-existent proposal"""
        mock_governance_manager.get_vote_results.side_effect = ProposalNotFoundError("Proposal not found")
        
        response = client.get("/governance/proposals/non-existent-id/results")
        
        assert response.status_code == 404
        assert "Proposal not found" in response.json()["detail"]
    
    def test_finalize_proposal_success(self, client, mock_governance_manager, sample_proposal):
        """Test successful proposal finalization"""
        mock_governance_manager.finalize_proposal.return_value = sample_proposal
        
        response = client.post(
            "/governance/proposals/test-proposal-id/finalize",
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_proposal.id
        
        mock_governance_manager.finalize_proposal.assert_called_once_with("test-proposal-id")
    
    def test_execute_proposal_success(self, client, mock_governance_manager, sample_proposal):
        """Test successful proposal execution"""
        mock_governance_manager.execute_proposal.return_value = sample_proposal
        
        response = client.post(
            "/governance/proposals/test-proposal-id/execute?executor_wallet_id=5",
            headers={"x-api-key": "supersecretapikey123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_proposal.id
        
        mock_governance_manager.execute_proposal.assert_called_once_with("test-proposal-id", 5)
    
    def test_get_voter_history(self, client, mock_governance_manager, sample_vote):
        """Test getting voter history"""
        mock_governance_manager.get_voter_history.return_value = [sample_vote]
        
        response = client.get("/governance/votes/history/2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["voter_wallet_id"] == 2
        
        mock_governance_manager.get_voter_history.assert_called_once_with(2)
    
    def test_get_proposal_votes(self, client, mock_governance_manager, sample_vote):
        """Test getting all votes for a proposal"""
        mock_governance_manager.get_proposal_votes.return_value = [sample_vote]
        
        response = client.get("/governance/proposals/test-proposal-id/votes")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["proposal_id"] == "test-proposal-id"
        
        mock_governance_manager.get_proposal_votes.assert_called_once_with("test-proposal-id")
    
    def test_get_governance_stats(self, client, mock_governance_manager):
        """Test getting governance statistics"""
        stats = {
            "total_proposals": 5,
            "active_proposals": 2,
            "passed_proposals": 2,
            "executed_proposals": 1,
            "total_votes": 15,
            "total_voting_power": 500.0
        }
        
        mock_governance_manager.get_governance_stats.return_value = stats
        
        response = client.get("/governance/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_proposals"] == 5
        assert data["active_proposals"] == 2
        assert data["total_voting_power"] == 500.0
        
        mock_governance_manager.get_governance_stats.assert_called_once() 