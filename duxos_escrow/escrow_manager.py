"""
Core Escrow Manager for DuxOS Escrow System
"""

import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .models import Escrow, EscrowStatus, EscrowTransaction, CommunityFund
from .transaction_validator import TransactionValidator
from .dispute_resolver import DisputeResolver

logger = logging.getLogger(__name__)

class EscrowManager:
    """Manages escrow contracts and fund distribution"""
    
    def __init__(self, db: Session, wallet_service=None, message_queue=None):
        self.db = db
        self.wallet_service = wallet_service
        self.message_queue = message_queue
        self.validator = TransactionValidator(db)
        self.dispute_resolver = DisputeResolver(db)
        
        # Initialize community fund if it doesn't exist
        self._ensure_community_fund()
    
    def _ensure_community_fund(self):
        """Ensure community fund exists"""
        fund = self.db.query(CommunityFund).first()
        if not fund:
            fund = CommunityFund()
            self.db.add(fund)
            self.db.commit()
            logger.info("Created community fund")
    
    def create_escrow(self, 
                     payer_wallet_id: int,
                     provider_wallet_id: int,
                     amount: float,
                     service_name: str,
                     task_id: Optional[str] = None,
                     api_call_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Escrow:
        """Create a new escrow contract"""
        
        # Validate inputs
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if payer_wallet_id == provider_wallet_id:
            raise ValueError("Payer and provider cannot be the same")
        
        # Create escrow contract
        escrow_id = str(uuid.uuid4())
        escrow = Escrow(
            id=escrow_id,
            payer_wallet_id=payer_wallet_id,
            provider_wallet_id=provider_wallet_id,
            amount=amount,
            status=EscrowStatus.PENDING,
            service_name=service_name,
            task_id=task_id,
            api_call_id=api_call_id
        )
        
        if metadata:
            escrow.set_metadata(metadata)
        
        # Calculate distribution amounts
        escrow.calculate_distribution()
        
        # Lock funds from payer
        if self.wallet_service:
            try:
                # Lock funds (this would be implemented in wallet service)
                lock_success = self._lock_funds(payer_wallet_id, amount, escrow_id)
                if not lock_success:
                    raise Exception("Failed to lock funds")
                
                setattr(escrow, 'status', EscrowStatus.ACTIVE)
                logger.info(f"Funds locked for escrow {escrow_id}")
                
            except Exception as e:
                logger.error(f"Failed to lock funds: {e}")
                raise
        
        # Save to database
        self.db.add(escrow)
        self.db.commit()
        self.db.refresh(escrow)
        
        # Record transaction
        self._record_transaction(
            escrow_id=escrow_id,
            transaction_type="create",
            amount=amount,
            from_wallet_id=payer_wallet_id,
            metadata={"service_name": service_name}
        )
        
        # Publish event
        if self.message_queue:
            self.message_queue.publish("duxos.escrow.created", {
                "escrow_id": escrow_id,
                "amount": amount,
                "service_name": service_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Created escrow {escrow_id} for {amount} FLOP")
        return escrow
    
    def release_escrow(self, escrow_id: str, result_hash: str, provider_signature: str) -> bool:
        """Release escrow funds after successful task completion"""
        
        escrow = self.db.query(Escrow).filter(Escrow.id == escrow_id).first()
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        
        if escrow.status != EscrowStatus.ACTIVE:
            raise ValueError(f"Escrow {escrow_id} is not active (status: {escrow.status})")
        
        # Validate result
        if not self.validator.validate_result(escrow, result_hash, provider_signature):
            raise ValueError("Result validation failed")
        
        # Release funds to provider (95%)
        provider_amount = escrow.provider_amount
        if self.wallet_service and provider_amount is not None:
            provider_wallet_id = escrow.provider_wallet_id
            provider_success = self._transfer_funds(
                from_wallet_id=None,  # From escrow
                to_wallet_id=provider_wallet_id,
                amount=provider_amount,
                escrow_id=escrow_id
            )
            if not provider_success:
                raise Exception("Failed to transfer funds to provider")
        
        # Add to community fund (5%)
        community_amount = escrow.community_amount
        if community_amount is not None:
            self._add_to_community_fund(community_amount)
        
        # Update escrow status
        escrow.status = EscrowStatus.RELEASED  # type: ignore
        escrow.released_at = datetime.now(timezone.utc)  # type: ignore
        escrow.result_hash = result_hash  # type: ignore
        escrow.provider_signature = provider_signature  # type: ignore
        
        self.db.commit()
        
        # Record transactions
        if escrow.provider_amount is not None:
            self._record_transaction(
                escrow_id=escrow_id,
                transaction_type="release_provider",
                amount=escrow.provider_amount,
                to_wallet_id=escrow.provider_wallet_id
            )
        
        if escrow.community_amount is not None:
            self._record_transaction(
                escrow_id=escrow_id,
                transaction_type="release_community",
                amount=escrow.community_amount,
                to_wallet_id=None  # Community fund
            )
        
        # Publish event
        if self.message_queue:
            self.message_queue.publish("duxos.escrow.released", {
                "escrow_id": escrow_id,
                "provider_amount": escrow.provider_amount,
                "community_amount": escrow.community_amount,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Released escrow {escrow_id}: {escrow.provider_amount} to provider, {escrow.community_amount} to community")
        return True
    
    def refund_escrow(self, escrow_id: str, reason: str = "Task failed") -> bool:
        """Refund escrow funds to payer"""
        
        escrow = self.db.query(Escrow).filter(Escrow.id == escrow_id).first()
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        
        if escrow.status not in [EscrowStatus.ACTIVE, EscrowStatus.DISPUTED]:
            raise ValueError(f"Escrow {escrow_id} cannot be refunded (status: {escrow.status})")
        
        # Refund funds to payer
        if self.wallet_service:
            refund_success = self._transfer_funds(
                from_wallet_id=None,  # From escrow
                to_wallet_id=escrow.payer_wallet_id,
                amount=escrow.amount,
                escrow_id=escrow_id
            )
            if not refund_success:
                raise Exception("Failed to refund funds")
        
        # Update escrow status
        escrow.status = EscrowStatus.REFUNDED  # type: ignore
        escrow.refunded_at = datetime.now(timezone.utc)  # type: ignore
        
        self.db.commit()
        
        # Record transaction
        self._record_transaction(
            escrow_id=escrow_id,
            transaction_type="refund",
            amount=escrow.amount,
            to_wallet_id=escrow.payer_wallet_id,
            metadata={"reason": reason}
        )
        
        # Publish event
        if self.message_queue:
            self.message_queue.publish("duxos.escrow.refunded", {
                "escrow_id": escrow_id,
                "amount": escrow.amount,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        logger.info(f"Refunded escrow {escrow_id}: {escrow.amount} to payer")
        return True
    
    def get_escrow(self, escrow_id: str) -> Optional[Escrow]:
        """Get escrow by ID"""
        return self.db.query(Escrow).filter(Escrow.id == escrow_id).first()
    
    def get_escrows_by_wallet(self, wallet_id: int, status: Optional[EscrowStatus] = None) -> List[Escrow]:
        """Get escrows for a wallet"""
        query = self.db.query(Escrow).filter(
            (Escrow.payer_wallet_id == wallet_id) | (Escrow.provider_wallet_id == wallet_id)
        )
        
        if status:
            query = query.filter(Escrow.status == status)
        
        return query.order_by(Escrow.created_at.desc()).all()
    
    def get_community_fund_balance(self) -> float:
        """Get current community fund balance"""
        fund = self.db.query(CommunityFund).first()
        return fund.balance if fund else 0.0
    
    def _lock_funds(self, wallet_id: int, amount: float, escrow_id: str) -> bool:
        """Lock funds in wallet (placeholder for wallet service integration)"""
        # This would integrate with the wallet service to lock funds
        # For now, we'll assume success
        logger.info(f"Locking {amount} FLOP from wallet {wallet_id} for escrow {escrow_id}")
        return True
    
    def _transfer_funds(self, from_wallet_id: Optional[int], to_wallet_id: int, 
                       amount: float, escrow_id: str) -> bool:
        """Transfer funds between wallets (placeholder for wallet service integration)"""
        # This would integrate with the wallet service to transfer funds
        # For now, we'll assume success
        logger.info(f"Transferring {amount} FLOP to wallet {to_wallet_id} from escrow {escrow_id}")
        return True
    
    def _add_to_community_fund(self, amount: float):
        """Add amount to community fund"""
        fund = self.db.query(CommunityFund).first()
        if fund:
            fund.balance += amount
            fund.updated_at = datetime.now(timezone.utc)  # type: ignore
            self.db.commit()
            logger.info(f"Added {amount} FLOP to community fund (new balance: {fund.balance})")
    
    def _record_transaction(self, escrow_id: str, transaction_type: str, amount: float,
                          from_wallet_id: Optional[int] = None, to_wallet_id: Optional[int] = None,
                          metadata: Optional[Dict[str, Any]] = None):
        """Record escrow transaction for audit trail"""
        transaction = EscrowTransaction(
            id=str(uuid.uuid4()),
            escrow_id=escrow_id,
            transaction_type=transaction_type,
            amount=amount,
            from_wallet_id=from_wallet_id,
            to_wallet_id=to_wallet_id
        )
        
        if metadata:
            transaction.set_metadata(metadata)
        
        self.db.add(transaction)
        self.db.commit() 