#!/usr/bin/env python3
"""
Escrow Service for DuxNet
Manages secure payments between service providers and consumers
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import sqlite3
from dataclasses import dataclass, asdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EscrowStatus(Enum):
    """Escrow contract status"""
    PENDING = "pending"
    FUNDED = "funded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DISPUTED = "disputed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class EscrowType(Enum):
    """Type of escrow contract"""
    SERVICE_PAYMENT = "service_payment"
    API_USAGE = "api_usage"
    TASK_EXECUTION = "task_execution"
    SUBSCRIPTION = "subscription"


@dataclass
class EscrowContract:
    """Escrow contract data structure"""
    contract_id: str
    escrow_type: EscrowType
    buyer_id: str
    seller_id: str
    amount: Decimal
    currency: str
    service_id: Optional[str] = None
    description: str = ""
    terms: str = ""
    status: EscrowStatus = EscrowStatus.PENDING
    funded_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class EscrowService:
    """Main escrow service for managing contracts"""
    
    def __init__(self, db_path: str = "escrow.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the escrow database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create escrow contracts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS escrow_contracts (
                        contract_id TEXT PRIMARY KEY,
                        escrow_type TEXT NOT NULL,
                        buyer_id TEXT NOT NULL,
                        seller_id TEXT NOT NULL,
                        amount TEXT NOT NULL,
                        currency TEXT NOT NULL,
                        service_id TEXT,
                        description TEXT,
                        terms TEXT,
                        status TEXT NOT NULL,
                        funded_at TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        dispute_reason TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create escrow transactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS escrow_transactions (
                        transaction_id TEXT PRIMARY KEY,
                        contract_id TEXT NOT NULL,
                        transaction_type TEXT NOT NULL,
                        amount TEXT NOT NULL,
                        currency TEXT NOT NULL,
                        from_address TEXT,
                        to_address TEXT,
                        tx_hash TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (contract_id) REFERENCES escrow_contracts (contract_id)
                    )
                """)
                
                # Create escrow disputes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS escrow_disputes (
                        dispute_id TEXT PRIMARY KEY,
                        contract_id TEXT NOT NULL,
                        initiator_id TEXT NOT NULL,
                        reason TEXT NOT NULL,
                        evidence TEXT,
                        status TEXT NOT NULL,
                        resolution TEXT,
                        created_at TEXT NOT NULL,
                        resolved_at TEXT,
                        FOREIGN KEY (contract_id) REFERENCES escrow_contracts (contract_id)
                    )
                """)
                
                conn.commit()
                logger.info("Escrow database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize escrow database: {e}")
            raise
    
    def create_contract(
        self,
        escrow_type: EscrowType,
        buyer_id: str,
        seller_id: str,
        amount: Decimal,
        currency: str,
        service_id: Optional[str] = None,
        description: str = "",
        terms: str = ""
    ) -> EscrowContract:
        """Create a new escrow contract"""
        try:
            contract_id = str(uuid.uuid4())
            contract = EscrowContract(
                contract_id=contract_id,
                escrow_type=escrow_type,
                buyer_id=buyer_id,
                seller_id=seller_id,
                amount=amount,
                currency=currency,
                service_id=service_id,
                description=description,
                terms=terms
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO escrow_contracts (
                        contract_id, escrow_type, buyer_id, seller_id, amount, currency,
                        service_id, description, terms, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contract.contract_id,
                    contract.escrow_type.value,
                    contract.buyer_id,
                    contract.seller_id,
                    str(contract.amount),
                    contract.currency,
                    contract.service_id,
                    contract.description,
                    contract.terms,
                    contract.status.value,
                    contract.created_at.isoformat(),
                    contract.updated_at.isoformat()
                ))
                conn.commit()
            
            logger.info(f"Created escrow contract {contract_id} for {amount} {currency}")
            return contract
            
        except Exception as e:
            logger.error(f"Failed to create escrow contract: {e}")
            raise
    
    def fund_contract(self, contract_id: str, tx_hash: str) -> bool:
        """Fund an escrow contract"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update contract status
                cursor.execute("""
                    UPDATE escrow_contracts 
                    SET status = ?, funded_at = ?, updated_at = ?
                    WHERE contract_id = ?
                """, (
                    EscrowStatus.FUNDED.value,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    contract_id
                ))
                
                # Record funding transaction
                transaction_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO escrow_transactions (
                        transaction_id, contract_id, transaction_type, amount, currency,
                        from_address, to_address, tx_hash, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    contract_id,
                    "funding",
                    "0",  # Will be updated from contract
                    "FLOP",  # Will be updated from contract
                    "buyer_address",  # Will be updated from actual transaction
                    "escrow_address",  # Will be updated from actual transaction
                    tx_hash,
                    "confirmed",
                    datetime.utcnow().isoformat()
                ))
                
                conn.commit()
            
            logger.info(f"Funded escrow contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fund escrow contract {contract_id}: {e}")
            return False
    
    def start_contract(self, contract_id: str) -> bool:
        """Start work on an escrow contract"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE escrow_contracts 
                    SET status = ?, started_at = ?, updated_at = ?
                    WHERE contract_id = ?
                """, (
                    EscrowStatus.IN_PROGRESS.value,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    contract_id
                ))
                conn.commit()
            
            logger.info(f"Started escrow contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start escrow contract {contract_id}: {e}")
            return False
    
    def complete_contract(self, contract_id: str, tx_hash: str) -> bool:
        """Complete an escrow contract and release funds"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get contract details
                cursor.execute("SELECT amount, currency, seller_id FROM escrow_contracts WHERE contract_id = ?", (contract_id,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Contract {contract_id} not found")
                
                amount, currency, seller_id = result
                
                # Update contract status
                cursor.execute("""
                    UPDATE escrow_contracts 
                    SET status = ?, completed_at = ?, updated_at = ?
                    WHERE contract_id = ?
                """, (
                    EscrowStatus.COMPLETED.value,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    contract_id
                ))
                
                # Record completion transaction (95% to seller, 5% to community)
                seller_amount = Decimal(amount) * Decimal('0.95')
                community_amount = Decimal(amount) * Decimal('0.05')
                
                # Seller payment transaction
                seller_tx_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO escrow_transactions (
                        transaction_id, contract_id, transaction_type, amount, currency,
                        from_address, to_address, tx_hash, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    seller_tx_id,
                    contract_id,
                    "seller_payment",
                    str(seller_amount),
                    currency,
                    "escrow_address",
                    f"seller_{seller_id}",
                    tx_hash,
                    "confirmed",
                    datetime.utcnow().isoformat()
                ))
                
                # Community fund transaction
                community_tx_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO escrow_transactions (
                        transaction_id, contract_id, transaction_type, amount, currency,
                        from_address, to_address, tx_hash, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    community_tx_id,
                    contract_id,
                    "community_fund",
                    str(community_amount),
                    currency,
                    "escrow_address",
                    "community_fund",
                    tx_hash,
                    "confirmed",
                    datetime.utcnow().isoformat()
                ))
                
                conn.commit()
            
            logger.info(f"Completed escrow contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete escrow contract {contract_id}: {e}")
            return False
    
    def dispute_contract(self, contract_id: str, initiator_id: str, reason: str, evidence: str = "") -> bool:
        """Create a dispute for an escrow contract"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update contract status
                cursor.execute("""
                    UPDATE escrow_contracts 
                    SET status = ?, dispute_reason = ?, updated_at = ?
                    WHERE contract_id = ?
                """, (
                    EscrowStatus.DISPUTED.value,
                    reason,
                    datetime.utcnow().isoformat(),
                    contract_id
                ))
                
                # Create dispute record
                dispute_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO escrow_disputes (
                        dispute_id, contract_id, initiator_id, reason, evidence, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    dispute_id,
                    contract_id,
                    initiator_id,
                    reason,
                    evidence,
                    "open",
                    datetime.utcnow().isoformat()
                ))
                
                conn.commit()
            
            logger.info(f"Disputed escrow contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to dispute escrow contract {contract_id}: {e}")
            return False
    
    def refund_contract(self, contract_id: str, tx_hash: str) -> bool:
        """Refund an escrow contract to the buyer"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get contract details
                cursor.execute("SELECT amount, currency, buyer_id FROM escrow_contracts WHERE contract_id = ?", (contract_id,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError(f"Contract {contract_id} not found")
                
                amount, currency, buyer_id = result
                
                # Update contract status
                cursor.execute("""
                    UPDATE escrow_contracts 
                    SET status = ?, updated_at = ?
                    WHERE contract_id = ?
                """, (
                    EscrowStatus.REFUNDED.value,
                    datetime.utcnow().isoformat(),
                    contract_id
                ))
                
                # Record refund transaction
                transaction_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO escrow_transactions (
                        transaction_id, contract_id, transaction_type, amount, currency,
                        from_address, to_address, tx_hash, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    transaction_id,
                    contract_id,
                    "refund",
                    amount,
                    currency,
                    "escrow_address",
                    f"buyer_{buyer_id}",
                    tx_hash,
                    "confirmed",
                    datetime.utcnow().isoformat()
                ))
                
                conn.commit()
            
            logger.info(f"Refunded escrow contract {contract_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refund escrow contract {contract_id}: {e}")
            return False
    
    def get_contract(self, contract_id: str) -> Optional[EscrowContract]:
        """Get an escrow contract by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT contract_id, escrow_type, buyer_id, seller_id, amount, currency,
                           service_id, description, terms, status, funded_at, started_at,
                           completed_at, dispute_reason, created_at, updated_at
                    FROM escrow_contracts WHERE contract_id = ?
                """, (contract_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return EscrowContract(
                    contract_id=result[0],
                    escrow_type=EscrowType(result[1]),
                    buyer_id=result[2],
                    seller_id=result[3],
                    amount=Decimal(result[4]),
                    currency=result[5],
                    service_id=result[6],
                    description=result[7],
                    terms=result[8],
                    status=EscrowStatus(result[9]),
                    funded_at=datetime.fromisoformat(result[10]) if result[10] else None,
                    started_at=datetime.fromisoformat(result[11]) if result[11] else None,
                    completed_at=datetime.fromisoformat(result[12]) if result[12] else None,
                    dispute_reason=result[13],
                    created_at=datetime.fromisoformat(result[14]),
                    updated_at=datetime.fromisoformat(result[15])
                )
                
        except Exception as e:
            logger.error(f"Failed to get escrow contract {contract_id}: {e}")
            return None
    
    def get_contracts_by_user(self, user_id: str, status: Optional[EscrowStatus] = None) -> List[EscrowContract]:
        """Get escrow contracts for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT contract_id, escrow_type, buyer_id, seller_id, amount, currency,
                           service_id, description, terms, status, funded_at, started_at,
                           completed_at, dispute_reason, created_at, updated_at
                    FROM escrow_contracts 
                    WHERE buyer_id = ? OR seller_id = ?
                """
                params = [user_id, user_id]
                
                if status:
                    query += " AND status = ?"
                    params.append(status.value)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                contracts = []
                for result in results:
                    contract = EscrowContract(
                        contract_id=result[0],
                        escrow_type=EscrowType(result[1]),
                        buyer_id=result[2],
                        seller_id=result[3],
                        amount=Decimal(result[4]),
                        currency=result[5],
                        service_id=result[6],
                        description=result[7],
                        terms=result[8],
                        status=EscrowStatus(result[9]),
                        funded_at=datetime.fromisoformat(result[10]) if result[10] else None,
                        started_at=datetime.fromisoformat(result[11]) if result[11] else None,
                        completed_at=datetime.fromisoformat(result[12]) if result[12] else None,
                        dispute_reason=result[13],
                        created_at=datetime.fromisoformat(result[14]),
                        updated_at=datetime.fromisoformat(result[15])
                    )
                    contracts.append(contract)
                
                return contracts
                
        except Exception as e:
            logger.error(f"Failed to get contracts for user {user_id}: {e}")
            return []
    
    def get_contract_statistics(self) -> Dict[str, Any]:
        """Get escrow service statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total contracts
                cursor.execute("SELECT COUNT(*) FROM escrow_contracts")
                total_contracts = cursor.fetchone()[0]
                
                # Contracts by status
                cursor.execute("SELECT status, COUNT(*) FROM escrow_contracts GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Total volume
                cursor.execute("SELECT SUM(CAST(amount AS DECIMAL)) FROM escrow_contracts WHERE status = 'completed'")
                total_volume = cursor.fetchone()[0] or 0
                
                # Community fund total
                cursor.execute("""
                    SELECT SUM(CAST(amount AS DECIMAL)) 
                    FROM escrow_transactions 
                    WHERE transaction_type = 'community_fund' AND status = 'confirmed'
                """)
                community_fund = cursor.fetchone()[0] or 0
                
                return {
                    "total_contracts": total_contracts,
                    "status_counts": status_counts,
                    "total_volume": float(total_volume),
                    "community_fund": float(community_fund),
                    "success_rate": (status_counts.get("completed", 0) / total_contracts * 100) if total_contracts > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get escrow statistics: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    escrow_service = EscrowService()
    
    # Create a test contract
    contract = escrow_service.create_contract(
        escrow_type=EscrowType.SERVICE_PAYMENT,
        buyer_id="user-1",
        seller_id="user-2",
        amount=Decimal("10.0"),
        currency="FLOP",
        service_id="service-123",
        description="API usage payment",
        terms="Payment for 100 API calls"
    )
    
    print(f"Created contract: {contract.contract_id}")
    
    # Fund the contract
    escrow_service.fund_contract(contract.contract_id, "tx_hash_123")
    
    # Start work
    escrow_service.start_contract(contract.contract_id)
    
    # Complete the contract
    escrow_service.complete_contract(contract.contract_id, "tx_hash_456")
    
    # Get statistics
    stats = escrow_service.get_contract_statistics()
    print(f"Escrow statistics: {stats}") 