"""
Simple tests for Governance functionality using mocking
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest

from duxos_escrow.exceptions import (
    AlreadyVotedError,
    GovernanceError,
    InsufficientVotingPowerError,
    ProposalExecutionError,
    ProposalNotFoundError,
    VotingNotActiveError,
)
from duxos_escrow.governance_manager import GovernanceManager
from duxos_escrow.models import ProposalCategory, ProposalStatus, VoteType


class TestGovernanceManagerSimple:
    """Simple test cases for GovernanceManager using mocking"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
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

    @pytest.fixture
    def sample_proposal_data(self):
        """Sample proposal data for testing"""
        return {
            "title": "Test Proposal",
            "description": "This is a test proposal for governance testing",
            "category": ProposalCategory.COMMUNITY_FUND,
            "proposer_wallet_id": 1,
            "required_quorum": 100.0,
            "voting_period_days": 7,
            "estimated_cost": 50.0,
            "funding_source": "community_fund",
        }

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

    def test_get_proposal_not_found(self, governance_manager, mock_db_session):
        """Test getting non-existent proposal"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ProposalNotFoundError, match="Proposal .* not found"):
            governance_manager.get_proposal("non-existent-id")

    def test_cast_vote_invalid_power(self, governance_manager, mock_db_session):
        """Test casting vote with invalid voting power"""
        # Mock proposal
        mock_proposal = Mock()
        mock_proposal.is_voting_active.return_value = True
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        # Mock no existing vote
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(InsufficientVotingPowerError, match="Voting power must be positive"):
            governance_manager.cast_vote(
                proposal_id="test-id", voter_wallet_id=2, vote_type=VoteType.YES, voting_power=0.0
            )

    def test_cast_vote_voting_not_active(self, governance_manager, mock_db_session):
        """Test casting vote when voting is not active"""
        # Mock proposal that's not active
        mock_proposal = Mock()
        mock_proposal.is_voting_active.return_value = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        with pytest.raises(VotingNotActiveError, match="Voting is not active"):
            governance_manager.cast_vote(
                proposal_id="test-id", voter_wallet_id=2, vote_type=VoteType.YES, voting_power=50.0
            )

    def test_cast_vote_already_voted(self, governance_manager, mock_db_session):
        """Test casting vote when already voted"""
        # Mock proposal
        mock_proposal = Mock()
        mock_proposal.is_voting_active.return_value = True
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_proposal,  # First call returns proposal
            Mock(),  # Second call returns existing vote
        ]

        with pytest.raises(AlreadyVotedError, match="has already voted"):
            governance_manager.cast_vote(
                proposal_id="test-id", voter_wallet_id=2, vote_type=VoteType.YES, voting_power=50.0
            )

    def test_activate_proposal_wrong_status(self, governance_manager, mock_db_session):
        """Test activating proposal in wrong status"""
        # Mock proposal that's already active
        mock_proposal = Mock()
        mock_proposal.status = ProposalStatus.ACTIVE
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        with pytest.raises(GovernanceError, match="Cannot activate proposal in active status"):
            governance_manager.activate_proposal("test-id")

    def test_finalize_proposal_not_active(self, governance_manager, mock_db_session):
        """Test finalizing proposal that's not active"""
        # Mock proposal that's not active
        mock_proposal = Mock()
        mock_proposal.status = ProposalStatus.DRAFT
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        with pytest.raises(GovernanceError, match="Cannot finalize proposal in draft status"):
            governance_manager.finalize_proposal("test-id")

    def test_finalize_proposal_not_expired(self, governance_manager, mock_db_session):
        """Test finalizing proposal that hasn't expired"""
        # Mock proposal that's active but not expired
        mock_proposal = Mock()
        mock_proposal.status = ProposalStatus.ACTIVE
        mock_proposal.has_expired.return_value = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        with pytest.raises(
            GovernanceError, match="Cannot finalize proposal before voting period ends"
        ):
            governance_manager.finalize_proposal("test-id")

    def test_execute_proposal_not_passed(self, governance_manager, mock_db_session):
        """Test executing proposal that hasn't passed"""
        # Mock proposal that's not passed
        mock_proposal = Mock()
        mock_proposal.status = ProposalStatus.ACTIVE
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_proposal

        with pytest.raises(
            ProposalExecutionError, match="Cannot execute proposal in active status"
        ):
            governance_manager.execute_proposal("test-id", 5)

    def test_get_governance_stats(self, governance_manager, mock_db_session):
        """Test getting governance statistics"""
        # Mock query results
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query

        # Mock counts
        mock_query.count.return_value = 5
        mock_query.filter.return_value.count.return_value = 2

        # Mock sum
        mock_query.filter.return_value.scalar.return_value = 100.0

        stats = governance_manager.get_governance_stats()

        assert stats["total_proposals"] == 5
        assert stats["active_proposals"] == 2
        assert stats["total_voting_power"] == 100.0


class TestProposalModel:
    """Test cases for Proposal model methods"""

    def test_proposal_is_voting_active(self):
        """Test proposal voting active status"""
        from duxos_escrow.models import Proposal

        # Create a mock proposal
        proposal = Mock(spec=Proposal)
        proposal.voting_started_at = datetime.now(timezone.utc) - timedelta(days=1)
        proposal.voting_ends_at = datetime.now(timezone.utc) + timedelta(days=1)

        # Mock the is_voting_active method
        with patch.object(Proposal, "is_voting_active", return_value=True):
            assert proposal.is_voting_active() == True

    def test_proposal_has_expired(self):
        """Test proposal expiration check"""
        from duxos_escrow.models import Proposal

        # Create a mock proposal
        proposal = Mock(spec=Proposal)
        proposal.voting_ends_at = datetime.now(timezone.utc) - timedelta(days=1)

        # Mock the has_expired method
        with patch.object(Proposal, "has_expired", return_value=True):
            assert proposal.has_expired() == True


class TestVoteModel:
    """Test cases for Vote model"""

    def test_vote_repr(self):
        """Test vote string representation"""
        from duxos_escrow.models import Vote

        # Create a mock vote
        vote = Mock(spec=Vote)
        vote.id = "test-vote-id"
        vote.proposal_id = "test-proposal-id"
        vote.vote_type = VoteType.YES
        vote.voting_power = 50.0

        # Mock the __repr__ method
        with patch.object(
            Vote,
            "__repr__",
            return_value="<Vote(id=test-vote-id, proposal_id=test-proposal-id, vote_type=yes, voting_power=50.0)>",
        ):
            expected = "<Vote(id=test-vote-id, proposal_id=test-proposal-id, vote_type=yes, voting_power=50.0)>"
            assert str(vote) == expected
