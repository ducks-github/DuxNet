"""
Community Fund Manager for DuxOS Escrow System

Handles:
- Community fund balance management
- Airdrop distribution
- Governance voting
- Fund allocation decisions
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import CommunityFund, Escrow
from .exceptions import CommunityFundError

logger = logging.getLogger(__name__)

class CommunityFundManager:
    """Manages community fund operations including airdrops and governance"""
    
    def __init__(self, db: Session):
        self.db = db
        self._ensure_fund_exists()
    
    def _ensure_fund_exists(self) -> None:
        """Ensure community fund exists, create if it doesn't"""
        fund = self.db.query(CommunityFund).first()
        if not fund:
            fund = CommunityFund(
                balance=0.0,
                airdrop_threshold=100.0,
                governance_enabled=True,
                min_vote_threshold=0.1
            )
            self.db.add(fund)
            self.db.commit()
            logger.info("Created new community fund")
    
    def get_fund_balance(self) -> float:
        """Get current community fund balance"""
        fund = self.db.query(CommunityFund).first()
        return fund.balance if fund else 0.0
    
    def add_to_fund(self, amount: float) -> bool:
        """Add amount to community fund"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        fund = self.db.query(CommunityFund).first()
        if fund:
            fund.balance += amount
            fund.updated_at = datetime.now(timezone.utc)  # type: ignore
            self.db.commit()
            logger.info(f"Added {amount} FLOP to community fund (new balance: {fund.balance})")
            return True
        return False
    
    def remove_from_fund(self, amount: float, reason: str) -> bool:
        """Remove amount from community fund (requires governance approval)"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        fund = self.db.query(CommunityFund).first()
        if not fund:
            raise CommunityFundError("Community fund not found")
        
        if fund.balance < amount:
            raise CommunityFundError(f"Insufficient funds: {fund.balance} < {amount}")
        
        fund.balance -= amount
        fund.updated_at = datetime.now(timezone.utc)  # type: ignore
        self.db.commit()
        logger.info(f"Removed {amount} FLOP from community fund for: {reason}")
        return True
    
    def check_airdrop_eligibility(self) -> bool:
        """Check if airdrop threshold is met"""
        fund = self.db.query(CommunityFund).first()
        if not fund:
            return False
        return fund.balance >= fund.airdrop_threshold
    
    def execute_airdrop(self, distribution_ratio: float = 0.5) -> Dict[str, Any]:
        """
        Execute airdrop to active nodes
        
        Args:
            distribution_ratio: Percentage of fund to distribute (0.0-1.0)
        
        Returns:
            Dict with airdrop details
        """
        fund = self.db.query(CommunityFund).first()
        if not fund:
            raise CommunityFundError("Community fund not found")
        
        if not self.check_airdrop_eligibility():
            raise CommunityFundError("Airdrop threshold not met")
        
        # Calculate airdrop amount
        airdrop_amount = fund.balance * distribution_ratio
        
        # Get active nodes (nodes with recent escrow activity)
        # For now, we'll use a simple approach - nodes with escrows in last 30 days
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        from .models import EscrowStatus
        active_escrows = self.db.query(Escrow).filter(
            and_(
                Escrow.created_at >= cutoff_date,
                or_(
                    Escrow.status == EscrowStatus.RELEASED,
                    Escrow.status == EscrowStatus.ACTIVE
                )
            )
        ).all()
        
        # Get unique wallet IDs from active escrows
        active_wallets = set()
        for escrow in active_escrows:
            active_wallets.add(escrow.payer_wallet_id)
            active_wallets.add(escrow.provider_wallet_id)
        
        if not active_wallets:
            raise CommunityFundError("No active wallets found for airdrop")
        
        # Calculate per-wallet amount
        per_wallet_amount = airdrop_amount / len(active_wallets)
        
        # Update fund
        fund.balance -= airdrop_amount
        fund.last_airdrop_at = datetime.now(timezone.utc)  # type: ignore
        fund.last_airdrop_amount = airdrop_amount  # type: ignore
        fund.updated_at = datetime.now(timezone.utc)  # type: ignore
        
        self.db.commit()
        
        airdrop_result = {
            "airdrop_id": str(uuid.uuid4()),
            "total_amount": airdrop_amount,
            "per_wallet_amount": per_wallet_amount,
            "wallet_count": len(active_wallets),
            "wallets": list(active_wallets),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "remaining_balance": fund.balance
        }
        
        logger.info(f"Airdrop executed: {airdrop_amount} FLOP distributed to {len(active_wallets)} wallets")
        return airdrop_result
    
    def get_airdrop_history(self) -> List[Dict[str, Any]]:
        """Get airdrop history"""
        fund = self.db.query(CommunityFund).first()
        if not fund or not fund.last_airdrop_at:
            return []
        
        return [{
            "timestamp": fund.last_airdrop_at.isoformat(),
            "amount": fund.last_airdrop_amount,
            "remaining_balance": fund.balance
        }]
    
    def update_airdrop_threshold(self, new_threshold: float) -> bool:
        """Update airdrop threshold (requires governance)"""
        if new_threshold <= 0:
            raise ValueError("Threshold must be positive")
        
        fund = self.db.query(CommunityFund).first()
        if fund:
            fund.airdrop_threshold = new_threshold
            fund.updated_at = datetime.now(timezone.utc)  # type: ignore
            self.db.commit()
            logger.info(f"Updated airdrop threshold to {new_threshold}")
            return True
        return False
    
    def get_fund_stats(self) -> Dict[str, Any]:
        """Get comprehensive fund statistics"""
        fund = self.db.query(CommunityFund).first()
        if not fund:
            return {}
        
        # Calculate recent activity
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        recent_escrows = self.db.query(Escrow).filter(
            Escrow.created_at >= cutoff_date
        ).count()
        
        total_escrows = self.db.query(Escrow).count()
        
        return {
            "balance": fund.balance,
            "airdrop_threshold": fund.airdrop_threshold,
            "governance_enabled": fund.governance_enabled,
            "min_vote_threshold": fund.min_vote_threshold,
            "last_airdrop_at": fund.last_airdrop_at.isoformat() if fund.last_airdrop_at else None,
            "last_airdrop_amount": fund.last_airdrop_amount,
            "created_at": fund.created_at.isoformat(),
            "updated_at": fund.updated_at.isoformat() if fund.updated_at else None,
            "recent_activity": {
                "escrows_last_30_days": recent_escrows,
                "total_escrows": total_escrows
            },
            "airdrop_eligible": self.check_airdrop_eligibility()
        } 