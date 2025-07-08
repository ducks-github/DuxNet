"""
Tests for Community Fund functionality
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from duxos_escrow.community_fund_manager import CommunityFundManager
from duxos_escrow.exceptions import CommunityFundError
from duxos_escrow.models import Base, CommunityFund, Escrow, EscrowStatus
from duxos_registry.models.database_models import Node, Wallet


@pytest.fixture(scope="function")
def db_session():
    # Use a file-based SQLite database to avoid threading issues
    engine = create_engine(
        "sqlite:///test_community_fund.db", connect_args={"check_same_thread": False}
    )

    # Import all models to ensure they're registered with Base
    from duxos_escrow.models import CommunityFund, Dispute, Escrow, EscrowTransaction
    from duxos_registry.models.database_models import Node, Wallet

    # Create all tables including escrow and wallet models
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test wallets
    node1 = Node(node_id="test_node_1", address="127.0.0.1:8001")
    node2 = Node(node_id="test_node_2", address="127.0.0.1:8002")
    session.add(node1)
    session.add(node2)
    session.commit()

    wallet1 = Wallet(node_id="test_node_1", wallet_name="test_wallet_1", address="addr1")
    wallet2 = Wallet(node_id="test_node_2", wallet_name="test_wallet_2", address="addr2")
    session.add(wallet1)
    session.add(wallet2)
    session.commit()

    yield session
    session.close()

    # Clean up the test database
    import os

    if os.path.exists("test_community_fund.db"):
        os.remove("test_community_fund.db")


@pytest.fixture
def fund_manager(db_session):
    return CommunityFundManager(db_session)


def test_create_community_fund(fund_manager, db_session):
    """Test that community fund is created automatically"""
    fund = db_session.query(CommunityFund).first()
    assert fund is not None
    assert fund.balance == 0.0
    assert fund.airdrop_threshold == 100.0
    assert fund.governance_enabled is True


def test_get_fund_balance(fund_manager):
    """Test getting fund balance"""
    balance = fund_manager.get_fund_balance()
    assert balance == 0.0


def test_add_to_fund(fund_manager, db_session):
    """Test adding funds to community fund"""
    success = fund_manager.add_to_fund(50.0)
    assert success is True

    fund = db_session.query(CommunityFund).first()
    assert fund.balance == 50.0


def test_add_to_fund_invalid_amount(fund_manager):
    """Test adding invalid amount to fund"""
    with pytest.raises(ValueError):
        fund_manager.add_to_fund(-10.0)

    with pytest.raises(ValueError):
        fund_manager.add_to_fund(0.0)


def test_remove_from_fund(fund_manager, db_session):
    """Test removing funds from community fund"""
    # Add funds first
    fund_manager.add_to_fund(100.0)

    # Remove funds
    success = fund_manager.remove_from_fund(30.0, "Test withdrawal")
    assert success is True

    fund = db_session.query(CommunityFund).first()
    assert fund.balance == 70.0


def test_remove_from_fund_insufficient_balance(fund_manager):
    """Test removing more funds than available"""
    fund_manager.add_to_fund(50.0)

    with pytest.raises(CommunityFundError):
        fund_manager.remove_from_fund(100.0, "Should fail")


def test_remove_from_fund_invalid_amount(fund_manager):
    """Test removing invalid amount"""
    with pytest.raises(ValueError):
        fund_manager.remove_from_fund(-10.0, "Invalid")

    with pytest.raises(ValueError):
        fund_manager.remove_from_fund(0.0, "Invalid")


def test_check_airdrop_eligibility_below_threshold(fund_manager):
    """Test airdrop eligibility when below threshold"""
    eligible = fund_manager.check_airdrop_eligibility()
    assert eligible is False


def test_check_airdrop_eligibility_above_threshold(fund_manager):
    """Test airdrop eligibility when above threshold"""
    fund_manager.add_to_fund(150.0)  # Above 100.0 threshold
    eligible = fund_manager.check_airdrop_eligibility()
    assert eligible is True


def test_execute_airdrop_no_active_wallets(fund_manager):
    """Test airdrop execution with no active wallets"""
    fund_manager.add_to_fund(150.0)

    with pytest.raises(CommunityFundError, match="No active wallets found"):
        fund_manager.execute_airdrop()


def test_execute_airdrop_with_active_wallets(fund_manager, db_session):
    """Test airdrop execution with active wallets"""
    # Add funds
    fund_manager.add_to_fund(200.0)

    # Create active escrows
    escrow1 = Escrow(
        id="test_escrow_1",
        payer_wallet_id=1,
        provider_wallet_id=2,
        amount=50.0,
        status=EscrowStatus.RELEASED,
        service_name="test_service",
    )
    escrow2 = Escrow(
        id="test_escrow_2",
        payer_wallet_id=2,
        provider_wallet_id=1,
        amount=30.0,
        status=EscrowStatus.ACTIVE,
        service_name="test_service",
    )
    db_session.add(escrow1)
    db_session.add(escrow2)
    db_session.commit()

    # Execute airdrop
    result = fund_manager.execute_airdrop(distribution_ratio=0.5)

    assert result["total_amount"] == 100.0  # 50% of 200
    assert result["wallet_count"] == 2  # Two unique wallets
    assert result["per_wallet_amount"] == 50.0  # 100 / 2
    assert result["wallets"] == [1, 2]  # Wallet IDs

    # Check fund balance was reduced
    fund = db_session.query(CommunityFund).first()
    assert fund.balance == 100.0  # 200 - 100


def test_execute_airdrop_below_threshold(fund_manager):
    """Test airdrop execution when below threshold"""
    fund_manager.add_to_fund(50.0)  # Below 100.0 threshold

    with pytest.raises(CommunityFundError, match="Airdrop threshold not met"):
        fund_manager.execute_airdrop()


def test_get_airdrop_history_no_history(fund_manager):
    """Test getting airdrop history when none exists"""
    history = fund_manager.get_airdrop_history()
    assert history == []


def test_get_airdrop_history_with_history(fund_manager, db_session):
    """Test getting airdrop history"""
    # Add funds and execute airdrop
    fund_manager.add_to_fund(200.0)

    # Create active escrow
    escrow = Escrow(
        id="test_escrow",
        payer_wallet_id=1,
        provider_wallet_id=2,
        amount=50.0,
        status=EscrowStatus.RELEASED,
        service_name="test_service",
    )
    db_session.add(escrow)
    db_session.commit()

    fund_manager.execute_airdrop(distribution_ratio=0.5)

    # Get history
    history = fund_manager.get_airdrop_history()
    assert len(history) == 1
    assert history[0]["amount"] == 100.0


def test_update_airdrop_threshold(fund_manager, db_session):
    """Test updating airdrop threshold"""
    success = fund_manager.update_airdrop_threshold(200.0)
    assert success is True

    fund = db_session.query(CommunityFund).first()
    assert fund.airdrop_threshold == 200.0


def test_update_airdrop_threshold_invalid(fund_manager):
    """Test updating airdrop threshold with invalid value"""
    with pytest.raises(ValueError):
        fund_manager.update_airdrop_threshold(-10.0)

    with pytest.raises(ValueError):
        fund_manager.update_airdrop_threshold(0.0)


def test_get_fund_stats(fund_manager, db_session):
    """Test getting comprehensive fund statistics"""
    # Add some activity
    fund_manager.add_to_fund(150.0)

    # Create some escrows
    escrow1 = Escrow(
        id="test_escrow_1",
        payer_wallet_id=1,
        provider_wallet_id=2,
        amount=50.0,
        status=EscrowStatus.RELEASED,
        service_name="test_service",
    )
    escrow2 = Escrow(
        id="test_escrow_2",
        payer_wallet_id=2,
        provider_wallet_id=1,
        amount=30.0,
        status=EscrowStatus.ACTIVE,
        service_name="test_service",
    )
    db_session.add(escrow1)
    db_session.add(escrow2)
    db_session.commit()

    stats = fund_manager.get_fund_stats()

    assert stats["balance"] == 150.0
    assert stats["airdrop_threshold"] == 100.0
    assert stats["governance_enabled"] is True
    assert stats["airdrop_eligible"] is True
    assert stats["recent_activity"]["total_escrows"] == 2
    assert stats["recent_activity"]["escrows_last_30_days"] == 2


def test_airdrop_distribution_ratio(fund_manager, db_session):
    """Test airdrop with different distribution ratios"""
    fund_manager.add_to_fund(1000.0)

    # Create active escrow
    escrow = Escrow(
        id="test_escrow",
        payer_wallet_id=1,
        provider_wallet_id=2,
        amount=50.0,
        status=EscrowStatus.RELEASED,
        service_name="test_service",
    )
    db_session.add(escrow)
    db_session.commit()

    # Test 25% distribution
    result = fund_manager.execute_airdrop(distribution_ratio=0.25)
    assert result["total_amount"] == 250.0  # 25% of 1000
    assert result["per_wallet_amount"] == 125.0  # 250 / 2 wallets

    # Check remaining balance
    fund = db_session.query(CommunityFund).first()
    assert fund.balance == 750.0  # 1000 - 250
