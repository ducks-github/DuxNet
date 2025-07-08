"""
Integrated Node Registry Service

This module combines P2P communication protocol with database-backed registry
to provide real-time node discovery, registration, and management.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..db.database import get_db
from .auth_service import AuthLevel, NodeAuthService
from .database_registry import DatabaseNodeRegistryService
from .p2p_protocol import MessageType, P2PMessage, P2PProtocol

# Configure logging
logger = logging.getLogger(__name__)


class IntegratedNodeRegistry:
    """
    Integrated Node Registry that combines P2P discovery with database persistence.

    Features:
    - Real-time node discovery via P2P protocol
    - Persistent storage in database
    - Automatic node registration from P2P messages
    - Health monitoring integration
    - Reputation tracking
    - Node authentication and authorization
    """

    def __init__(
        self,
        node_id: str,
        db_session: Session,
        p2p_listen_port: int = 9334,
        p2p_broadcast_port: int = 9335,
    ):
        self.node_id = node_id
        self.db_session = db_session

        # Core services
        self.db_registry = DatabaseNodeRegistryService(db_session)
        self.p2p_protocol = P2PProtocol(node_id, p2p_listen_port, p2p_broadcast_port)
        self.auth_service = NodeAuthService()

        # State tracking
        self.running = False
        self.sync_task = None

        # Configuration
        self.auto_register_p2p_nodes = True
        self.require_authentication = True
        self.sync_interval = 30  # seconds
        self.health_broadcast_interval = 60  # seconds

        logger.info(f"Integrated Node Registry initialized for node {node_id}")

    async def start(self):
        """Start the integrated registry service"""
        if self.running:
            return

        self.running = True

        # Start P2P protocol
        await self.p2p_protocol.start()

        # Register P2P message handlers
        self._register_p2p_handlers()

        # Start background tasks
        self.sync_task = asyncio.create_task(self._sync_p2p_to_database())
        asyncio.create_task(self._broadcast_health_status())
        asyncio.create_task(self._cleanup_expired_nodes())

        logger.info("Integrated Node Registry started")

    async def stop(self):
        """Stop the integrated registry service"""
        if not self.running:
            return

        self.running = False

        # Stop background tasks
        if self.sync_task:
            self.sync_task.cancel()

        # Stop P2P protocol
        await self.p2p_protocol.stop()

        logger.info("Integrated Node Registry stopped")

    def _register_p2p_handlers(self):
        """Register P2P message handlers that integrate with database"""
        # Note: P2P protocol uses direct method calls, not handler registration
        # The handlers will be called from the P2P protocol's _handle_message method
        logger.info("P2P message handlers will be called from protocol")

    async def _handle_p2p_hello(self, message: P2PMessage, addr):
        """Handle P2P hello message and register node in database"""
        try:
            node_id = message.sender_id
            node_address = f"{addr[0]}:{addr[1]}"
            capabilities = message.payload.get("capabilities", [])
            reputation = message.payload.get("reputation", 0.0)
            health_status = message.payload.get("health_status", "unknown")

            # Authenticate node if required
            if self.require_authentication:
                auth_data = message.payload.get("auth_data", {})
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)

                if not authenticated:
                    logger.warning(f"Authentication failed for node {node_id}")
                    return

            # Check if node exists in database
            existing_node = self.db_registry.get_node(node_id)

            if existing_node:
                # Update existing node
                logger.debug(f"Updating existing node {node_id} from P2P hello")
                # Update node status and last seen
                self.db_registry.update_node_status(node_id, health_status)
                self.db_registry.update_node_heartbeat(node_id)
            else:
                # Register new node
                if self.auto_register_p2p_nodes:
                    logger.info(f"Auto-registering new node {node_id} from P2P hello")

                    # Generate identity for new node if not authenticated
                    if self.require_authentication and not self.auth_service.get_node_identity(
                        node_id
                    ):
                        secret_key, _ = self.auth_service.generate_node_identity(
                            node_id, AuthLevel.SIGNED
                        )
                        logger.info(f"Generated identity for new node {node_id}")

                    result = self.db_registry.register_node(
                        node_id=node_id,
                        address=node_address,
                        capabilities=capabilities,
                        metadata={
                            "discovered_via": "p2p",
                            "discovery_time": time.time(),
                            "reputation": reputation,
                            "auth_level": (
                                auth_level.value if self.require_authentication else "none"
                            ),
                        },
                    )

                    if not result["success"]:
                        logger.warning(f"Failed to register node {node_id}: {result['message']}")

            # Also update P2P protocol's known nodes
            await self.p2p_protocol._handle_hello(message, addr)

        except Exception as e:
            logger.error(f"Error handling P2P hello for {message.sender_id}: {e}")

    async def _handle_p2p_goodbye(self, message: P2PMessage, addr):
        """Handle P2P goodbye message"""
        try:
            node_id = message.sender_id

            # Update node status to offline
            self.db_registry.update_node_status(node_id, "offline")

            # Also handle in P2P protocol
            await self.p2p_protocol._handle_goodbye(message, addr)

        except Exception as e:
            logger.error(f"Error handling P2P goodbye for {message.sender_id}: {e}")

    async def _handle_p2p_health(self, message: P2PMessage, addr):
        """Handle P2P health broadcast message"""
        try:
            node_id = message.sender_id
            health_data = message.payload

            # Update node heartbeat
            self.db_registry.update_node_heartbeat(node_id)

            # Also handle in P2P protocol
            await self.p2p_protocol._handle_health_broadcast(message, addr)

        except Exception as e:
            logger.error(f"Error handling P2P health for {message.sender_id}: {e}")

    async def _handle_p2p_node_register(self, message: P2PMessage, addr):
        """Handle P2P node registration message"""
        try:
            node_data = message.payload
            node_id = node_data.get("node_id")
            address = node_data.get("address")
            capabilities = node_data.get("capabilities", [])
            metadata = node_data.get("metadata", {})

            # Authenticate node if required
            if self.require_authentication and node_id:
                auth_data = node_data.get("auth_data", {})
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)

                if not authenticated:
                    logger.warning(f"Authentication failed for node registration {node_id}")
                    return

            if node_id and address:
                logger.info(f"Registering node {node_id} via P2P")
                result = self.db_registry.register_node(
                    node_id=node_id, address=address, capabilities=capabilities, metadata=metadata
                )

                if result["success"]:
                    # Broadcast success to P2P network
                    await self.p2p_protocol.broadcast_message(
                        MessageType.NODE_UPDATE,
                        {"node_id": node_id, "status": "registered", "capabilities": capabilities},
                    )
                else:
                    logger.warning(f"Failed to register node {node_id}: {result['message']}")

        except Exception as e:
            logger.error(f"Error handling P2P node register: {e}")

    async def _handle_p2p_node_update(self, message: P2PMessage, addr):
        """Handle P2P node update message"""
        try:
            node_data = message.payload
            node_id = node_data.get("node_id")

            if node_id:
                # Update node in database
                if "status" in node_data:
                    self.db_registry.update_node_status(node_id, node_data["status"])

                if "reputation" in node_data:
                    # Calculate delta for reputation update
                    current_node = self.db_registry.get_node(node_id)
                    if current_node:
                        current_reputation = current_node.get("reputation", 0.0)
                        new_reputation = node_data["reputation"]
                        delta = new_reputation - current_reputation
                        self.db_registry.update_node_reputation(node_id, delta)

        except Exception as e:
            logger.error(f"Error handling P2P node update: {e}")

    async def _sync_p2p_to_database(self):
        """Sync P2P discovered nodes to database"""
        while self.running:
            try:
                # Get P2P nodes
                p2p_nodes = self.p2p_protocol.get_known_nodes()

                # Sync to database
                for p2p_node in p2p_nodes:
                    node_id = p2p_node.node_id
                    existing_node = self.db_registry.get_node(node_id)

                    if not existing_node and self.auto_register_p2p_nodes:
                        # Register new node from P2P
                        result = self.db_registry.register_node(
                            node_id=node_id,
                            address=p2p_node.address,
                            capabilities=p2p_node.capabilities,
                            metadata={
                                "discovered_via": "p2p_sync",
                                "discovery_time": time.time(),
                                "reputation": p2p_node.reputation,
                                "health_status": p2p_node.health_status,
                            },
                        )

                        if result["success"]:
                            logger.debug(f"Synced P2P node {node_id} to database")

                await asyncio.sleep(self.sync_interval)

            except Exception as e:
                logger.error(f"Error in P2P sync: {e}")
                await asyncio.sleep(self.sync_interval)

    async def _broadcast_health_status(self):
        """Broadcast health status to P2P network"""
        while self.running:
            try:
                # Get current node health
                current_node = self.db_registry.get_node(self.node_id)
                if current_node:
                    health_data = {
                        "node_id": self.node_id,
                        "status": current_node.get("status", "unknown"),
                        "reputation": current_node.get("reputation", 0.0),
                        "capabilities": current_node.get("capabilities", []),
                        "timestamp": time.time(),
                    }

                    # Add authentication if required
                    if self.require_authentication:
                        identity = self.auth_service.get_node_identity(self.node_id)
                        if identity:
                            message = json.dumps(health_data)
                            signature = self.auth_service.create_signed_message(
                                self.node_id, identity.secret_key, message
                            )
                            health_data["auth_data"] = {
                                "signature": signature,
                                "timestamp": time.time(),
                                "message": message,
                            }

                    await self.p2p_protocol.broadcast_message(
                        MessageType.HEALTH_BROADCAST, health_data
                    )

                await asyncio.sleep(self.health_broadcast_interval)

            except Exception as e:
                logger.error(f"Error broadcasting health: {e}")
                await asyncio.sleep(self.health_broadcast_interval)

    async def _cleanup_expired_nodes(self):
        """Clean up expired nodes from database"""
        while self.running:
            try:
                # Get all nodes
                all_nodes = self.db_registry.get_all_nodes(active_only=False)

                current_time = time.time()
                for node in all_nodes:
                    # Check if node hasn't been seen for too long
                    last_heartbeat = node.get("last_heartbeat")
                    if last_heartbeat:
                        # Parse ISO timestamp
                        try:
                            import datetime

                            last_seen = datetime.datetime.fromisoformat(
                                last_heartbeat.replace("Z", "+00:00")
                            )
                            last_seen_timestamp = last_seen.timestamp()

                            # If node hasn't been seen for 1 hour, mark as offline
                            if current_time - last_seen_timestamp > 3600:
                                self.db_registry.update_node_status(node["node_id"], "offline")
                                logger.info(
                                    f"Marked node {node['node_id']} as offline due to inactivity"
                                )
                        except Exception as e:
                            logger.warning(
                                f"Error parsing heartbeat for node {node['node_id']}: {e}"
                            )

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
                await asyncio.sleep(300)

    # Public API methods that combine P2P and database functionality

    def register_node(
        self,
        node_id: str,
        address: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        auth_data: Optional[Dict] = None,
    ) -> Dict:
        """Register a node in both database and P2P network"""
        try:
            # Authenticate if required
            if self.require_authentication and auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}

                # Check authorization
                if not self.auth_service.authorize_operation(node_id, "register", auth_level):
                    return {"success": False, "message": "Insufficient permissions"}

            # Register in database
            result = self.db_registry.register_node(node_id, address, capabilities, metadata)

            if result["success"]:
                # Generate identity if not exists
                if self.require_authentication and not self.auth_service.get_node_identity(node_id):
                    secret_key, _ = self.auth_service.generate_node_identity(
                        node_id, AuthLevel.SIGNED
                    )
                    logger.info(f"Generated identity for registered node {node_id}")

                # Broadcast registration to P2P network
                p2p_data = {
                    "node_id": node_id,
                    "address": address,
                    "capabilities": capabilities or [],
                    "metadata": metadata or {},
                }

                # Add authentication data
                if self.require_authentication:
                    identity = self.auth_service.get_node_identity(node_id)
                    if identity:
                        message = json.dumps(p2p_data)
                        signature = self.auth_service.create_signed_message(
                            node_id, identity.secret_key, message
                        )
                        p2p_data["auth_data"] = {
                            "signature": signature,
                            "timestamp": time.time(),
                            "message": message,
                        }

                asyncio.create_task(
                    self.p2p_protocol.broadcast_message(MessageType.NODE_REGISTER, p2p_data)
                )

                logger.info(f"Registered node {node_id} in integrated registry")

            return result

        except Exception as e:
            logger.error(f"Error registering node {node_id}: {e}")
            return {"success": False, "message": f"Error registering node: {str(e)}"}

    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get node information from database"""
        return self.db_registry.get_node(node_id)

    def get_all_nodes(self, active_only: bool = True) -> List[Dict]:
        """Get all nodes from database"""
        return self.db_registry.get_all_nodes(active_only)

    def get_p2p_nodes(self) -> List[Any]:
        """Get nodes discovered via P2P"""
        return self.p2p_protocol.get_known_nodes()

    def update_node_status(
        self, node_id: str, status: str, auth_data: Optional[Dict] = None
    ) -> Dict:
        """Update node status in database and broadcast via P2P"""
        try:
            # Authenticate if required
            if self.require_authentication and auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}

                # Check authorization
                if not self.auth_service.authorize_operation(node_id, "update", auth_level):
                    return {"success": False, "message": "Insufficient permissions"}

            # Update in database
            result = self.db_registry.update_node_status(node_id, status)

            if result["success"]:
                # Broadcast update to P2P network
                p2p_data = {"node_id": node_id, "status": status, "timestamp": time.time()}

                # Add authentication data
                if self.require_authentication:
                    identity = self.auth_service.get_node_identity(node_id)
                    if identity:
                        message = json.dumps(p2p_data)
                        signature = self.auth_service.create_signed_message(
                            node_id, identity.secret_key, message
                        )
                        p2p_data["auth_data"] = {
                            "signature": signature,
                            "timestamp": time.time(),
                            "message": message,
                        }

                asyncio.create_task(
                    self.p2p_protocol.broadcast_message(MessageType.NODE_UPDATE, p2p_data)
                )

            return result

        except Exception as e:
            logger.error(f"Error updating node status {node_id}: {e}")
            return {"success": False, "message": f"Error updating status: {str(e)}"}

    def update_node_reputation(
        self, node_id: str, delta: float, auth_data: Optional[Dict] = None
    ) -> Dict:
        """Update node reputation in database and broadcast via P2P"""
        try:
            # Authenticate if required
            if self.require_authentication and auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}

                # Check authorization
                if not self.auth_service.authorize_operation(node_id, "update", auth_level):
                    return {"success": False, "message": "Insufficient permissions"}

            # Update in database
            result = self.db_registry.update_node_reputation(node_id, delta)

            if result["success"]:
                # Broadcast update to P2P network
                p2p_data = {
                    "node_id": node_id,
                    "reputation": result["new_reputation"],
                    "timestamp": time.time(),
                }

                # Add authentication data
                if self.require_authentication:
                    identity = self.auth_service.get_node_identity(node_id)
                    if identity:
                        message = json.dumps(p2p_data)
                        signature = self.auth_service.create_signed_message(
                            node_id, identity.secret_key, message
                        )
                        p2p_data["auth_data"] = {
                            "signature": signature,
                            "timestamp": time.time(),
                            "message": message,
                        }

                asyncio.create_task(
                    self.p2p_protocol.broadcast_message(MessageType.NODE_UPDATE, p2p_data)
                )

            return result

        except Exception as e:
            logger.error(f"Error updating node reputation {node_id}: {e}")
            return {"success": False, "message": f"Error updating reputation: {str(e)}"}

    # Authentication methods

    def generate_node_identity(
        self, node_id: str, auth_level: AuthLevel = AuthLevel.SIGNED
    ) -> Tuple[str, str]:
        """Generate a new node identity"""
        return self.auth_service.generate_node_identity(node_id, auth_level)

    def get_node_identity(self, node_id: str) -> Optional[Any]:
        """Get node identity information"""
        return self.auth_service.get_node_identity(node_id)

    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return self.auth_service.get_auth_stats()

    def revoke_node_identity(self, node_id: str) -> bool:
        """Revoke a node's identity"""
        return self.auth_service.revoke_node_identity(node_id)
