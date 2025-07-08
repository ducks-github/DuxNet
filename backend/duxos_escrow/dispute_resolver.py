"""
Dispute Resolver for DuxOS Escrow System
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .models import Dispute, DisputeStatus, Escrow, EscrowStatus

logger = logging.getLogger(__name__)


class DisputeResolver:
    """Handles dispute resolution for escrow contracts"""

    def __init__(self, db: Session):
        self.db = db

    def create_dispute(
        self,
        escrow_id: str,
        initiator_wallet_id: int,
        reason: str,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Dispute:
        """Create a new dispute for an escrow"""

        # Validate escrow exists and is in disputable state
        escrow = self.db.query(Escrow).filter(Escrow.id == escrow_id).first()
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")

        if escrow.status not in [EscrowStatus.ACTIVE, EscrowStatus.RELEASED]:
            raise ValueError(f"Escrow {escrow_id} cannot be disputed (status: {escrow.status})")

        # Determine respondent (the other party)
        if initiator_wallet_id == escrow.payer_wallet_id:
            respondent_wallet_id = escrow.provider_wallet_id
        elif initiator_wallet_id == escrow.provider_wallet_id:
            respondent_wallet_id = escrow.payer_wallet_id
        else:
            raise ValueError("Initiator must be either payer or provider")

        # Create dispute
        dispute = Dispute(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            status=DisputeStatus.OPEN,
            reason=reason,
            initiator_wallet_id=initiator_wallet_id,
            respondent_wallet_id=respondent_wallet_id,
        )

        if evidence:
            dispute.set_evidence(evidence)

        # Update escrow status
        escrow.status = EscrowStatus.DISPUTED  # type: ignore
        escrow.dispute_id = dispute.id  # type: ignore

        # Save to database
        self.db.add(dispute)
        self.db.commit()
        self.db.refresh(dispute)

        logger.info(f"Created dispute {dispute.id} for escrow {escrow_id}")
        return dispute

    def add_evidence(self, dispute_id: str, wallet_id: int, evidence: Dict[str, Any]) -> bool:
        """Add evidence to an existing dispute"""

        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError(f"Dispute {dispute_id} is not open for evidence")

        # Verify wallet is involved in dispute
        if wallet_id not in [dispute.initiator_wallet_id, dispute.respondent_wallet_id]:
            raise ValueError("Wallet not involved in dispute")

        # Merge new evidence with existing
        current_evidence = dispute.get_evidence()
        current_evidence[f"evidence_{wallet_id}"] = evidence
        dispute.set_evidence(current_evidence)

        self.db.commit()
        logger.info(f"Added evidence to dispute {dispute_id}")
        return True

    def resolve_dispute(
        self,
        dispute_id: str,
        resolution: str,
        winner_wallet_id: Optional[int] = None,
        refund_amount: Optional[float] = None,
    ) -> bool:
        """Resolve a dispute with a decision"""

        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError(f"Dispute {dispute_id} is not open for resolution")

        # Update dispute status
        dispute.status = DisputeStatus.RESOLVED  # type: ignore
        dispute.resolution = resolution  # type: ignore
        dispute.resolved_at = datetime.now(timezone.utc)  # type: ignore

        # Handle escrow based on resolution
        escrow = dispute.escrow
        if escrow:
            if winner_wallet_id == escrow.payer_wallet_id:
                # Payer wins - refund
                escrow.status = EscrowStatus.REFUNDED  # type: ignore
                escrow.refunded_at = datetime.now(timezone.utc)  # type: ignore
                logger.info(f"Dispute {dispute_id} resolved: payer wins, escrow refunded")
            elif winner_wallet_id == escrow.provider_wallet_id:
                # Provider wins - release funds
                escrow.status = EscrowStatus.RELEASED  # type: ignore
                escrow.released_at = datetime.utcnow()  # type: ignore
                logger.info(f"Dispute {dispute_id} resolved: provider wins, escrow released")
            else:
                # Split or other resolution
                escrow.status = EscrowStatus.RESOLVED  # type: ignore
                logger.info(f"Dispute {dispute_id} resolved: split decision")

        self.db.commit()
        logger.info(f"Resolved dispute {dispute_id}: {resolution}")
        return True

    def reject_dispute(self, dispute_id: str, reason: str) -> bool:
        """Reject a dispute as invalid"""

        dispute = self.db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")

        if dispute.status != DisputeStatus.OPEN:
            raise ValueError(f"Dispute {dispute_id} is not open for rejection")

        # Update dispute status
        dispute.status = DisputeStatus.REJECTED  # type: ignore
        dispute.resolution = f"Rejected: {reason}"  # type: ignore
        dispute.resolved_at = datetime.utcnow()  # type: ignore

        # Restore escrow to previous state
        escrow = dispute.escrow
        if escrow:
            escrow.status = EscrowStatus.ACTIVE  # type: ignore
            escrow.dispute_id = None  # type: ignore

        self.db.commit()
        logger.info(f"Rejected dispute {dispute_id}: {reason}")
        return True

    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get dispute by ID"""
        return self.db.query(Dispute).filter(Dispute.id == dispute_id).first()

    def get_disputes_by_wallet(
        self, wallet_id: int, status: Optional[DisputeStatus] = None
    ) -> List[Dispute]:
        """Get disputes involving a wallet"""
        query = self.db.query(Dispute).filter(
            (Dispute.initiator_wallet_id == wallet_id) | (Dispute.respondent_wallet_id == wallet_id)
        )

        if status:
            query = query.filter(Dispute.status == status)

        return query.order_by(Dispute.created_at.desc()).all()

    def get_active_disputes(self) -> List[Dispute]:
        """Get all active disputes"""
        return self.db.query(Dispute).filter(Dispute.status == DisputeStatus.OPEN).all()

    def get_dispute_statistics(self) -> Dict[str, Any]:
        """Get dispute resolution statistics"""
        total_disputes = self.db.query(Dispute).count()
        open_disputes = self.db.query(Dispute).filter(Dispute.status == DisputeStatus.OPEN).count()
        resolved_disputes = (
            self.db.query(Dispute).filter(Dispute.status == DisputeStatus.RESOLVED).count()
        )
        rejected_disputes = (
            self.db.query(Dispute).filter(Dispute.status == DisputeStatus.REJECTED).count()
        )

        return {
            "total_disputes": total_disputes,
            "open_disputes": open_disputes,
            "resolved_disputes": resolved_disputes,
            "rejected_disputes": rejected_disputes,
            "resolution_rate": (
                (resolved_disputes + rejected_disputes) / total_disputes
                if total_disputes > 0
                else 0
            ),
        }
