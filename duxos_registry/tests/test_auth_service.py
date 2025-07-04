"""
Tests for Node Authentication Service
"""

import pytest
import time
from duxos_registry.services.auth_service import NodeAuthService, AuthLevel, NodeIdentity


class TestNodeAuthService:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auth_service = NodeAuthService()
        self.test_node_id = "test_node_123"
        self.test_message = "Hello, this is a test message"
    
    def test_generate_node_identity(self):
        """Test generating a new node identity"""
        secret_key, node_id = self.auth_service.generate_node_identity(self.test_node_id, AuthLevel.SIGNED)
        
        assert secret_key is not None
        assert len(secret_key) == 64  # 32 bytes as hex
        assert node_id == self.test_node_id
        
        # Check that identity was stored
        identity = self.auth_service.get_node_identity(self.test_node_id)
        assert identity is not None
        assert identity.node_id == self.test_node_id
        assert identity.auth_level == AuthLevel.SIGNED
        assert identity.signature_algorithm == "hmac-sha256"
    
    def test_create_and_verify_signature(self):
        """Test creating and verifying HMAC signatures"""
        # Generate identity
        secret_key, _ = self.auth_service.generate_node_identity(self.test_node_id)
        
        # Create signature
        signature = self.auth_service.create_signed_message(self.test_node_id, secret_key, self.test_message)
        assert signature is not None
        
        # Verify signature
        is_valid = self.auth_service.verify_node_signature(self.test_node_id, self.test_message, signature)
        assert is_valid is True
        
        # Test invalid signature
        invalid_signature = "invalid_signature_base64_encoded"
        is_valid = self.auth_service.verify_node_signature(self.test_node_id, self.test_message, invalid_signature)
        assert is_valid is False
    
    def test_authenticate_node(self):
        """Test node authentication"""
        # Generate identity
        secret_key, _ = self.auth_service.generate_node_identity(self.test_node_id)
        
        # Create authentication data
        auth_data = {
            "signature": self.auth_service.create_signed_message(self.test_node_id, secret_key, self.test_message),
            "timestamp": time.time(),
            "message": self.test_message
        }
        
        # Authenticate
        authenticated, auth_level = self.auth_service.authenticate_node(self.test_node_id, auth_data)
        assert authenticated is True
        assert auth_level == AuthLevel.SIGNED
    
    def test_authenticate_node_invalid_data(self):
        """Test authentication with invalid data"""
        # Test with missing data
        auth_data = {"signature": "some_signature"}  # Missing timestamp and message
        authenticated, auth_level = self.auth_service.authenticate_node(self.test_node_id, auth_data)
        assert authenticated is False
        assert auth_level == AuthLevel.NONE
        
        # Test with expired timestamp
        auth_data = {
            "signature": "some_signature",
            "timestamp": time.time() - 400,  # 400 seconds ago (expired)
            "message": self.test_message
        }
        authenticated, auth_level = self.auth_service.authenticate_node(self.test_node_id, auth_data)
        assert authenticated is False
        assert auth_level == AuthLevel.NONE
    
    def test_authorize_operation(self):
        """Test operation authorization"""
        # Generate identity with SIGNED level
        secret_key, _ = self.auth_service.generate_node_identity(self.test_node_id, AuthLevel.SIGNED)
        
        # Test authorized operations
        assert self.auth_service.authorize_operation(self.test_node_id, "register", AuthLevel.SIGNED) is True
        assert self.auth_service.authorize_operation(self.test_node_id, "update", AuthLevel.SIGNED) is True
        assert self.auth_service.authorize_operation(self.test_node_id, "query", AuthLevel.SIGNED) is True
        
        # Test unauthorized operations
        assert self.auth_service.authorize_operation(self.test_node_id, "admin", AuthLevel.SIGNED) is False
        
        # Test with insufficient auth level
        assert self.auth_service.authorize_operation(self.test_node_id, "register", AuthLevel.BASIC) is False
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Generate identity
        secret_key, _ = self.auth_service.generate_node_identity(self.test_node_id)
        
        # Make multiple failed authentication attempts
        for i in range(6):  # More than max_auth_attempts (5)
            auth_data = {
                "signature": "invalid_signature",
                "timestamp": time.time(),
                "message": self.test_message
            }
            authenticated, _ = self.auth_service.authenticate_node(self.test_node_id, auth_data)
            assert authenticated is False
        
        # Next attempt should be rate limited
        auth_data = {
            "signature": self.auth_service.create_signed_message(self.test_node_id, secret_key, self.test_message),
            "timestamp": time.time(),
            "message": self.test_message
        }
        authenticated, _ = self.auth_service.authenticate_node(self.test_node_id, auth_data)
        assert authenticated is False  # Should be rate limited
    
    def test_revoke_identity(self):
        """Test revoking node identity"""
        # Generate identity
        secret_key, _ = self.auth_service.generate_node_identity(self.test_node_id)
        
        # Verify identity exists
        identity = self.auth_service.get_node_identity(self.test_node_id)
        assert identity is not None
        
        # Revoke identity
        revoked = self.auth_service.revoke_node_identity(self.test_node_id)
        assert revoked is True
        
        # Verify identity is gone
        identity = self.auth_service.get_node_identity(self.test_node_id)
        assert identity is None
        
        # Test revoking non-existent identity
        revoked = self.auth_service.revoke_node_identity("non_existent_node")
        assert revoked is False
    
    def test_get_auth_stats(self):
        """Test getting authentication statistics"""
        # Generate identities for multiple nodes
        self.auth_service.generate_node_identity("node1", AuthLevel.BASIC)
        self.auth_service.generate_node_identity("node2", AuthLevel.SIGNED)
        self.auth_service.generate_node_identity("node3", AuthLevel.VERIFIED)
        
        stats = self.auth_service.get_auth_stats()
        
        assert stats["total_nodes"] == 3
        assert stats["auth_levels"]["basic"] == 1
        assert stats["auth_levels"]["signed"] == 1
        assert stats["auth_levels"]["verified"] == 1
        assert stats["rate_limited_nodes"] == 0
    
    def test_list_authenticated_nodes(self):
        """Test listing authenticated nodes"""
        # Generate identities
        self.auth_service.generate_node_identity("node1")
        self.auth_service.generate_node_identity("node2")
        
        nodes = self.auth_service.list_authenticated_nodes()
        
        assert len(nodes) == 2
        assert "node1" in nodes
        assert "node2" in nodes
        assert isinstance(nodes["node1"], NodeIdentity)
        assert isinstance(nodes["node2"], NodeIdentity)


if __name__ == "__main__":
    pytest.main([__file__]) 