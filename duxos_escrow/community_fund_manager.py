"""
Community Fund Manager for DuxOS Escrow System

This module manages the community fund, including:
- 5% tax collection from escrow transactions
- Automatic distribution when threshold is reached
- Fund monitoring and reporting
- Airdrop coordination
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .models import CommunityFund, Escrow, EscrowTransaction
from .wallet_integration import EscrowWalletIntegration
from .exceptions import CommunityFundError, InsufficientCommunityFundError, AirdropError

logger = logging.getLogger(__name__)


class CommunityFundManager:
    """Manages community fund operations and airdrops"""
    
    def __init__(self, db: Session, wallet_integration: EscrowWalletIntegration, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.wallet_integration = wallet_integration
        self.config = config or {}
        
        # Configuration
        self.airdrop_threshold = self.config.get('airdrop_threshold', 100.0)  # 100 FLOP
        self.min_airdrop_amount = self.config.get('min_airdrop_amount', 1.0)  # 1 FLOP per node
        self.airdrop_interval_hours = self.config.get('airdrop_interval_hours', 24)  # Daily airdrops
        self.max_airdrop_nodes = self.config.get('max_airdrop_nodes', 1000)  # Max nodes per airdrop
        
        # State tracking
        self.last_airdrop_check = datetime.now(timezone.utc)
        self.airdrop_in_progress = False
        
        # Initialize community fund if it doesn't exist
        self._ensure_community_fund()
        
        logger.info("Community Fund Manager initialized")
    
    def _ensure_community_fund(self):
        """Ensure community fund exists in database"""
        try:
            fund = self.db.query(CommunityFund).first()
            if not fund:
                fund = CommunityFund(
                    balance=0.0,
                    airdrop_threshold=self.airdrop_threshold,
                    governance_enabled=True,
                    min_vote_threshold=0.1
                )
                self.db.add(fund)
                self.db.commit()
                logger.info("Created community fund")
        except Exception as e:
            logger.error(f"Failed to ensure community fund: {e}")
            raise
    
    def collect_tax(self, escrow_id: str, amount: float) -> str:
        """
        Collect 5% tax from escrow transaction
        
        Args:
            escrow_id: Escrow contract ID
            amount: Amount to collect (should be 5% of escrow amount)
            
        Returns:
            Transaction ID
        """
        try:
            if amount <= 0:
                raise ValueError("Tax amount must be positive")
            
            # Add to community fund using wallet integration
            txid = self.wallet_integration.add_to_community_fund(amount, escrow_id)
            
            # Update community fund balance
            fund = self.db.query(CommunityFund).first()
            if fund:
                fund.balance += amount
                fund.updated_at = datetime.now(timezone.utc)
                self.db.commit()
            
            logger.info(f"Collected {amount} FLOP tax for escrow {escrow_id}")
            
            # Check if airdrop should be triggered
            self._check_airdrop_trigger()
            
            return txid
            
        except Exception as e:
            logger.error(f"Failed to collect tax for escrow {escrow_id}: {e}")
            raise CommunityFundError(f"Tax collection failed: {e}")
    
    def get_fund_balance(self) -> float:
        """Get current community fund balance"""
        try:
            fund = self.db.query(CommunityFund).first()
            return fund.balance if fund else 0.0
        except Exception as e:
            logger.error(f"Failed to get fund balance: {e}")
            return 0.0
    
    def get_fund_statistics(self) -> Dict[str, Any]:
        """Get comprehensive fund statistics"""
        try:
            fund = self.db.query(CommunityFund).first()
            if not fund:
                return {"error": "Community fund not found"}
            
            # Calculate recent activity
            last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_transactions = self.db.query(EscrowTransaction).filter(
                and_(
                    EscrowTransaction.transaction_type == "community_fund",
                    EscrowTransaction.created_at >= last_24h
                )
            ).all()
            
            recent_amount = sum(tx.amount for tx in recent_transactions)
            
            # Calculate total collected
            total_collected = self.db.query(func.sum(EscrowTransaction.amount)).filter(
                EscrowTransaction.transaction_type == "community_fund"
            ).scalar() or 0.0
            
            return {
                "current_balance": fund.balance,
                "airdrop_threshold": fund.airdrop_threshold,
                "last_airdrop_at": fund.last_airdrop_at.isoformat() if fund.last_airdrop_at else None,
                "last_airdrop_amount": fund.last_airdrop_amount,
                "recent_24h_collected": recent_amount,
                "total_collected": total_collected,
                "next_airdrop_trigger": fund.balance >= fund.airdrop_threshold,
                "governance_enabled": fund.governance_enabled,
                "min_vote_threshold": fund.min_vote_threshold
            }
            
        except Exception as e:
            logger.error(f"Failed to get fund statistics: {e}")
            return {"error": str(e)}
    
    def _check_airdrop_trigger(self):
        """Check if airdrop should be triggered"""
        try:
            fund = self.db.query(CommunityFund).first()
            if not fund:
                return
            
            # Check if threshold is met and enough time has passed
            if (fund.balance >= fund.airdrop_threshold and 
                (not fund.last_airdrop_at or 
                 datetime.now(timezone.utc) - fund.last_airdrop_at >= timedelta(hours=self.airdrop_interval_hours))):
                
                logger.info(f"Community fund threshold reached ({fund.balance} >= {fund.airdrop_threshold}), triggering airdrop")
                self._trigger_airdrop()
                
        except Exception as e:
            logger.error(f"Error checking airdrop trigger: {e}")
    
    def _trigger_airdrop(self):
        """Trigger automatic airdrop to active nodes"""
        try:
            if self.airdrop_in_progress:
                logger.warning("Airdrop already in progress, skipping")
                return
            
            self.airdrop_in_progress = True
            
            # Get community fund
            fund = self.db.query(CommunityFund).first()
            if not fund or fund.balance < fund.airdrop_threshold:
                logger.warning("Insufficient funds for airdrop")
                return
            
            # Get active nodes (this would integrate with node registry)
            active_nodes = self._get_active_nodes()
            if not active_nodes:
                logger.warning("No active nodes found for airdrop")
                return
            
            # Calculate airdrop amount per node
            total_nodes = min(len(active_nodes), self.max_airdrop_nodes)
            airdrop_per_node = fund.balance / total_nodes
            
            if airdrop_per_node < self.min_airdrop_amount:
                logger.warning(f"Airdrop per node too small: {airdrop_per_node} < {self.min_airdrop_amount}")
                return
            
            # Execute airdrop
            successful_airdrops = 0
            total_distributed = 0.0
            
            for node in active_nodes[:self.max_airdrop_nodes]:
                try:
                    # Get node's wallet
                    wallet = self._get_node_wallet(node['node_id'])
                    if not wallet:
                        logger.warning(f"No wallet found for node {node['node_id']}")
                        continue
                    
                    # Send airdrop
                    txid = self.wallet_integration.transfer_funds(
                        from_wallet_id=None,  # From community fund
                        to_wallet_id=wallet.id,
                        amount=airdrop_per_node,
                        escrow_id=f"airdrop_{int(time.time())}"
                    )
                    
                    successful_airdrops += 1
                    total_distributed += airdrop_per_node
                    
                    logger.info(f"Airdropped {airdrop_per_node} FLOP to node {node['node_id']}, txid: {txid}")
                    
                except Exception as e:
                    logger.error(f"Failed to airdrop to node {node['node_id']}: {e}")
                    continue
            
            # Update community fund
            fund.balance -= total_distributed
            fund.last_airdrop_at = datetime.now(timezone.utc)
            fund.last_airdrop_amount = total_distributed
            fund.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Airdrop completed: {successful_airdrops} nodes, {total_distributed} FLOP distributed")
            
        except Exception as e:
            logger.error(f"Failed to trigger airdrop: {e}")
            raise AirdropError(f"Airdrop failed: {e}")
        finally:
            self.airdrop_in_progress = False
    
    def _get_active_nodes(self) -> List[Dict[str, Any]]:
        """Get list of active nodes eligible for airdrop"""
        try:
            # This would integrate with the node registry to get active nodes
            # For now, return a placeholder list
            # In real implementation, this would query the node registry
            
            # Placeholder implementation
            return [
                {"node_id": "node_001", "wallet_id": 1, "reputation": 85.0},
                {"node_id": "node_002", "wallet_id": 2, "reputation": 92.0},
                {"node_id": "node_003", "wallet_id": 3, "reputation": 78.0}
            ]
            
        except Exception as e:
            logger.error(f"Failed to get active nodes: {e}")
            return []
    
    def _get_node_wallet(self, node_id: str) -> Optional[Any]:
        """Get wallet for a node"""
        try:
            # This would integrate with the wallet repository
            # For now, return None (placeholder)
            return None
        except Exception as e:
            logger.error(f"Failed to get wallet for node {node_id}: {e}")
            return None
    
    def manual_airdrop(self, node_ids: List[str], amount_per_node: float) -> Dict[str, Any]:
        """
        Manual airdrop to specific nodes
        
        Args:
            node_ids: List of node IDs to airdrop to
            amount_per_node: Amount per node
            
        Returns:
            Airdrop results
        """
        try:
            fund = self.db.query(CommunityFund).first()
            if not fund:
                raise CommunityFundError("Community fund not found")
            
            total_amount = len(node_ids) * amount_per_node
            if fund.balance < total_amount:
                raise InsufficientCommunityFundError(f"Insufficient funds: {fund.balance} < {total_amount}")
            
            successful_airdrops = 0
            failed_airdrops = 0
            total_distributed = 0.0
            
            for node_id in node_ids:
                try:
                    wallet = self._get_node_wallet(node_id)
                    if not wallet:
                        failed_airdrops += 1
                        continue
                    
                    txid = self.wallet_integration.transfer_funds(
                        from_wallet_id=None,
                        to_wallet_id=wallet.id,
                        amount=amount_per_node,
                        escrow_id=f"manual_airdrop_{int(time.time())}"
                    )
                    
                    successful_airdrops += 1
                    total_distributed += amount_per_node
                    
                except Exception as e:
                    logger.error(f"Failed to airdrop to node {node_id}: {e}")
                    failed_airdrops += 1
            
            # Update community fund
            fund.balance -= total_distributed
            fund.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            return {
                "successful_airdrops": successful_airdrops,
                "failed_airdrops": failed_airdrops,
                "total_distributed": total_distributed,
                "amount_per_node": amount_per_node
            }
            
        except Exception as e:
            logger.error(f"Manual airdrop failed: {e}")
            raise AirdropError(f"Manual airdrop failed: {e}")
    
    def update_airdrop_config(self, threshold: Optional[float] = None, 
                            interval_hours: Optional[int] = None,
                            min_amount: Optional[float] = None) -> bool:
        """
        Update airdrop configuration
        
        Args:
            threshold: New airdrop threshold
            interval_hours: New airdrop interval in hours
            min_amount: New minimum airdrop amount per node
            
        Returns:
            True if updated successfully
        """
        try:
            fund = self.db.query(CommunityFund).first()
            if not fund:
                return False
            
            if threshold is not None:
                fund.airdrop_threshold = threshold
                self.airdrop_threshold = threshold
            
            if interval_hours is not None:
                self.airdrop_interval_hours = interval_hours
            
            if min_amount is not None:
                self.min_airdrop_amount = min_amount
            
            fund.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info("Updated airdrop configuration")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update airdrop config: {e}")
            return False
    
    async def start_monitoring(self):
        """Start background monitoring of community fund"""
        try:
            logger.info("Starting community fund monitoring")
            
            while True:
                try:
                    # Check for airdrop triggers
                    self._check_airdrop_trigger()
                    
                    # Log fund statistics periodically
                    stats = self.get_fund_statistics()
                    logger.info(f"Community fund status: {stats['current_balance']} FLOP balance")
                    
                    # Wait before next check
                    await asyncio.sleep(3600)  # Check every hour
                    
                except Exception as e:
                    logger.error(f"Error in fund monitoring: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes on error
                    
        except Exception as e:
            logger.error(f"Fund monitoring failed: {e}")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        logger.info("Stopping community fund monitoring") 