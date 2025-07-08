import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from duxos_escrow.dispute_resolver import DisputeResolver
from duxos_escrow.escrow_manager import EscrowManager
from duxos_escrow.models import Base, DisputeStatus, EscrowStatus

# Import wallet models for foreign key relationships
from duxos_registry.models.database_models import Node, Wallet


@pytest.fixture(scope="function")
def db_session():
    # Use a file-based SQLite database to avoid threading issues
    engine = create_engine(
        "sqlite:///test_escrow_logic.db", connect_args={"check_same_thread": False}
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

    if os.path.exists("test_escrow_logic.db"):
        os.remove("test_escrow_logic.db")


@pytest.fixture
def escrow_manager(db_session):
    return EscrowManager(db_session)


@pytest.fixture
def dispute_resolver(db_session):
    return DisputeResolver(db_session)


def test_create_escrow(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=100.0, service_name="test_service"
    )
    assert escrow.id is not None
    assert escrow.status == EscrowStatus.PENDING or escrow.status == EscrowStatus.ACTIVE
    assert escrow.amount == 100.0
    assert escrow.provider_amount == 95.0
    assert escrow.community_amount == 5.0


def test_release_escrow(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=50.0, service_name="test_service"
    )
    escrow_id = escrow.id
    # Simulate activation
    escrow.status = EscrowStatus.ACTIVE  # type: ignore
    db_session.commit()
    # Release
    result_hash = "a" * 64
    provider_signature = "b" * 64
    success = escrow_manager.release_escrow(escrow_id, result_hash, provider_signature)
    assert success
    escrow = escrow_manager.get_escrow(escrow_id)
    assert escrow.status == EscrowStatus.RELEASED
    assert escrow.result_hash == result_hash
    assert escrow.provider_signature == provider_signature


def test_refund_escrow(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=25.0, service_name="test_service"
    )
    escrow_id = escrow.id
    # Simulate activation
    escrow.status = EscrowStatus.ACTIVE  # type: ignore
    db_session.commit()
    # Refund
    success = escrow_manager.refund_escrow(escrow_id, reason="Test refund")
    assert success
    escrow = escrow_manager.get_escrow(escrow_id)
    assert escrow.status == EscrowStatus.REFUNDED


def test_create_and_resolve_dispute(escrow_manager, dispute_resolver, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=75.0, service_name="test_service"
    )
    escrow_id = escrow.id
    # Simulate activation
    escrow.status = EscrowStatus.ACTIVE  # type: ignore
    db_session.commit()
    # Create dispute
    dispute = dispute_resolver.create_dispute(
        escrow_id=escrow_id, initiator_wallet_id=1, reason="Test dispute"
    )
    assert dispute.id is not None
    assert dispute.status == DisputeStatus.OPEN
    # Resolve dispute
    success = dispute_resolver.resolve_dispute(
        dispute_id=dispute.id, resolution="Payer wins", winner_wallet_id=1
    )
    assert success
    dispute = dispute_resolver.get_dispute(dispute.id)
    assert dispute.status == DisputeStatus.RESOLVED
    escrow = escrow_manager.get_escrow(escrow_id)
    assert escrow.status == EscrowStatus.REFUNDED or escrow.status == EscrowStatus.RESOLVED


def test_create_escrow_invalid_amount(escrow_manager):
    with pytest.raises(ValueError):
        escrow_manager.create_escrow(
            payer_wallet_id=1, provider_wallet_id=2, amount=-10.0, service_name="test_service"
        )


def test_create_escrow_same_payer_provider(escrow_manager):
    with pytest.raises(ValueError):
        escrow_manager.create_escrow(
            payer_wallet_id=1, provider_wallet_id=1, amount=10.0, service_name="test_service"
        )


def test_release_escrow_invalid_state(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=10.0, service_name="test_service"
    )
    escrow_id = escrow.id
    # Not activated
    with pytest.raises(ValueError):
        escrow_manager.release_escrow(escrow_id, "a" * 64, "b" * 64)


def test_refund_escrow_invalid_state(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=10.0, service_name="test_service"
    )
    escrow_id = escrow.id
    # Not activated
    with pytest.raises(ValueError):
        escrow_manager.refund_escrow(escrow_id, reason="Should fail")


def test_double_release(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=10.0, service_name="test_service"
    )
    escrow_id = escrow.id
    escrow.status = escrow.status.ACTIVE  # type: ignore
    db_session.commit()
    escrow_manager.release_escrow(escrow_id, "a" * 64, "b" * 64)
    with pytest.raises(ValueError):
        escrow_manager.release_escrow(escrow_id, "a" * 64, "b" * 64)


def test_double_refund(escrow_manager, db_session):
    escrow = escrow_manager.create_escrow(
        payer_wallet_id=1, provider_wallet_id=2, amount=10.0, service_name="test_service"
    )
    escrow_id = escrow.id
    escrow.status = escrow.status.ACTIVE  # type: ignore
    db_session.commit()
    escrow_manager.refund_escrow(escrow_id, reason="First refund")
    with pytest.raises(ValueError):
        escrow_manager.refund_escrow(escrow_id, reason="Second refund")
