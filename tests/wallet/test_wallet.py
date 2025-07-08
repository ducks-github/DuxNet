import os
import tempfile

import pytest
import yaml

from duxos.wallet.wallet import FlopcoinWallet


@pytest.fixture
def mock_config():
    """Create a temporary configuration file for testing."""
    config_data = {
        "rpc": {"host": "127.0.0.1", "port": 32553, "user": "testuser", "password": "testpass"},
        "wallet": {"encryption": False, "backup_interval": 3600},
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as temp_config:
        yaml.safe_dump(config_data, temp_config)
        temp_config_path = temp_config.name

    yield temp_config_path

    # Clean up the temporary file
    os.unlink(temp_config_path)


def test_wallet_initialization(mock_config):
    """Test wallet initialization with a mock configuration."""
    wallet = FlopcoinWallet(config_path=mock_config)

    assert wallet.rpc_url == "http://127.0.0.1:32553"
    assert wallet.rpc_user == "testuser"
    assert wallet.rpc_password == "testpass"


def test_get_new_address(mock_config):
    """Test generating a new Flopcoin address."""
    wallet = FlopcoinWallet(config_path=mock_config)
    address = wallet.get_new_address()

    assert address is not None
    assert isinstance(address, str)
    assert address.startswith("FLOP")
    assert len(address) >= 10


def test_get_balance(mock_config):
    """Test retrieving wallet balance."""
    wallet = FlopcoinWallet(config_path=mock_config)
    balance = wallet.get_balance()

    assert balance is not None
    assert isinstance(balance, float)
    assert balance >= 0


def test_send_to_address(mock_config):
    """Test sending Flop Coin to an address."""
    wallet = FlopcoinWallet(config_path=mock_config)

    # Generate a mock recipient address
    recipient_address = wallet.get_new_address()
    assert recipient_address is not None, "Failed to generate test address"

    amount = 10.50

    txid, error = wallet.send_to_address(recipient_address, amount)

    assert txid is not None
    assert error is None
    assert isinstance(txid, str)
    assert len(txid) >= 10


def test_send_to_address_invalid_inputs(mock_config):
    """Test sending with invalid inputs."""
    wallet = FlopcoinWallet(config_path=mock_config)

    # Test empty address
    txid, error = wallet.send_to_address("", 10.50)
    assert txid is None
    assert error == "Invalid address"

    # Test negative amount
    txid, error = wallet.send_to_address("FLOP_TEST_ADDRESS", -10.50)
    assert txid is None
    assert error == "Invalid amount"


def test_config_file_not_found():
    """Test behavior when config file is not found."""
    with pytest.raises(FileNotFoundError):
        FlopcoinWallet(config_path="/path/to/nonexistent/config.yaml")


def test_config_file_invalid_yaml():
    """Test behavior with an invalid YAML configuration."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as invalid_config:
        invalid_config.write("invalid: yaml: config")
        invalid_config_path = invalid_config.name

    with pytest.raises(yaml.YAMLError):
        FlopcoinWallet(config_path=invalid_config_path)

    # Clean up
    os.unlink(invalid_config_path)
