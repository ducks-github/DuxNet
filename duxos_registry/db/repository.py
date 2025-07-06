from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from ..models.database_models import Node, Capability, ReputationEvent, Wallet, Transaction, WalletCapability
import uuid
from datetime import datetime

class NodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_node(self, node_id: str, address: str, capabilities: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> Node:
        """Create a new node"""
        node = Node(
            node_id=node_id,
            address=address
        )
        if metadata:
            node.set_metadata(metadata)
        
        # Add capabilities if provided
        if capabilities:
            for cap_name in capabilities:
                capability = self.db.query(Capability).filter(Capability.name == cap_name).first()
                if not capability:
                    capability = Capability(name=cap_name)
                    self.db.add(capability)
                node.capabilities.append(capability)
        
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return self.db.query(Node).filter(Node.node_id == node_id).first()

    def get_all_nodes(self, active_only: bool = True) -> List[Node]:
        """Get all nodes, optionally filtered by active status"""
        query = self.db.query(Node)
        if active_only:
            query = query.filter(Node.is_active == True)
        return query.all()

    def get_nodes_by_capability(self, capability_name: str, active_only: bool = True) -> List[Node]:
        """Get all nodes with a specific capability"""
        query = self.db.query(Node).join(Node.capabilities).filter(Capability.name == capability_name)
        if active_only:
            query = query.filter(Node.is_active == True)
        return query.all()

    def update_node_status(self, node_id: str, status: str) -> Optional[Node]:
        """Update node status"""
        node = self.get_node(node_id)
        if node:
            # Use setattr to avoid type checker issues with SQLAlchemy columns
            setattr(node, 'status', status)
            setattr(node, 'updated_at', datetime.utcnow())
            self.db.commit()
            self.db.refresh(node)
        return node

    def update_node_heartbeat(self, node_id: str) -> Optional[Node]:
        """Update node heartbeat timestamp"""
        node = self.get_node(node_id)
        if node:
            setattr(node, 'last_heartbeat', datetime.utcnow())
            setattr(node, 'status', "online")
            self.db.commit()
            self.db.refresh(node)
        return node

    def update_node_reputation(self, node_id: str, reputation: float) -> Optional[Node]:
        """Update node reputation"""
        node = self.get_node(node_id)
        if node:
            setattr(node, 'reputation', max(0.0, min(100.0, reputation)))  # Clamp between 0-100
            setattr(node, 'updated_at', datetime.utcnow())
            self.db.commit()
            self.db.refresh(node)
        return node

    def add_capability_to_node(self, node_id: str, capability_name: str) -> Optional[Node]:
        """Add a capability to a node"""
        node = self.get_node(node_id)
        if node:
            capability = self.db.query(Capability).filter(Capability.name == capability_name).first()
            if not capability:
                capability = Capability(name=capability_name)
                self.db.add(capability)
            
            if capability not in node.capabilities:
                node.capabilities.append(capability)
                self.db.commit()
                self.db.refresh(node)
        return node

    def remove_capability_from_node(self, node_id: str, capability_name: str) -> Optional[Node]:
        """Remove a capability from a node"""
        node = self.get_node(node_id)
        if node:
            capability = self.db.query(Capability).filter(Capability.name == capability_name).first()
            if capability and capability in node.capabilities:
                node.capabilities.remove(capability)
                self.db.commit()
                self.db.refresh(node)
        return node

    def delete_node(self, node_id: str) -> bool:
        """Soft delete a node (set is_active to False)"""
        node = self.get_node(node_id)
        if node:
            setattr(node, 'is_active', False)
            setattr(node, 'updated_at', datetime.utcnow())
            self.db.commit()
            return True
        return False

class CapabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_capability(self, name: str, description: Optional[str] = None, version: str = "1.0") -> Capability:
        """Create a new capability"""
        capability = Capability(
            name=name,
            description=description,
            version=version
        )
        self.db.add(capability)
        self.db.commit()
        self.db.refresh(capability)
        return capability

    def get_capability(self, name: str) -> Optional[Capability]:
        """Get a capability by name"""
        return self.db.query(Capability).filter(Capability.name == name).first()

    def get_all_capabilities(self, active_only: bool = True) -> List[Capability]:
        """Get all capabilities"""
        query = self.db.query(Capability)
        if active_only:
            query = query.filter(Capability.is_active == True)
        return query.all()

    def update_capability(self, name: str, description: Optional[str] = None, version: Optional[str] = None) -> Optional[Capability]:
        """Update a capability"""
        capability = self.get_capability(name)
        if capability:
            if description is not None:
                setattr(capability, 'description', description)
            if version is not None:
                setattr(capability, 'version', version)
            self.db.commit()
            self.db.refresh(capability)
        return capability

    def delete_capability(self, name: str) -> bool:
        """Soft delete a capability"""
        capability = self.get_capability(name)
        if capability:
            setattr(capability, 'is_active', False)
            self.db.commit()
            return True
        return False

class ReputationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reputation_event(self, node_id: str, event_type: str, score_change: float, 
                              description: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ReputationEvent:
        """Create a new reputation event"""
        event = ReputationEvent(
            id=str(uuid.uuid4()),
            node_id=node_id,
            event_type=event_type,
            score_change=score_change,
            description=description,
            event_metadata=metadata or {}
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_reputation_events(self, node_id: str, limit: int = 100) -> List[ReputationEvent]:
        """Get reputation events for a node"""
        return self.db.query(ReputationEvent).filter(
            ReputationEvent.node_id == node_id
        ).order_by(ReputationEvent.created_at.desc()).limit(limit).all()

    def get_reputation_summary(self, node_id: str) -> Dict[str, Any]:
        """Get reputation summary for a node"""
        events = self.get_reputation_events(node_id)
        total_score = sum(event.score_change for event in events)
        event_count = len(events)
        
        return {
            "total_score": total_score,
            "event_count": event_count,
            "events": events
        }


class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_wallet(self, node_id: str, wallet_name: str, address: str, 
                     wallet_type: str = "flopcoin", is_active: bool = True) -> Wallet:
        """Create a new wallet"""
        wallet = Wallet(
            node_id=node_id,
            wallet_name=wallet_name,
            address=address,
            wallet_type=wallet_type,
            is_active=is_active
        )
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        return wallet

    def get_wallet_by_node(self, node_id: str) -> Optional[Wallet]:
        """Get wallet by node ID"""
        return self.db.query(Wallet).filter(Wallet.node_id == node_id).first()

    def get_wallet_by_id(self, wallet_id: int) -> Optional[Wallet]:
        """Get wallet by ID"""
        return self.db.query(Wallet).filter(Wallet.id == wallet_id).first()

    def get_all_wallets(self, active_only: bool = True) -> List[Wallet]:
        """Get all wallets"""
        query = self.db.query(Wallet)
        if active_only:
            query = query.filter(Wallet.is_active == True)
        return query.all()

    def update_wallet_balance(self, wallet_id: int, balance: float) -> Optional[Wallet]:
        """Update wallet balance"""
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            setattr(wallet, 'balance', balance)
            self.db.commit()
            self.db.refresh(wallet)
        return wallet

    def update_wallet_address(self, wallet_id: int, address: str) -> Optional[Wallet]:
        """Update wallet address"""
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            setattr(wallet, 'address', address)
            self.db.commit()
            self.db.refresh(wallet)
        return wallet

    def deactivate_wallet(self, wallet_id: int) -> bool:
        """Deactivate a wallet"""
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            setattr(wallet, 'is_active', False)
            self.db.commit()
            return True
        return False

    def delete_wallet(self, wallet_id: int) -> bool:
        """Delete a wallet"""
        wallet = self.get_wallet_by_id(wallet_id)
        if wallet:
            self.db.delete(wallet)
            self.db.commit()
            return True
        return False


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, wallet_id: int, txid: str, recipient_address: str, 
                          amount: float, transaction_type: str = "send", 
                          status: str = "pending") -> Transaction:
        """Create a new transaction"""
        transaction = Transaction(
            wallet_id=wallet_id,
            txid=txid,
            recipient_address=recipient_address,
            amount=amount,
            transaction_type=transaction_type,
            status=status
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transaction_by_txid(self, txid: str) -> Optional[Transaction]:
        """Get transaction by TXID"""
        return self.db.query(Transaction).filter(Transaction.txid == txid).first()

    def get_transactions_by_wallet(self, wallet_id: int, limit: int = 50) -> List[Transaction]:
        """Get transactions for a wallet"""
        return self.db.query(Transaction).filter(
            Transaction.wallet_id == wallet_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()

    def get_transactions_by_node_since(self, node_id: str, since: datetime) -> List[Transaction]:
        """Get transactions for a node since a specific time"""
        return self.db.query(Transaction).join(Wallet).filter(
            Wallet.node_id == node_id,
            Transaction.created_at >= since
        ).all()

    def update_transaction_status(self, txid: str, status: str) -> Optional[Transaction]:
        """Update transaction status"""
        transaction = self.get_transaction_by_txid(txid)
        if transaction:
            setattr(transaction, 'status', status)
            if status == "confirmed":
                setattr(transaction, 'confirmed_at', datetime.utcnow())
            self.db.commit()
            self.db.refresh(transaction)
        return transaction

    def get_transaction_statistics(self, wallet_id: int) -> Dict[str, Any]:
        """Get transaction statistics for a wallet"""
        transactions = self.db.query(Transaction).filter(Transaction.wallet_id == wallet_id).all()
        
        # Use list comprehension with proper filtering
        total_sent = sum(tx.amount for tx in transactions if getattr(tx, 'transaction_type') == "send")
        total_received = sum(tx.amount for tx in transactions if getattr(tx, 'transaction_type') == "receive")
        total_fees = sum(getattr(tx, 'fee', 0.0) for tx in transactions)
        pending_count = len([tx for tx in transactions if getattr(tx, 'status') == "pending"])
        
        return {
            "total_transactions": len(transactions),
            "total_sent": total_sent,
            "total_received": total_received,
            "total_fees": total_fees,
            "pending_transactions": pending_count
        } 