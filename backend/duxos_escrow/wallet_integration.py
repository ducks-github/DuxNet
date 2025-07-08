"""
Wallet Integration Service for DuxOS Escrow System

This module provides real wallet integration for the escrow system, including:
- Fund locking mechanisms
- Transaction signing and validation
- Real Flopcoin RPC integration
- Community fund management
"""

import base64
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

# Import wallet service from registry
try:
    from duxos_registry.db.repository import TransactionRepository, WalletRepository
    from duxos_registry.models.database_models import Transaction, Wallet
    from duxos_registry.services.auth_service import AuthLevel, NodeAuthService
    from duxos_registry.services.wallet_service import (
        FlopcoinWalletService,
        WalletService,
    )
except ImportError:
    # Fallback for standalone development
    FlopcoinWalletService = None
    WalletService = None
    NodeAuthService = None
    AuthLevel = None
    WalletRepository = None
    TransactionRepository = None
    Wallet = None
    Transaction = None

from .exceptions import (
    InsufficientFundsError,
    TransactionFailedError,
    WalletIntegrationError,
)
from .models import CommunityFund, Escrow, EscrowTransaction

logger = logging.getLogger(__name__)


class EscrowWalletIntegration:
    """Real wallet integration for escrow system"""

    def __init__(self, db: Session, config: Optional[Dict[str, Any]] = None):
        self.db = db
        self.config = config or {}

        # Initialize wallet services
        self._init_wallet_services()

        # Initialize repositories
        self.wallet_repo = WalletRepository(db) if WalletRepository else None
        self.transaction_repo = TransactionRepository(db) if TransactionRepository else None

        # Authentication service
        self.auth_service = NodeAuthService() if NodeAuthService else None

        # Fund locking state
        self.locked_funds: Dict[str, Dict[str, Any]] = {}  # escrow_id -> fund_info

        # Transaction tracking
        self.pending_transactions: Dict[str, Dict[str, Any]] = {}

        logger.info("Escrow Wallet Integration initialized")

    def _init_wallet_services(self):
        """Initialize wallet services"""
        try:
            # Load configuration
            rpc_config = self.config.get("rpc", {})
            rpc_host = rpc_config.get("host", "127.0.0.1")
            rpc_port = rpc_config.get("port", 32553)
            rpc_user = rpc_config.get("user", "flopcoinrpc")
            rpc_password = rpc_config.get("password", "password123")

            # Initialize Flopcoin service
            if FlopcoinWalletService:
                self.flopcoin_service = FlopcoinWalletService(
                    rpc_host=rpc_host,
                    rpc_port=rpc_port,
                    rpc_user=rpc_user,
                    rpc_password=rpc_password,
                )
                logger.info("Flopcoin wallet service initialized")
            else:
                self.flopcoin_service = None
                logger.warning("Flopcoin wallet service not available")

            # Initialize registry wallet service
            if WalletService:
                self.registry_wallet_service = WalletService(self.db)
                logger.info("Registry wallet service initialized")
            else:
                self.registry_wallet_service = None
                logger.warning("Registry wallet service not available")

        except Exception as e:
            logger.error(f"Failed to initialize wallet services: {e}")
            self.flopcoin_service = None
            self.registry_wallet_service = None

    def lock_funds(
        self,
        wallet_id: int,
        amount: float,
        escrow_id: str,
        auth_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Lock funds in a wallet for escrow

        Args:
            wallet_id: ID of the wallet to lock funds from
            amount: Amount to lock
            escrow_id: Escrow contract ID
            auth_data: Authentication data for the operation

        Returns:
            True if funds were successfully locked
        """
        try:
            # Validate inputs
            if amount <= 0:
                raise ValueError("Amount must be positive")

            if not self.flopcoin_service:
                raise WalletIntegrationError("Flopcoin service not available")

            # Get wallet information
            wallet = self.wallet_repo.get_wallet_by_id(wallet_id) if self.wallet_repo else None
            if not wallet:
                raise WalletIntegrationError(f"Wallet {wallet_id} not found")

            # Check balance
            balance_info = self.flopcoin_service.get_balance()
            available_balance = balance_info.get("confirmed", 0.0)

            if available_balance < amount:
                raise InsufficientFundsError(f"Insufficient funds: {available_balance} < {amount}")

            # Check if funds are already locked for this escrow
            if escrow_id in self.locked_funds:
                raise WalletIntegrationError(f"Funds already locked for escrow {escrow_id}")

            # Create fund lock record
            lock_info = {
                "wallet_id": wallet_id,
                "amount": amount,
                "escrow_id": escrow_id,
                "locked_at": datetime.now(timezone.utc),
                "status": "locked",
                "transaction_id": None,
            }

            # Store lock information
            self.locked_funds[escrow_id] = lock_info

            # Record the lock in database
            self._record_fund_lock(escrow_id, wallet_id, amount)

            logger.info(f"Locked {amount} FLOP from wallet {wallet_id} for escrow {escrow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to lock funds for escrow {escrow_id}: {e}")
            raise

    def unlock_funds(self, escrow_id: str) -> bool:
        """
        Unlock funds for an escrow (for refunds or cancellations)

        Args:
            escrow_id: Escrow contract ID

        Returns:
            True if funds were successfully unlocked
        """
        try:
            if escrow_id not in self.locked_funds:
                logger.warning(f"No locked funds found for escrow {escrow_id}")
                return True  # Nothing to unlock

            lock_info = self.locked_funds[escrow_id]

            # Update lock status
            lock_info["status"] = "unlocked"
            lock_info["unlocked_at"] = datetime.now(timezone.utc)

            # Remove from locked funds
            del self.locked_funds[escrow_id]

            # Record the unlock in database
            self._record_fund_unlock(escrow_id, lock_info["wallet_id"], lock_info["amount"])

            logger.info(f"Unlocked {lock_info['amount']} FLOP for escrow {escrow_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unlock funds for escrow {escrow_id}: {e}")
            raise

    def transfer_funds(
        self,
        from_wallet_id: Optional[int],
        to_wallet_id: int,
        amount: float,
        escrow_id: str,
        auth_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Transfer funds between wallets (or from escrow to wallet)

        Args:
            from_wallet_id: Source wallet ID (None for escrow funds)
            to_wallet_id: Destination wallet ID
            amount: Amount to transfer
            escrow_id: Escrow contract ID
            auth_data: Authentication data

        Returns:
            Transaction ID
        """
        try:
            # Validate inputs
            if amount <= 0:
                raise ValueError("Amount must be positive")

            if not self.flopcoin_service:
                raise WalletIntegrationError("Flopcoin service not available")

            # Get destination wallet
            to_wallet = (
                self.wallet_repo.get_wallet_by_id(to_wallet_id) if self.wallet_repo else None
            )
            if not to_wallet:
                raise WalletIntegrationError(f"Destination wallet {to_wallet_id} not found")

            # Handle escrow fund transfer (from locked funds)
            if from_wallet_id is None:
                return self._transfer_from_escrow(to_wallet_id, amount, escrow_id)

            # Handle regular wallet-to-wallet transfer
            return self._transfer_between_wallets(from_wallet_id, to_wallet_id, amount, escrow_id)

        except Exception as e:
            logger.error(f"Failed to transfer funds for escrow {escrow_id}: {e}")
            raise

    def _transfer_from_escrow(self, to_wallet_id: int, amount: float, escrow_id: str) -> str:
        """Transfer funds from escrow to wallet"""
        try:
            # Verify funds are locked for this escrow
            if escrow_id not in self.locked_funds:
                raise WalletIntegrationError(f"No locked funds for escrow {escrow_id}")

            lock_info = self.locked_funds[escrow_id]
            if lock_info["amount"] < amount:
                raise InsufficientFundsError(
                    f"Insufficient locked funds: {lock_info['amount']} < {amount}"
                )

            # Get destination wallet address
            to_wallet = (
                self.wallet_repo.get_wallet_by_id(to_wallet_id) if self.wallet_repo else None
            )
            if not to_wallet:
                raise WalletIntegrationError(f"Destination wallet {to_wallet_id} not found")

            # Send transaction via Flopcoin Core
            transaction_info = self.flopcoin_service.send_transaction(
                to_address=to_wallet.address, amount=amount, comment=f"Escrow {escrow_id} payment"
            )

            txid = transaction_info.get("txid")
            if not txid:
                raise TransactionFailedError("No transaction ID returned")

            # Update lock information
            lock_info["amount"] -= amount
            if lock_info["amount"] <= 0:
                # All funds transferred, remove lock
                del self.locked_funds[escrow_id]

            # Record transaction in database
            self._record_escrow_transaction(escrow_id, txid, amount, to_wallet_id, "release")

            logger.info(
                f"Transferred {amount} FLOP from escrow {escrow_id} to wallet {to_wallet_id}"
            )
            return txid

        except Exception as e:
            logger.error(f"Failed to transfer from escrow {escrow_id}: {e}")
            raise

    def _transfer_between_wallets(
        self, from_wallet_id: int, to_wallet_id: int, amount: float, escrow_id: str
    ) -> str:
        """Transfer funds between two wallets"""
        try:
            # Get wallet addresses
            from_wallet = (
                self.wallet_repo.get_wallet_by_id(from_wallet_id) if self.wallet_repo else None
            )
            to_wallet = (
                self.wallet_repo.get_wallet_by_id(to_wallet_id) if self.wallet_repo else None
            )

            if not from_wallet or not to_wallet:
                raise WalletIntegrationError("Source or destination wallet not found")

            # Check source wallet balance
            balance_info = self.flopcoin_service.get_balance()
            available_balance = balance_info.get("confirmed", 0.0)

            if available_balance < amount:
                raise InsufficientFundsError(f"Insufficient funds: {available_balance} < {amount}")

            # Send transaction via Flopcoin Core
            transaction_info = self.flopcoin_service.send_transaction(
                to_address=to_wallet.address, amount=amount, comment=f"Escrow {escrow_id} transfer"
            )

            txid = transaction_info.get("txid")
            if not txid:
                raise TransactionFailedError("No transaction ID returned")

            # Record transaction in database
            self._record_escrow_transaction(escrow_id, txid, amount, to_wallet_id, "transfer")

            logger.info(
                f"Transferred {amount} FLOP from wallet {from_wallet_id} to wallet {to_wallet_id}"
            )
            return txid

        except Exception as e:
            logger.error(f"Failed to transfer between wallets: {e}")
            raise

    def add_to_community_fund(self, amount: float, escrow_id: str) -> str:
        """
        Add funds to community fund

        Args:
            amount: Amount to add
            escrow_id: Escrow contract ID

        Returns:
            Transaction ID
        """
        try:
            if amount <= 0:
                raise ValueError("Amount must be positive")

            # Get community fund wallet (this would be a special wallet)
            # For now, we'll use a placeholder address
            community_address = self.config.get("community_fund_address", "FLOPcommunityfund123")

            # Send transaction to community fund
            transaction_info = self.flopcoin_service.send_transaction(
                to_address=community_address,
                amount=amount,
                comment=f"Community fund contribution from escrow {escrow_id}",
            )

            txid = transaction_info.get("txid")
            if not txid:
                raise TransactionFailedError("No transaction ID returned")

            # Update community fund balance in database
            self._update_community_fund_balance(amount)

            # Record transaction
            self._record_escrow_transaction(escrow_id, txid, amount, None, "community_fund")

            logger.info(f"Added {amount} FLOP to community fund from escrow {escrow_id}")
            return txid

        except Exception as e:
            logger.error(f"Failed to add to community fund: {e}")
            raise

    def validate_transaction_signature(
        self, escrow: Escrow, signature: str, message: str, node_id: str
    ) -> bool:
        """
        Validate transaction signature using authentication service

        Args:
            escrow: Escrow contract
            signature: Signature to validate
            message: Original message
            node_id: Node ID that created the signature

        Returns:
            True if signature is valid
        """
        try:
            if not self.auth_service:
                logger.warning(
                    "Authentication service not available, skipping signature validation"
                )
                return True

            # Verify signature using authentication service
            is_valid = self.auth_service.verify_node_signature(node_id, message, signature)

            if is_valid:
                logger.info(f"Transaction signature validated for escrow {escrow.id}")
            else:
                logger.warning(f"Invalid transaction signature for escrow {escrow.id}")

            return is_valid

        except Exception as e:
            logger.error(f"Error validating transaction signature: {e}")
            return False

    def get_locked_funds_info(self, escrow_id: str) -> Optional[Dict[str, Any]]:
        """Get information about locked funds for an escrow"""
        return self.locked_funds.get(escrow_id)

    def get_total_locked_funds(self) -> float:
        """Get total amount of locked funds across all escrows"""
        return sum(lock_info["amount"] for lock_info in self.locked_funds.values())

    def _record_fund_lock(self, escrow_id: str, wallet_id: int, amount: float):
        """Record fund lock in database"""
        try:
            if self.transaction_repo:
                self.transaction_repo.create_transaction(
                    wallet_id=wallet_id,
                    txid=f"lock_{escrow_id}_{int(time.time())}",
                    recipient_address="ESCROW_LOCK",
                    amount=amount,
                    transaction_type="lock",
                    status="confirmed",
                )
        except Exception as e:
            logger.error(f"Failed to record fund lock: {e}")

    def _record_fund_unlock(self, escrow_id: str, wallet_id: int, amount: float):
        """Record fund unlock in database"""
        try:
            if self.transaction_repo:
                self.transaction_repo.create_transaction(
                    wallet_id=wallet_id,
                    txid=f"unlock_{escrow_id}_{int(time.time())}",
                    recipient_address="ESCROW_UNLOCK",
                    amount=amount,
                    transaction_type="unlock",
                    status="confirmed",
                )
        except Exception as e:
            logger.error(f"Failed to record fund unlock: {e}")

    def _record_escrow_transaction(
        self,
        escrow_id: str,
        txid: str,
        amount: float,
        to_wallet_id: Optional[int],
        transaction_type: str,
    ):
        """Record escrow transaction in database"""
        try:
            if self.transaction_repo and to_wallet_id:
                self.transaction_repo.create_transaction(
                    wallet_id=to_wallet_id,
                    txid=txid,
                    recipient_address="ESCROW_PAYMENT",
                    amount=amount,
                    transaction_type=transaction_type,
                    status="pending",
                )
        except Exception as e:
            logger.error(f"Failed to record escrow transaction: {e}")

    def _update_community_fund_balance(self, amount: float):
        """Update community fund balance in database"""
        try:
            fund = self.db.query(CommunityFund).first()
            if fund:
                fund.balance += amount
                fund.updated_at = datetime.now(timezone.utc)
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update community fund balance: {e}")


class EscrowTransactionSigner:
    """Handles transaction signing for escrow operations"""

    def __init__(self, auth_service: Optional[NodeAuthService] = None):
        self.auth_service = auth_service

    def sign_escrow_creation(
        self, node_id: str, secret_key: str, escrow_data: Dict[str, Any]
    ) -> str:
        """Sign escrow creation data"""
        try:
            # Create message to sign
            message_data = {
                "escrow_id": escrow_data.get("escrow_id"),
                "payer_wallet_id": escrow_data.get("payer_wallet_id"),
                "provider_wallet_id": escrow_data.get("provider_wallet_id"),
                "amount": escrow_data.get("amount"),
                "service_name": escrow_data.get("service_name"),
                "timestamp": int(time.time()),
            }

            message = json.dumps(message_data, sort_keys=True)

            # Create signature
            if self.auth_service:
                return self.auth_service.create_signed_message(node_id, secret_key, message)
            else:
                # Fallback signature creation
                key = secret_key.encode()
                signature = hmac.new(key, message.encode(), hashlib.sha256).digest()
                return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Failed to sign escrow creation: {e}")
            raise

    def sign_escrow_release(
        self, node_id: str, secret_key: str, escrow_id: str, result_hash: str
    ) -> str:
        """Sign escrow release data"""
        try:
            # Create message to sign
            message_data = {
                "escrow_id": escrow_id,
                "result_hash": result_hash,
                "action": "release",
                "timestamp": int(time.time()),
            }

            message = json.dumps(message_data, sort_keys=True)

            # Create signature
            if self.auth_service:
                return self.auth_service.create_signed_message(node_id, secret_key, message)
            else:
                # Fallback signature creation
                key = secret_key.encode()
                signature = hmac.new(key, message.encode(), hashlib.sha256).digest()
                return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Failed to sign escrow release: {e}")
            raise
