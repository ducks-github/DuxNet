"""
Governance Manager for DuxOS Escrow System
Handles proposal creation, voting, and execution
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from .exceptions import (
    AlreadyVotedError,
    GovernanceError,
    InsufficientVotingPowerError,
    ProposalExecutionError,
    ProposalNotFoundError,
    VotingNotActiveError,
)
from .models import Proposal, ProposalCategory, ProposalStatus, Vote, VoteType


class GovernanceManager:
    """Manages governance proposals and voting"""

    def __init__(self, db: Session):
        self.db = db

    def create_proposal(
        self,
        title: str,
        description: str,
        category: ProposalCategory,
        proposer_wallet_id: int,
        required_quorum: float,
        voting_period_days: int = 7,
        estimated_cost: Optional[float] = None,
        funding_source: Optional[str] = None,
        execution_data: Optional[Dict[str, Any]] = None,
    ) -> Proposal:
        """Create a new governance proposal"""

        # Validate inputs
        if not title or len(title.strip()) < 5:
            raise GovernanceError("Proposal title must be at least 5 characters")

        if not description or len(description.strip()) < 20:
            raise GovernanceError("Proposal description must be at least 20 characters")

        if required_quorum <= 0:
            raise GovernanceError("Required quorum must be positive")

        if voting_period_days < 1 or voting_period_days > 30:
            raise GovernanceError("Voting period must be between 1 and 30 days")

        # Create proposal
        proposal = Proposal(
            id=str(uuid.uuid4()),
            title=title.strip(),
            description=description.strip(),
            category=category,
            proposer_wallet_id=proposer_wallet_id,
            required_quorum=required_quorum,
            voting_period_days=voting_period_days,
            estimated_cost=estimated_cost,
            funding_source=funding_source,
            status=ProposalStatus.DRAFT,
        )

        if execution_data:
            proposal.set_execution_data(execution_data)

        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)

        return proposal

    def activate_proposal(self, proposal_id: str) -> Proposal:
        """Activate a proposal for voting"""
        proposal = self.get_proposal(proposal_id)

        if proposal.status != ProposalStatus.DRAFT:
            raise GovernanceError(f"Cannot activate proposal in {proposal.status} status")

        # Set voting period
        now = datetime.now(timezone.utc)
        proposal.voting_started_at = now
        proposal.voting_ends_at = now + timedelta(days=proposal.voting_period_days)
        proposal.status = ProposalStatus.ACTIVE

        self.db.commit()
        self.db.refresh(proposal)

        return proposal

    def get_proposal(self, proposal_id: str) -> Proposal:
        """Get a proposal by ID"""
        proposal = self.db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ProposalNotFoundError(f"Proposal {proposal_id} not found")
        return proposal

    def get_active_proposals(self) -> List[Proposal]:
        """Get all active proposals"""
        return (
            self.db.query(Proposal)
            .filter(Proposal.status == ProposalStatus.ACTIVE)
            .order_by(desc(Proposal.created_at))
            .all()
        )

    def get_proposals_by_category(self, category: ProposalCategory) -> List[Proposal]:
        """Get proposals by category"""
        return (
            self.db.query(Proposal)
            .filter(Proposal.category == category)
            .order_by(desc(Proposal.created_at))
            .all()
        )

    def get_proposals_by_status(self, status: ProposalStatus) -> List[Proposal]:
        """Get proposals by status"""
        return (
            self.db.query(Proposal)
            .filter(Proposal.status == status)
            .order_by(desc(Proposal.created_at))
            .all()
        )

    def cast_vote(
        self,
        proposal_id: str,
        voter_wallet_id: int,
        vote_type: VoteType,
        voting_power: float,
        reason: Optional[str] = None,
    ) -> Vote:
        """Cast a vote on a proposal"""

        proposal = self.get_proposal(proposal_id)

        # Check if voting is active
        if not proposal.is_voting_active():
            raise VotingNotActiveError(f"Voting is not active for proposal {proposal_id}")

        # Check if already voted
        existing_vote = (
            self.db.query(Vote)
            .filter(and_(Vote.proposal_id == proposal_id, Vote.voter_wallet_id == voter_wallet_id))
            .first()
        )

        if existing_vote:
            raise AlreadyVotedError(
                f"Wallet {voter_wallet_id} has already voted on proposal {proposal_id}"
            )

        # Validate voting power
        if voting_power <= 0:
            raise InsufficientVotingPowerError("Voting power must be positive")

        # Create vote
        vote = Vote(
            id=str(uuid.uuid4()),
            proposal_id=proposal_id,
            voter_wallet_id=voter_wallet_id,
            vote_type=vote_type,
            voting_power=voting_power,
            reason=reason,
        )

        self.db.add(vote)
        self.db.commit()
        self.db.refresh(vote)

        return vote

    def get_vote_results(self, proposal_id: str) -> Dict[str, Any]:
        """Get voting results for a proposal"""
        proposal = self.get_proposal(proposal_id)

        # Get all votes
        votes = self.db.query(Vote).filter(Vote.proposal_id == proposal_id).all()

        # Calculate totals
        total_votes = len(votes)
        total_voting_power = sum(vote.voting_power for vote in votes)

        yes_votes = [v for v in votes if v.vote_type == VoteType.YES]
        no_votes = [v for v in votes if v.vote_type == VoteType.NO]
        abstain_votes = [v for v in votes if v.vote_type == VoteType.ABSTAIN]

        yes_power = sum(v.voting_power for v in yes_votes)
        no_power = sum(v.voting_power for v in no_votes)
        abstain_power = sum(v.voting_power for v in abstain_votes)

        # Calculate percentages
        yes_percentage = (yes_power / total_voting_power * 100) if total_voting_power > 0 else 0
        no_percentage = (no_power / total_voting_power * 100) if total_voting_power > 0 else 0
        abstain_percentage = (
            (abstain_power / total_voting_power * 100) if total_voting_power > 0 else 0
        )

        # Check if quorum is met
        quorum_met = total_voting_power >= proposal.required_quorum

        # Determine outcome
        outcome = "pending"
        if proposal.has_expired() or proposal.status in [
            ProposalStatus.PASSED,
            ProposalStatus.REJECTED,
        ]:
            if quorum_met and yes_power > no_power:
                outcome = "passed"
            elif quorum_met and no_power >= yes_power:
                outcome = "rejected"
            else:
                outcome = "failed_quorum"

        return {
            "proposal_id": proposal_id,
            "total_votes": total_votes,
            "total_voting_power": total_voting_power,
            "yes_votes": len(yes_votes),
            "no_votes": len(no_votes),
            "abstain_votes": len(abstain_votes),
            "yes_power": yes_power,
            "no_power": no_power,
            "abstain_power": abstain_power,
            "yes_percentage": round(yes_percentage, 2),
            "no_percentage": round(no_percentage, 2),
            "abstain_percentage": round(abstain_percentage, 2),
            "required_quorum": proposal.required_quorum,
            "quorum_met": quorum_met,
            "outcome": outcome,
            "voting_active": proposal.is_voting_active(),
            "voting_ends_at": proposal.voting_ends_at,
        }

    def finalize_proposal(self, proposal_id: str) -> Proposal:
        """Finalize a proposal based on voting results"""
        proposal = self.get_proposal(proposal_id)

        if proposal.status != ProposalStatus.ACTIVE:
            raise GovernanceError(f"Cannot finalize proposal in {proposal.status} status")

        if not proposal.has_expired():
            raise GovernanceError("Cannot finalize proposal before voting period ends")

        # Get voting results
        results = self.get_vote_results(proposal_id)

        # Update proposal status
        if results["outcome"] == "passed":
            proposal.status = ProposalStatus.PASSED
        elif results["outcome"] == "rejected":
            proposal.status = ProposalStatus.REJECTED
        else:
            proposal.status = ProposalStatus.EXPIRED

        self.db.commit()
        self.db.refresh(proposal)

        return proposal

    def execute_proposal(self, proposal_id: str, executor_wallet_id: int) -> Proposal:
        """Execute a passed proposal"""
        proposal = self.get_proposal(proposal_id)

        if proposal.status != ProposalStatus.PASSED:
            raise ProposalExecutionError(f"Cannot execute proposal in {proposal.status} status")

        # Mark as executed
        proposal.status = ProposalStatus.EXECUTED
        proposal.executed_at = datetime.now(timezone.utc)
        proposal.executed_by = executor_wallet_id

        self.db.commit()
        self.db.refresh(proposal)

        return proposal

    def get_voter_history(self, voter_wallet_id: int) -> List[Vote]:
        """Get voting history for a wallet"""
        return (
            self.db.query(Vote)
            .filter(Vote.voter_wallet_id == voter_wallet_id)
            .order_by(desc(Vote.created_at))
            .all()
        )

    def get_proposal_votes(self, proposal_id: str) -> List[Vote]:
        """Get all votes for a proposal"""
        return (
            self.db.query(Vote)
            .filter(Vote.proposal_id == proposal_id)
            .order_by(Vote.created_at)
            .all()
        )

    def get_governance_stats(self) -> Dict[str, Any]:
        """Get governance statistics"""
        total_proposals = self.db.query(Proposal).count()
        active_proposals = (
            self.db.query(Proposal).filter(Proposal.status == ProposalStatus.ACTIVE).count()
        )
        passed_proposals = (
            self.db.query(Proposal).filter(Proposal.status == ProposalStatus.PASSED).count()
        )
        executed_proposals = (
            self.db.query(Proposal).filter(Proposal.status == ProposalStatus.EXECUTED).count()
        )

        total_votes = self.db.query(Vote).count()
        total_voting_power = self.db.query(func.sum(Vote.voting_power)).scalar() or 0

        return {
            "total_proposals": total_proposals,
            "active_proposals": active_proposals,
            "passed_proposals": passed_proposals,
            "executed_proposals": executed_proposals,
            "total_votes": total_votes,
            "total_voting_power": total_voting_power,
        }
