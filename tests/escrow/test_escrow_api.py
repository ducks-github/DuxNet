import pytest
from fastapi.testclient import TestClient
from duxos_escrow.api import app, escrow_manager
from duxos_escrow.escrow_manager import EscrowManager
from duxos_escrow.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import wallet models for foreign key relationships
from duxos_registry.models.database_models import Wallet, Node

@pytest.fixture(scope="function", autouse=True)
def setup_test_db(monkeypatch):
    # Use a file-based SQLite database to avoid threading issues
    engine = create_engine("sqlite:///test_escrow_api.db", connect_args={"check_same_thread": False})
    
    # Import all models to ensure they're registered with Base
    from duxos_escrow.models import Escrow, Dispute, CommunityFund, EscrowTransaction
    from duxos_registry.models.database_models import Wallet, Node
    
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
    
    # Patch the global escrow_manager in the API
    test_manager = EscrowManager(session)
    monkeypatch.setattr("duxos_escrow.api.escrow_manager", test_manager)
    yield session
    session.close()
    
    # Clean up the test database
    import os
    if os.path.exists("test_escrow_api.db"):
        os.remove("test_escrow_api.db")

@pytest.fixture
def client():
    return TestClient(app)

def test_create_escrow_api(client):
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 10.0,
        "service_name": "api_test_service"
    }
    response = client.post("/escrow/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["escrow_id"]
    assert data["amount"] == 10.0
    assert data["provider_amount"] == 9.5
    assert data["community_amount"] == 0.5

def test_release_escrow_api(client):
    # Create escrow first
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 20.0,
        "service_name": "api_test_service"
    }
    create_resp = client.post("/escrow/create", json=payload)
    escrow_id = create_resp.json()["escrow_id"]
    # Simulate activation (would be done by business logic in real system)
    # For test, patch status directly
    from duxos_escrow.api import escrow_manager as manager
    escrow = manager.get_escrow(escrow_id)  # type: ignore
    escrow.status = escrow.status.ACTIVE  # type: ignore
    manager.db.commit()  # type: ignore
    # Release
    release_payload = {"result_hash": "a"*64, "provider_signature": "b"*64}
    resp = client.post(f"/escrow/{escrow_id}/release", json=release_payload)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Escrow released successfully"

def test_refund_escrow_api(client):
    # Create escrow first
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 30.0,
        "service_name": "api_test_service"
    }
    create_resp = client.post("/escrow/create", json=payload)
    escrow_id = create_resp.json()["escrow_id"]
    # Simulate activation
    from duxos_escrow.api import escrow_manager as manager
    escrow = manager.get_escrow(escrow_id)  # type: ignore
    escrow.status = escrow.status.ACTIVE  # type: ignore
    manager.db.commit()  # type: ignore
    # Refund
    refund_payload = {"reason": "API test refund"}
    resp = client.post(f"/escrow/{escrow_id}/refund", json=refund_payload)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Escrow refunded successfully"

def test_create_dispute_api(client):
    # Create escrow first
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 40.0,
        "service_name": "api_test_service"
    }
    create_resp = client.post("/escrow/create", json=payload)
    escrow_id = create_resp.json()["escrow_id"]
    # Simulate activation
    from duxos_escrow.api import escrow_manager as manager
    escrow = manager.get_escrow(escrow_id)  # type: ignore
    escrow.status = escrow.status.ACTIVE  # type: ignore
    manager.db.commit()  # type: ignore
    # Create dispute
    dispute_payload = {"reason": "API test dispute", "evidence": {"proof": "test"}}
    resp = client.post(f"/escrow/{escrow_id}/dispute", json=dispute_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["dispute_id"]
    assert data["escrow_id"] == escrow_id

def test_add_evidence_api(client):
    # Create escrow and dispute first
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 50.0,
        "service_name": "api_test_service"
    }
    create_resp = client.post("/escrow/create", json=payload)
    escrow_id = create_resp.json()["escrow_id"]
    from duxos_escrow.api import escrow_manager as manager
    escrow = manager.get_escrow(escrow_id)
    escrow.status = escrow.status.ACTIVE  # type: ignore
    manager.db.commit()
    dispute_payload = {"reason": "API test dispute", "evidence": {"proof": "test"}}
    dispute_resp = client.post(f"/escrow/{escrow_id}/dispute", json=dispute_payload)
    dispute_id = dispute_resp.json()["dispute_id"]
    # Add evidence
    evidence_payload = {"evidence": {"extra": "evidence"}}
    resp = client.post(f"/dispute/{dispute_id}/evidence", json=evidence_payload)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Evidence added successfully"

def test_resolve_dispute_api(client):
    # Create escrow and dispute first
    payload = {
        "payer_wallet_id": 1,
        "provider_wallet_id": 2,
        "amount": 60.0,
        "service_name": "api_test_service"
    }
    create_resp = client.post("/escrow/create", json=payload)
    escrow_id = create_resp.json()["escrow_id"]
    from duxos_escrow.api import escrow_manager as manager
    escrow = manager.get_escrow(escrow_id)
    escrow.status = escrow.status.ACTIVE  # type: ignore
    manager.db.commit()
    dispute_payload = {"reason": "API test dispute", "evidence": {"proof": "test"}}
    dispute_resp = client.post(f"/escrow/{escrow_id}/dispute", json=dispute_payload)
    dispute_id = dispute_resp.json()["dispute_id"]
    # Resolve dispute
    resolve_payload = {"resolution": "Payer wins", "winner_wallet_id": 1}
    resp = client.post(f"/dispute/{dispute_id}/resolve", json=resolve_payload)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Dispute resolved successfully" 