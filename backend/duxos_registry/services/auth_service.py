"""
Authentication and Authorization Service for Dux_OS Node Registry

This module implements node identity verification, cryptographic signatures,
and authorization controls for secure node registration and communication.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class AuthLevel(Enum):
    """Authentication levels"""

    NONE = "none"
    BASIC = "basic"
    SIGNED = "signed"
    VERIFIED = "verified"


@dataclass
class NodeIdentity:
    """Node identity information"""

    node_id: str
    secret_key: str
    auth_level: AuthLevel
    created_at: float
    last_verified: float
    signature_algorithm: str = "hmac-sha256"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "secret_key": "***HIDDEN***",  # Don't expose secret key
            "auth_level": self.auth_level.value,
            "created_at": self.created_at,
            "last_verified": self.last_verified,
            "signature_algorithm": self.signature_algorithm,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NodeIdentity":
        """Create from dictionary"""
        return cls(
            node_id=data["node_id"],
            secret_key=data.get("secret_key", ""),
            auth_level=AuthLevel(data["auth_level"]),
            created_at=data["created_at"],
            last_verified=data["last_verified"],
            signature_algorithm=data.get("signature_algorithm", "hmac-sha256"),
        )


class NodeAuthService:
    """Node authentication and authorization service"""

    def __init__(self, master_secret: Optional[str] = None):
        self.master_secret = master_secret or secrets.token_hex(32)

        # Node identities cache
        self.node_identities: Dict[str, NodeIdentity] = {}

        # Rate limiting
        self.auth_attempts: Dict[str, list] = {}
        self.max_auth_attempts = 5
        self.auth_window = 300  # 5 minutes

        # Configuration
        self.require_signature = True
        self.signature_timeout = 300  # 5 minutes
        self.min_auth_level = AuthLevel.SIGNED

        logger.info("Node Authentication Service initialized")

    def generate_node_identity(
        self, node_id: str, auth_level: AuthLevel = AuthLevel.SIGNED
    ) -> Tuple[str, str]:
        """
        Generate a new node identity with secret key.

        Args:
            node_id: The node identifier
            auth_level: Required authentication level

        Returns:
            Tuple of (secret_key, node_id)
        """
        try:
            # Generate secret key for node
            secret_key = secrets.token_hex(32)

            # Store identity
            identity = NodeIdentity(
                node_id=node_id,
                secret_key=secret_key,
                auth_level=auth_level,
                created_at=time.time(),
                last_verified=time.time(),
                signature_algorithm="hmac-sha256",
            )

            self.node_identities[node_id] = identity

            logger.info(f"Generated identity for node {node_id}")
            return secret_key, node_id

        except Exception as e:
            logger.error(f"Error generating identity for node {node_id}: {e}")
            raise

    def verify_node_signature(self, node_id: str, message: str, signature: str) -> bool:
        """
        Verify a node's HMAC signature on a message.

        Args:
            node_id: The node identifier
            message: The message that was signed
            signature: The signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Get node identity
            identity = self.node_identities.get(node_id)
            if not identity:
                logger.warning(f"No identity found for node {node_id}")
                return False

            # Decode signature
            expected_signature = base64.b64decode(signature)

            # Create expected signature
            key = identity.secret_key.encode()
            expected_hmac = hmac.new(key, message.encode(), hashlib.sha256).digest()

            # Compare signatures
            if hmac.compare_digest(expected_signature, expected_hmac):
                # Update last verified time
                identity.last_verified = time.time()
                logger.debug(f"Signature verified for node {node_id}")
                return True
            else:
                logger.warning(f"Invalid signature for node {node_id}")
                return False

        except Exception as e:
            logger.warning(f"Signature verification failed for node {node_id}: {e}")
            return False

    def create_signed_message(self, node_id: str, secret_key: str, message: str) -> str:
        """
        Create a signed message for a node using HMAC.

        Args:
            node_id: The node identifier
            secret_key: The node's secret key
            message: The message to sign

        Returns:
            Base64 encoded signature
        """
        try:
            # Create HMAC signature
            key = secret_key.encode()
            signature = hmac.new(key, message.encode(), hashlib.sha256).digest()

            # Return base64 encoded signature
            return base64.b64encode(signature).decode()

        except Exception as e:
            logger.error(f"Error creating signature for node {node_id}: {e}")
            raise

    def authenticate_node(self, node_id: str, auth_data: Dict[str, Any]) -> Tuple[bool, AuthLevel]:
        """
        Authenticate a node based on provided authentication data.

        Args:
            node_id: The node identifier
            auth_data: Authentication data (signature, timestamp, etc.)

        Returns:
            Tuple of (authenticated, auth_level)
        """
        try:
            # Check rate limiting
            if self._is_rate_limited(node_id):
                logger.warning(f"Rate limit exceeded for node {node_id}")
                return False, AuthLevel.NONE

            # Get node identity
            identity = self.node_identities.get(node_id)
            if not identity:
                logger.warning(f"No identity found for node {node_id}")
                return False, AuthLevel.NONE

            # Check if signature is required and provided
            if self.require_signature:
                signature = auth_data.get("signature")
                timestamp = auth_data.get("timestamp")
                message = auth_data.get("message")

                if not all([signature, timestamp, message]):
                    logger.warning(f"Missing authentication data for node {node_id}")
                    return False, AuthLevel.NONE

                # Check timestamp
                if timestamp is not None and abs(time.time() - timestamp) > self.signature_timeout:
                    logger.warning(f"Signature timestamp expired for node {node_id}")
                    return False, AuthLevel.NONE

                # Verify signature
                if message is not None and signature is not None:
                    if not self.verify_node_signature(node_id, message, signature):
                        self._record_auth_attempt(node_id, False)
                        return False, AuthLevel.NONE
                else:
                    logger.warning(f"Missing message or signature for node {node_id}")
                    return False, AuthLevel.NONE

            # Record successful authentication
            self._record_auth_attempt(node_id, True)

            logger.info(f"Node {node_id} authenticated at level {identity.auth_level.value}")
            return True, identity.auth_level

        except Exception as e:
            logger.error(f"Authentication error for node {node_id}: {e}")
            return False, AuthLevel.NONE

    def authorize_operation(self, node_id: str, operation: str, auth_level: AuthLevel) -> bool:
        """
        Authorize a node to perform an operation.

        Args:
            node_id: The node identifier
            operation: The operation to authorize
            auth_level: The node's authentication level

        Returns:
            True if authorized, False otherwise
        """
        try:
            # Check minimum auth level
            if auth_level.value < self.min_auth_level.value:
                logger.warning(
                    f"Insufficient auth level for node {node_id}: {auth_level.value} < {self.min_auth_level.value}"
                )
                return False

            # Get node identity
            identity = self.node_identities.get(node_id)
            if not identity:
                logger.warning(f"No identity found for node {node_id}")
                return False

            # Check operation-specific permissions
            if operation in ["register", "update", "delete"]:
                return auth_level in [AuthLevel.SIGNED, AuthLevel.VERIFIED]
            elif operation in ["query", "list"]:
                return auth_level in [AuthLevel.BASIC, AuthLevel.SIGNED, AuthLevel.VERIFIED]
            else:
                return auth_level == AuthLevel.VERIFIED

        except Exception as e:
            logger.error(f"Authorization error for node {node_id}: {e}")
            return False

    def get_node_identity(self, node_id: str) -> Optional[NodeIdentity]:
        """Get node identity information."""
        return self.node_identities.get(node_id)

    def list_authenticated_nodes(self) -> Dict[str, NodeIdentity]:
        """Get all authenticated nodes."""
        return self.node_identities.copy()

    def revoke_node_identity(self, node_id: str) -> bool:
        """
        Revoke a node's identity.

        Args:
            node_id: The node identifier

        Returns:
            True if revoked, False if not found
        """
        if node_id in self.node_identities:
            del self.node_identities[node_id]
            logger.info(f"Revoked identity for node {node_id}")
            return True
        return False

    def _is_rate_limited(self, node_id: str) -> bool:
        """Check if node is rate limited."""
        now = time.time()
        attempts = self.auth_attempts.get(node_id, [])

        # Remove old attempts
        attempts = [t for t in attempts if now - t < self.auth_window]
        self.auth_attempts[node_id] = attempts

        return len(attempts) >= self.max_auth_attempts

    def _record_auth_attempt(self, node_id: str, successful: bool):
        """Record an authentication attempt."""
        if not successful:
            if node_id not in self.auth_attempts:
                self.auth_attempts[node_id] = []
            self.auth_attempts[node_id].append(time.time())

    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        total_nodes = len(self.node_identities)
        auth_levels = {}

        for identity in self.node_identities.values():
            level = identity.auth_level.value
            auth_levels[level] = auth_levels.get(level, 0) + 1

        return {
            "total_nodes": total_nodes,
            "auth_levels": auth_levels,
            "rate_limited_nodes": len(
                [
                    n
                    for n, attempts in self.auth_attempts.items()
                    if len(attempts) >= self.max_auth_attempts
                ]
            ),
        }
