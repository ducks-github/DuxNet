"""
Integration test for Governance System workflow
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, timezone

from duxos_escrow.governance_manager import GovernanceManager
from duxos_escrow.models import ProposalStatus, ProposalCategory, VoteType
from duxos_escrow.exceptions import (
    GovernanceError, ProposalNotFoundError, VotingNotActiveError,
    AlreadyVotedError, InsufficientVotingPowerError, ProposalExecutionError
)

class TestGovernanceIntegration:
    """Integration test for complete governance workflow"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a comprehensive mock database session"""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.query = Mock()
        return session
    
    @pytest.fixture
    def governance_manager(self, mock_db_session):
        """Create a governance manager with mocked database"""
        return GovernanceManager(mock_db_session)
    
    def test_complete_governance_workflow(self, governance_manager, mock_db_session):
        """Test a complete governance workflow from proposal to execution"""
        
        # Mock proposal data
        proposal_data = {
            "title": "Community Fund Airdrop",
            "description": "Distribute 1000 FLOP to active community members based on their participation",
            "category": ProposalCategory.COMMUNITY_FUND,
            "proposer_wallet_id": 1,
            "required_quorum": 100.0,
            "voting_period_days": 7,
            "estimated_cost": 1000.0,
            "funding_source": "community_fund"
        }
        
        # Step 1: Create proposal
        mock_proposal = Mock()
        mock_proposal.id = "proposal-123"
        mock_proposal.title = proposal_data["title"]
        mock_proposal.description = proposal_data["description"]
        mock_proposal.category = proposal_data["category"]
        mock_proposal.status = ProposalStatus.DRAFT
        mock_proposal.proposer_wallet_id = proposal_data["proposer_wallet_id"]
        mock_proposal.required_quorum = proposal_data["required_quorum"]
        mock_proposal.voting_period_days = proposal_data["voting_period_days"]
        mock_proposal.estimated_cost = proposal_data["estimated_cost"]
        mock_proposal.funding_source = proposal_data["funding_source"]
        mock_proposal.created_at = datetime.now(timezone.utc)
        mock_proposal.voting_started_at = None
        mock_proposal.voting_ends_at = None
        mock_proposal.executed_at = None
        mock_proposal.executed_by = None
        
        # Mock the create_proposal method
        with patch.object(governance_manager, 'create_proposal', return_value=mock_proposal):
            proposal = governance_manager.create_proposal(**proposal_data)
            
            assert proposal.id == "proposal-123"
            assert proposal.title == "Community Fund Airdrop"
            assert proposal.status == ProposalStatus.DRAFT
        
        # Step 2: Activate proposal
        mock_proposal.status = ProposalStatus.ACTIVE
        mock_proposal.voting_started_at = datetime.now(timezone.utc)
        mock_proposal.voting_ends_at = datetime.now(timezone.utc) + timedelta(days=7)
        mock_proposal.is_voting_active.return_value = True
        mock_proposal.has_expired.return_value = False
        
        with patch.object(governance_manager, 'activate_proposal', return_value=mock_proposal):
            activated_proposal = governance_manager.activate_proposal("proposal-123")
            
            assert activated_proposal.status == ProposalStatus.ACTIVE
            assert activated_proposal.voting_started_at is not None
            assert activated_proposal.voting_ends_at is not None
        
        # Step 3: Cast votes
        mock_vote1 = Mock()
        mock_vote1.id = "vote-1"
        mock_vote1.proposal_id = "proposal-123"
        mock_vote1.voter_wallet_id = 2
        mock_vote1.vote_type = VoteType.YES
        mock_vote1.voting_power = 60.0
        mock_vote1.reason = "I support this airdrop"
        mock_vote1.created_at = datetime.now(timezone.utc)
        
        mock_vote2 = Mock()
        mock_vote2.id = "vote-2"
        mock_vote2.proposal_id = "proposal-123"
        mock_vote2.voter_wallet_id = 3
        mock_vote2.vote_type = VoteType.NO
        mock_vote2.voting_power = 30.0
        mock_vote2.reason = "I think the amount is too high"
        mock_vote2.created_at = datetime.now(timezone.utc)
        
        mock_vote3 = Mock()
        mock_vote3.id = "vote-3"
        mock_vote3.proposal_id = "proposal-123"
        mock_vote3.voter_wallet_id = 4
        mock_vote3.vote_type = VoteType.ABSTAIN
        mock_vote3.voting_power = 10.0
        mock_vote3.reason = "I'm not sure about this"
        mock_vote3.created_at = datetime.now(timezone.utc)
        
        # Mock the cast_vote method
        with patch.object(governance_manager, 'cast_vote', side_effect=[mock_vote1, mock_vote2, mock_vote3]):
            # Cast first vote
            vote1 = governance_manager.cast_vote(
                proposal_id="proposal-123",
                voter_wallet_id=2,
                vote_type=VoteType.YES,
                voting_power=60.0,
                reason="I support this airdrop"
            )
            assert vote1.vote_type == VoteType.YES
            assert vote1.voting_power == 60.0
            
            # Cast second vote
            vote2 = governance_manager.cast_vote(
                proposal_id="proposal-123",
                voter_wallet_id=3,
                vote_type=VoteType.NO,
                voting_power=30.0,
                reason="I think the amount is too high"
            )
            assert vote2.vote_type == VoteType.NO
            assert vote2.voting_power == 30.0
            
            # Cast third vote
            vote3 = governance_manager.cast_vote(
                proposal_id="proposal-123",
                voter_wallet_id=4,
                vote_type=VoteType.ABSTAIN,
                voting_power=10.0,
                reason="I'm not sure about this"
            )
            assert vote3.vote_type == VoteType.ABSTAIN
            assert vote3.voting_power == 10.0
        
        # Step 4: Get vote results
        expected_results = {
            "proposal_id": "proposal-123",
            "total_votes": 3,
            "total_voting_power": 100.0,
            "yes_votes": 1,
            "no_votes": 1,
            "abstain_votes": 1,
            "yes_power": 60.0,
            "no_power": 30.0,
            "abstain_power": 10.0,
            "yes_percentage": 60.0,
            "no_percentage": 30.0,
            "abstain_percentage": 10.0,
            "required_quorum": 100.0,
            "quorum_met": True,
            "outcome": "pending",
            "voting_active": True,
            "voting_ends_at": mock_proposal.voting_ends_at
        }
        
        with patch.object(governance_manager, 'get_vote_results', return_value=expected_results):
            results = governance_manager.get_vote_results("proposal-123")
            
            assert results["total_votes"] == 3
            assert results["total_voting_power"] == 100.0
            assert results["quorum_met"] == True
            assert results["yes_percentage"] == 60.0
            assert results["no_percentage"] == 30.0
            assert results["abstain_percentage"] == 10.0
        
        # Step 5: Finalize proposal (after voting period ends)
        mock_proposal.has_expired.return_value = True
        mock_proposal.status = ProposalStatus.PASSED
        
        with patch.object(governance_manager, 'finalize_proposal', return_value=mock_proposal):
            finalized_proposal = governance_manager.finalize_proposal("proposal-123")
            
            assert finalized_proposal.status == ProposalStatus.PASSED
        
        # Step 6: Execute proposal
        mock_proposal.executed_at = datetime.now(timezone.utc)
        mock_proposal.executed_by = 5
        mock_proposal.status = ProposalStatus.EXECUTED
        
        with patch.object(governance_manager, 'execute_proposal', return_value=mock_proposal):
            executed_proposal = governance_manager.execute_proposal("proposal-123", 5)
            
            assert executed_proposal.status == ProposalStatus.EXECUTED
            assert executed_proposal.executed_at is not None
            assert executed_proposal.executed_by == 5
    
    def test_governance_error_handling(self, governance_manager, mock_db_session):
        """Test error handling in governance workflow"""
        
        # Test proposal not found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ProposalNotFoundError, match="Proposal .* not found"):
            governance_manager.get_proposal("non-existent-id")
        
        # Test voting on inactive proposal
        mock_proposal = Mock()
        mock_proposal.is_voting_active.return_value = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal
        
        with pytest.raises(VotingNotActiveError, match="Voting is not active"):
            governance_manager.cast_vote(
                proposal_id="test-id",
                voter_wallet_id=1,
                vote_type=VoteType.YES,
                voting_power=50.0
            )
        
        # Test duplicate voting
        mock_proposal.is_voting_active.return_value = True
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_proposal,  # First call returns proposal
            Mock()  # Second call returns existing vote
        ]
        
        with pytest.raises(AlreadyVotedError, match="has already voted"):
            governance_manager.cast_vote(
                proposal_id="test-id",
                voter_wallet_id=1,
                vote_type=VoteType.YES,
                voting_power=50.0
            )
    
    def test_governance_statistics(self, governance_manager, mock_db_session):
        """Test governance statistics calculation"""
        
        # Mock statistics data
        expected_stats = {
            "total_proposals": 10,
            "active_proposals": 2,
            "passed_proposals": 5,
            "executed_proposals": 3,
            "total_votes": 50,
            "total_voting_power": 2500.0
        }
        
        with patch.object(governance_manager, 'get_governance_stats', return_value=expected_stats):
            stats = governance_manager.get_governance_stats()
            
            assert stats["total_proposals"] == 10
            assert stats["active_proposals"] == 2
            assert stats["passed_proposals"] == 5
            assert stats["executed_proposals"] == 3
            assert stats["total_votes"] == 50
            assert stats["total_voting_power"] == 2500.0
            
            # Calculate some derived metrics
            pass_rate = stats["passed_proposals"] / stats["total_proposals"] * 100
            execution_rate = stats["executed_proposals"] / stats["passed_proposals"] * 100
            avg_voting_power = stats["total_voting_power"] / stats["total_votes"]
            
            assert pass_rate == 50.0  # 5/10 * 100
            assert execution_rate == 60.0  # 3/5 * 100
            assert avg_voting_power == 50.0  # 2500/50

class TestGovernanceAPI:
    """Test governance API endpoints"""
    
    def test_api_endpoints_structure(self):
        """Test that all required API endpoints are defined"""
        from duxos_escrow.governance_api import router
        
        # Check that router has the expected routes
        routes = [route.path for route in router.routes]
        
        expected_routes = [
            "/governance/proposals",
            "/governance/proposals/{proposal_id}",
            "/governance/proposals/{proposal_id}/activate",
            "/governance/proposals/{proposal_id}/vote",
            "/governance/proposals/{proposal_id}/results",
            "/governance/proposals/{proposal_id}/finalize",
            "/governance/proposals/{proposal_id}/execute",
            "/governance/votes/history/{voter_wallet_id}",
            "/governance/proposals/{proposal_id}/votes",
            "/governance/stats"
        ]
        
        for route in expected_routes:
            assert any(route in r for r in routes), f"Missing route: {route}"
    
    def test_api_request_models(self):
        """Test API request/response models"""
        from duxos_escrow.governance_api import (
            ProposalCreateRequest, VoteRequest, ProposalResponse, VoteResponse
        )
        
        # Test proposal creation request
        proposal_data = {
            "title": "Test Proposal",
            "description": "This is a test proposal",
            "category": ProposalCategory.COMMUNITY_FUND,
            "proposer_wallet_id": 1,
            "required_quorum": 100.0,
            "voting_period_days": 7,
            "estimated_cost": 50.0,
            "funding_source": "community_fund"
        }
        
        request = ProposalCreateRequest(**proposal_data)
        assert request.title == "Test Proposal"
        assert request.category == ProposalCategory.COMMUNITY_FUND
        
        # Test vote request
        vote_data = {
            "proposal_id": "test-123",
            "voter_wallet_id": 2,
            "vote_type": VoteType.YES,
            "voting_power": 50.0,
            "reason": "I support this"
        }
        
        request = VoteRequest(**vote_data)
        assert request.proposal_id == "test-123"
        assert request.vote_type == VoteType.YES 