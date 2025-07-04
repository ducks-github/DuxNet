"""
Integration tests for Wallet System (Phase 2.2)

This module tests the complete wallet integration with the registry system,
including wallet creation, balance checking, transaction sending, and
integration with the Flopcoin blockchain.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from duxos_registry.main import app
from duxos_registry.db.database import Base, get_db
from duxos_registry.services.wallet_service import WalletService
from duxos_registry.models.database_models import Node, Wallet, Transaction
from duxos_registry.db.repository import NodeRepository, WalletRepository, TransactionRepository


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wallet.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Get database session for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_node_data():
    """Sample node data for testing"""
    return {
        "node_id": "test_node_001",
        "address": "192.168.1.100:8080",
        "capabilities": ["gpu_compute", "wallet"]
    }


@pytest.fixture
def sample_wallet_data():
    """Sample wallet data for testing"""
    return {
        "node_id": "test_node_001",
        "wallet_name": "test_wallet",
        "address": "FLOP123456789abcdef",
        "wallet_type": "flopcoin",
        "balance": 100.0
    }


class TestWalletService:
    """Test wallet service functionality"""
    
    def test_wallet_service_initialization(self, db_session):
        """Test wallet service initialization"""
        wallet_service = WalletService(db_session)
        assert wallet_service is not None
        assert wallet_service.max_transaction_amount == 1000.0
        assert wallet_service.rate_limit_window == 3600
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_create_wallet_success(self, mock_rpc, db_session, sample_node_data):
        """Test successful wallet creation"""
        # Mock RPC call to return a new address
        mock_rpc.return_value = ("FLOP123456789abcdef", None)
        
        # Create a test node first
        node_repo = NodeRepository(db_session)
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        # Create wallet service and wallet
        wallet_service = WalletService(db_session)
        result = wallet_service.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet"
        )
        
        assert result["success"] is True
        assert "test_wallet" in result["message"]
        assert result["wallet"]["node_id"] == sample_node_data["node_id"]
        assert result["wallet"]["wallet_name"] == "test_wallet"
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_create_wallet_already_exists(self, mock_rpc, db_session, sample_node_data):
        """Test wallet creation when wallet already exists"""
        # Mock RPC call
        mock_rpc.return_value = ("FLOP123456789abcdef", None)
        
        # Create a test node
        node_repo = NodeRepository(db_session)
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        # Create wallet service
        wallet_service = WalletService(db_session)
        
        # Create wallet first time
        result1 = wallet_service.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet"
        )
        assert result1["success"] is True
        
        # Try to create wallet again
        result2 = wallet_service.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet2"
        )
        assert result2["success"] is False
        assert "already exists" in result2["message"]
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_get_wallet_balance_success(self, mock_rpc, db_session, sample_node_data):
        """Test successful balance retrieval"""
        # Mock RPC call to return balance
        mock_rpc.return_value = (150.75, None)
        
        # Create test node and wallet
        node_repo = NodeRepository(db_session)
        wallet_repo = WalletRepository(db_session)
        
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        wallet = wallet_repo.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet",
            address="FLOP123456789abcdef"
        )
        
        # Get balance
        wallet_service = WalletService(db_session)
        result = wallet_service.get_wallet_balance(sample_node_data["node_id"])
        
        assert result["success"] is True
        assert result["balance"] == 150.75
        assert result["currency"] == "FLOP"
    
    def test_get_wallet_balance_no_wallet(self, db_session, sample_node_data):
        """Test balance retrieval when no wallet exists"""
        # Create test node without wallet
        node_repo = NodeRepository(db_session)
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        # Try to get balance
        wallet_service = WalletService(db_session)
        result = wallet_service.get_wallet_balance(sample_node_data["node_id"])
        
        assert result["success"] is False
        assert "No wallet found" in result["message"]
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_send_transaction_success(self, mock_rpc, db_session, sample_node_data):
        """Test successful transaction sending"""
        # Mock RPC calls
        mock_rpc.side_effect = [
            (200.0, None),  # getbalance
            ("txid123456789", None)  # sendtoaddress
        ]
        
        # Create test node and wallet
        node_repo = NodeRepository(db_session)
        wallet_repo = WalletRepository(db_session)
        
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        wallet = wallet_repo.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet",
            address="FLOP123456789abcdef"
        )
        
        # Send transaction
        wallet_service = WalletService(db_session)
        result = wallet_service.send_transaction(
            node_id=sample_node_data["node_id"],
            recipient_address="FLOP987654321fedcba",
            amount=50.0
        )
        
        assert result["success"] is True
        assert result["txid"] == "txid123456789"
        assert result["amount"] == 50.0
        assert result["recipient"] == "FLOP987654321fedcba"
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_send_transaction_insufficient_balance(self, mock_rpc, db_session, sample_node_data):
        """Test transaction sending with insufficient balance"""
        # Mock RPC call to return low balance
        mock_rpc.return_value = (25.0, None)  # getbalance
        
        # Create test node and wallet
        node_repo = NodeRepository(db_session)
        wallet_repo = WalletRepository(db_session)
        
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        wallet = wallet_repo.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet",
            address="FLOP123456789abcdef"
        )
        
        # Try to send transaction
        wallet_service = WalletService(db_session)
        result = wallet_service.send_transaction(
            node_id=sample_node_data["node_id"],
            recipient_address="FLOP987654321fedcba",
            amount=50.0
        )
        
        assert result["success"] is False
        assert "Insufficient balance" in result["message"]
    
    def test_send_transaction_invalid_amount(self, db_session, sample_node_data):
        """Test transaction sending with invalid amount"""
        # Create test node and wallet
        node_repo = NodeRepository(db_session)
        wallet_repo = WalletRepository(db_session)
        
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        wallet = wallet_repo.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet",
            address="FLOP123456789abcdef"
        )
        
        # Try to send transaction with invalid amount
        wallet_service = WalletService(db_session)
        result = wallet_service.send_transaction(
            node_id=sample_node_data["node_id"],
            recipient_address="FLOP987654321fedcba",
            amount=-10.0
        )
        
        assert result["success"] is False
        assert "Invalid amount" in result["message"]
    
    @patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call')
    def test_generate_new_address_success(self, mock_rpc, db_session, sample_node_data):
        """Test successful address generation"""
        # Mock RPC call to return new address
        mock_rpc.return_value = ("FLOPnewaddress123", None)
        
        # Create test node and wallet
        node_repo = NodeRepository(db_session)
        wallet_repo = WalletRepository(db_session)
        
        node = node_repo.create_node(
            sample_node_data["node_id"],
            sample_node_data["address"],
            sample_node_data["capabilities"]
        )
        
        wallet = wallet_repo.create_wallet(
            node_id=sample_node_data["node_id"],
            wallet_name="test_wallet",
            address="FLOP123456789abcdef"
        )
        
        # Generate new address
        wallet_service = WalletService(db_session)
        result = wallet_service.generate_new_address(sample_node_data["node_id"])
        
        assert result["success"] is True
        assert result["new_address"] == "FLOPnewaddress123"
        assert result["wallet_name"] == "test_wallet"


class TestWalletAPI:
    """Test wallet API endpoints"""
    
    def test_create_wallet_api(self, setup_database, sample_node_data):
        """Test wallet creation via API"""
        # First create a node
        node_response = client.post("/nodes/register", json=sample_node_data)
        assert node_response.status_code == 200
        
        # Create wallet
        wallet_data = {
            "node_id": sample_node_data["node_id"],
            "wallet_name": "test_wallet"
        }
        
        with patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call') as mock_rpc:
            mock_rpc.return_value = ("FLOP123456789abcdef", None)
            
            response = client.post("/wallet/create", json=wallet_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "test_wallet" in data["message"]
    
    def test_get_wallet_api(self, setup_database, sample_node_data):
        """Test wallet retrieval via API"""
        # Create node and wallet
        node_response = client.post("/nodes/register", json=sample_node_data)
        assert node_response.status_code == 200
        
        wallet_data = {
            "node_id": sample_node_data["node_id"],
            "wallet_name": "test_wallet"
        }
        
        with patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call') as mock_rpc:
            mock_rpc.return_value = ("FLOP123456789abcdef", None)
            
            # Create wallet
            create_response = client.post("/wallet/create", json=wallet_data)
            assert create_response.status_code == 200
            
            # Get wallet
            get_response = client.get(f"/wallet/{sample_node_data['node_id']}")
            assert get_response.status_code == 200
            
            data = get_response.json()
            assert data["node_id"] == sample_node_data["node_id"]
            assert data["wallet_name"] == "test_wallet"
    
    def test_get_wallet_balance_api(self, setup_database, sample_node_data):
        """Test wallet balance retrieval via API"""
        # Create node and wallet
        node_response = client.post("/nodes/register", json=sample_node_data)
        assert node_response.status_code == 200
        
        wallet_data = {
            "node_id": sample_node_data["node_id"],
            "wallet_name": "test_wallet"
        }
        
        with patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call') as mock_rpc:
            mock_rpc.side_effect = [
                ("FLOP123456789abcdef", None),  # getnewaddress
                (150.75, None)  # getbalance
            ]
            
            # Create wallet
            create_response = client.post("/wallet/create", json=wallet_data)
            assert create_response.status_code == 200
            
            # Get balance
            balance_response = client.get(f"/wallet/{sample_node_data['node_id']}/balance")
            assert balance_response.status_code == 200
            
            data = balance_response.json()
            assert data["success"] is True
            assert data["balance"] == 150.75
            assert data["currency"] == "FLOP"
    
    def test_send_transaction_api(self, setup_database, sample_node_data):
        """Test transaction sending via API"""
        # Create node and wallet
        node_response = client.post("/nodes/register", json=sample_node_data)
        assert node_response.status_code == 200
        
        wallet_data = {
            "node_id": sample_node_data["node_id"],
            "wallet_name": "test_wallet"
        }
        
        with patch('duxos_registry.services.wallet_service.WalletService._make_rpc_call') as mock_rpc:
            mock_rpc.side_effect = [
                ("FLOP123456789abcdef", None),  # getnewaddress
                (200.0, None),  # getbalance
                ("txid123456789", None)  # sendtoaddress
            ]
            
            # Create wallet
            create_response = client.post("/wallet/create", json=wallet_data)
            assert create_response.status_code == 200
            
            # Send transaction
            transaction_data = {
                "node_id": sample_node_data["node_id"],
                "recipient_address": "FLOP987654321fedcba",
                "amount": 50.0
            }
            
            send_response = client.post(f"/wallet/{sample_node_data['node_id']}/send", json=transaction_data)
            assert send_response.status_code == 200
            
            data = send_response.json()
            assert data["success"] is True
            assert data["txid"] == "txid123456789"
            assert data["amount"] == 50.0
    
    def test_wallet_health_check(self):
        """Test wallet health check endpoint"""
        response = client.get("/wallet/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "wallet"
        assert data["version"] == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 