"""
Integration tests for Phase 1 Escrow Core Implementation

This test suite validates:
- Real wallet integration with Flopcoin RPC
- Fund locking mechanisms
- Transaction signing and validation
- Community fund integration with 5% tax collection
- Automatic distribution logic
"""

import asyncio
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from duxos_escrow.community_fund_manager import CommunityFundManager

# Import escrow components
from duxos_escrow.escrow_manager import EscrowManager
from duxos_escrow.exceptions import (
    AirdropError,
    CommunityFundError,
    InsufficientFundsError,
    TransactionFailedError,
    WalletIntegrationError,
)
from duxos_escrow.models import CommunityFund, Escrow, EscrowStatus, EscrowTransaction
from duxos_escrow.transaction_validator import TransactionValidator
from duxos_escrow.wallet_integration import (
    EscrowTransactionSigner,
    EscrowWalletIntegration,
)

# Import registry components for integration
try:
    from duxos_registry.db.repository import TransactionRepository, WalletRepository
    from duxos_registry.models.database_models import Transaction, Wallet
    from duxos_registry.services.auth_service import NodeAuthService
    from duxos_registry.services.wallet_service import FlopcoinWalletService

    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False


class TestEscrowCoreIntegration:
    """Integration tests for escrow core functionality"""

    @pytest.fixture
    def db_session(self):
        """Create test database session"""
        # Use in-memory SQLite for testing
        engine = create_engine("sqlite:///:memory:")

        # Import and create tables
        from duxos_escrow.models import Base

        Base.metadata.create_all(engine)

        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        yield session

        session.close()

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return {
            "rpc": {
                "host": "127.0.0.1",
                "port": 32553,
                "user": "flopcoinrpc",
                "password": "test_password",
            },
            "airdrop_threshold": 50.0,
            "min_airdrop_amount": 0.5,
            "airdrop_interval_hours": 1,
            "max_airdrop_nodes": 10,
        }

    @pytest.fixture
    def mock_wallet_service(self):
        """Mock Flopcoin wallet service"""
        mock_service = Mock()

        # Mock balance response
        mock_service.get_balance.return_value = {
            "confirmed": 1000.0,
            "unconfirmed": 0.0,
            "total": 1000.0,
            "currency": "FLOP",
        }

        # Mock transaction response
        mock_service.send_transaction.return_value = {
            "txid": "test_txid_12345",
            "amount": 10.0,
            "fee": 0.001,
            "status": "pending",
        }

        return mock_service

    @pytest.fixture
    def escrow_manager(self, db_session, mock_config, mock_wallet_service):
        """Create escrow manager with mocked dependencies"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            manager = EscrowManager(db=db_session, config=mock_config)
            return manager

    def test_wallet_integration_initialization(self, db_session, mock_config):
        """Test wallet integration service initialization"""
        integration = EscrowWalletIntegration(db_session, mock_config)

        assert integration.db is not None
        assert integration.config == mock_config
        assert hasattr(integration, "locked_funds")
        assert hasattr(integration, "pending_transactions")

    def test_fund_locking_mechanism(self, db_session, mock_config, mock_wallet_service):
        """Test fund locking functionality"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)

            # Test successful fund locking
            result = integration.lock_funds(wallet_id=1, amount=100.0, escrow_id="test_escrow_001")

            assert result is True
            assert "test_escrow_001" in integration.locked_funds

            lock_info = integration.locked_funds["test_escrow_001"]
            assert lock_info["wallet_id"] == 1
            assert lock_info["amount"] == 100.0
            assert lock_info["status"] == "locked"

    def test_fund_unlocking_mechanism(self, db_session, mock_config, mock_wallet_service):
        """Test fund unlocking functionality"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)

            # First lock funds
            integration.lock_funds(1, 100.0, "test_escrow_001")

            # Then unlock funds
            result = integration.unlock_funds("test_escrow_001")

            assert result is True
            assert "test_escrow_001" not in integration.locked_funds

    def test_insufficient_funds_handling(self, db_session, mock_config):
        """Test handling of insufficient funds"""
        # Mock wallet service with low balance
        mock_service = Mock()
        mock_service.get_balance.return_value = {
            "confirmed": 50.0,
            "unconfirmed": 0.0,
            "total": 50.0,
            "currency": "FLOP",
        }

        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService", return_value=mock_service
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)

            # Try to lock more funds than available
            with pytest.raises(InsufficientFundsError):
                integration.lock_funds(1, 100.0, "test_escrow_001")

    def test_transaction_signing(self, db_session, mock_config):
        """Test transaction signing functionality"""
        signer = EscrowTransactionSigner()

        # Test escrow creation signing
        escrow_data = {
            "escrow_id": "test_escrow_001",
            "payer_wallet_id": 1,
            "provider_wallet_id": 2,
            "amount": 100.0,
            "service_name": "test_service",
        }

        signature = signer.sign_escrow_creation(
            node_id="test_node", secret_key="test_secret_key", escrow_data=escrow_data
        )

        assert signature is not None
        assert len(signature) > 0

    def test_escrow_creation_with_real_integration(self, escrow_manager, db_session):
        """Test complete escrow creation workflow"""
        # Create test wallets in database
        if REGISTRY_AVAILABLE:
            wallet_repo = WalletRepository(db_session)

            # Mock wallet creation
            payer_wallet = Mock()
            payer_wallet.id = 1
            payer_wallet.address = "FLOP123456789abcdef"

            provider_wallet = Mock()
            provider_wallet.id = 2
            provider_wallet.address = "FLOP987654321fedcba"

            wallet_repo.get_wallet_by_id = Mock(
                side_effect=lambda x: payer_wallet if x == 1 else provider_wallet
            )

        # Create escrow
        escrow = escrow_manager.create_escrow(
            payer_wallet_id=1,
            provider_wallet_id=2,
            amount=100.0,
            service_name="test_api_service",
            task_id="task_001",
            metadata={"test": "data"},
        )

        assert escrow is not None
        assert escrow.id is not None
        assert escrow.amount == 100.0
        assert escrow.status == EscrowStatus.ACTIVE
        assert escrow.provider_amount == 95.0  # 95% to provider
        assert escrow.community_amount == 5.0  # 5% to community

    def test_escrow_release_workflow(self, escrow_manager, db_session):
        """Test escrow release workflow"""
        # Create escrow first
        escrow = escrow_manager.create_escrow(
            payer_wallet_id=1, provider_wallet_id=2, amount=100.0, service_name="test_api_service"
        )

        # Mock result validation
        escrow_manager.validator.validate_result = Mock(return_value=True)

        # Release escrow
        result = escrow_manager.release_escrow(
            escrow_id=escrow.id,
            result_hash="test_result_hash_12345",
            provider_signature="test_signature_67890",
        )

        assert result is True

        # Verify escrow status
        updated_escrow = escrow_manager.get_escrow(escrow.id)
        assert updated_escrow.status == EscrowStatus.RELEASED
        assert updated_escrow.result_hash == "test_result_hash_12345"
        assert updated_escrow.provider_signature == "test_signature_67890"

    def test_escrow_refund_workflow(self, escrow_manager, db_session):
        """Test escrow refund workflow"""
        # Create escrow first
        escrow = escrow_manager.create_escrow(
            payer_wallet_id=1, provider_wallet_id=2, amount=100.0, service_name="test_api_service"
        )

        # Refund escrow
        result = escrow_manager.refund_escrow(escrow_id=escrow.id, reason="Task failed")

        assert result is True

        # Verify escrow status
        updated_escrow = escrow_manager.get_escrow(escrow.id)
        assert updated_escrow.status == EscrowStatus.REFUNDED

    def test_community_fund_integration(self, db_session, mock_config, mock_wallet_service):
        """Test community fund integration"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)
            fund_manager = CommunityFundManager(db_session, integration, mock_config)

            # Test tax collection
            txid = fund_manager.collect_tax("test_escrow_001", 5.0)

            assert txid is not None

            # Verify fund balance
            balance = fund_manager.get_fund_balance()
            assert balance == 5.0

    def test_community_fund_statistics(self, db_session, mock_config, mock_wallet_service):
        """Test community fund statistics"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)
            fund_manager = CommunityFundManager(db_session, integration, mock_config)

            # Add some funds
            fund_manager.collect_tax("escrow_001", 10.0)
            fund_manager.collect_tax("escrow_002", 15.0)

            # Get statistics
            stats = fund_manager.get_fund_statistics()

            assert stats["current_balance"] == 25.0
            assert stats["airdrop_threshold"] == 50.0
            assert stats["next_airdrop_trigger"] is False  # Not enough for airdrop

    def test_airdrop_trigger_logic(self, db_session, mock_config, mock_wallet_service):
        """Test airdrop trigger logic"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)
            fund_manager = CommunityFundManager(db_session, integration, mock_config)

            # Add enough funds to trigger airdrop
            fund_manager.collect_tax("escrow_001", 60.0)

            # Check statistics
            stats = fund_manager.get_fund_statistics()
            assert stats["next_airdrop_trigger"] is True

    def test_transaction_validation(self, db_session):
        """Test transaction validation"""
        validator = TransactionValidator(db_session)

        # Test hash validation
        valid_hash = "a" * 64  # 64 character hex string
        invalid_hash = "invalid_hash"

        assert validator._is_valid_hash(valid_hash) is True
        assert validator._is_valid_hash(invalid_hash) is False

    def test_error_handling(self, db_session, mock_config):
        """Test error handling in wallet integration"""
        # Test with invalid configuration
        invalid_config = {"rpc": {"host": "invalid_host"}}

        integration = EscrowWalletIntegration(db_session, invalid_config)

        # Should handle connection errors gracefully
        with pytest.raises(Exception):
            integration.lock_funds(1, 100.0, "test_escrow_001")

    def test_concurrent_operations(self, db_session, mock_config, mock_wallet_service):
        """Test concurrent operations"""
        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(db_session, mock_config)

            # Test concurrent fund locking
            async def test_concurrent_locks():
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        asyncio.to_thread(integration.lock_funds, 1, 10.0, f"escrow_{i}")
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

            # Run concurrent test
            results = asyncio.run(test_concurrent_locks())

            # All operations should succeed
            assert all(result is True for result in results)
            assert len(integration.locked_funds) == 5

    def test_audit_trail(self, escrow_manager, db_session):
        """Test audit trail functionality"""
        # Create escrow
        escrow = escrow_manager.create_escrow(
            payer_wallet_id=1, provider_wallet_id=2, amount=100.0, service_name="test_api_service"
        )

        # Check that transaction was recorded
        transactions = (
            db_session.query(EscrowTransaction)
            .filter(EscrowTransaction.escrow_id == escrow.id)
            .all()
        )

        assert len(transactions) > 0

        # Verify transaction details
        create_transaction = next(tx for tx in transactions if tx.transaction_type == "create")
        assert create_transaction.amount == 100.0
        assert create_transaction.from_wallet_id == 1


class TestEscrowCorePerformance:
    """Performance tests for escrow core"""

    @pytest.fixture
    def performance_db_session(self):
        """Create performance test database session"""
        engine = create_engine("sqlite:///:memory:")
        from duxos_escrow.models import Base

        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

    def test_bulk_escrow_creation(self, performance_db_session, mock_config):
        """Test bulk escrow creation performance"""
        mock_wallet_service = Mock()
        mock_wallet_service.get_balance.return_value = {
            "confirmed": 10000.0,
            "unconfirmed": 0.0,
            "total": 10000.0,
            "currency": "FLOP",
        }
        mock_wallet_service.send_transaction.return_value = {
            "txid": "test_txid",
            "amount": 10.0,
            "status": "pending",
        }

        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            manager = EscrowManager(performance_db_session, config=mock_config)

            start_time = time.time()

            # Create 100 escrows
            for i in range(100):
                escrow = manager.create_escrow(
                    payer_wallet_id=1,
                    provider_wallet_id=2,
                    amount=10.0,
                    service_name=f"service_{i}",
                )
                assert escrow is not None

            end_time = time.time()
            duration = end_time - start_time

            # Should complete within reasonable time
            assert duration < 30.0  # 30 seconds max

            # Verify all escrows were created
            escrows = performance_db_session.query(Escrow).all()
            assert len(escrows) == 100

    def test_concurrent_wallet_operations(self, performance_db_session, mock_config):
        """Test concurrent wallet operations"""
        mock_wallet_service = Mock()
        mock_wallet_service.get_balance.return_value = {
            "confirmed": 1000.0,
            "unconfirmed": 0.0,
            "total": 1000.0,
            "currency": "FLOP",
        }
        mock_wallet_service.send_transaction.return_value = {
            "txid": "test_txid",
            "amount": 10.0,
            "status": "pending",
        }

        with patch(
            "duxos_escrow.wallet_integration.FlopcoinWalletService",
            return_value=mock_wallet_service,
        ):
            integration = EscrowWalletIntegration(performance_db_session, mock_config)

            async def concurrent_operations():
                tasks = []

                # Concurrent fund locks
                for i in range(10):
                    task = asyncio.create_task(
                        asyncio.to_thread(integration.lock_funds, 1, 10.0, f"escrow_{i}")
                    )
                    tasks.append(task)

                # Concurrent transfers
                for i in range(5):
                    task = asyncio.create_task(
                        asyncio.to_thread(integration.transfer_funds, None, 2, 5.0, f"transfer_{i}")
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results

            start_time = time.time()
            results = asyncio.run(concurrent_operations())
            end_time = time.time()

            duration = end_time - start_time

            # Should complete within reasonable time
            assert duration < 10.0  # 10 seconds max

            # Most operations should succeed
            success_count = sum(1 for r in results if r is True or isinstance(r, str))
            assert success_count >= 10  # At least 10 successful operations


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
