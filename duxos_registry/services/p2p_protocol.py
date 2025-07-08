"""
P2P Communication Protocol for Dux_OS Node Registry

This module implements a peer-to-peer communication protocol
for decentralized node discovery and health monitoring.
"""

import asyncio
import hashlib
import json
import logging
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """P2P message types"""

    PING = "ping"
    PONG = "pong"
    HELLO = "hello"
    GOODBYE = "goodbye"
    NODE_REGISTER = "node_register"
    NODE_UPDATE = "node_update"
    HEALTH_BROADCAST = "health_broadcast"


@dataclass
class P2PMessage:
    """P2P message structure"""

    message_type: MessageType
    sender_id: str
    sender_address: str
    timestamp: float
    message_id: str
    payload: Dict[str, Any]

    def __post_init__(self):
        if not hasattr(self, "payload") or self.payload is None:
            self.payload = {}
        if not self.message_id:
            self.message_id = self._generate_message_id()

    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        data = f"{self.sender_id}:{self.timestamp}:{secrets.token_hex(8)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "sender_address": self.sender_address,
            "timestamp": self.timestamp,
            "message_id": self.message_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "P2PMessage":
        """Create from dictionary"""
        return cls(
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            sender_address=data["sender_address"],
            timestamp=data["timestamp"],
            message_id=data["message_id"],
            payload=data.get("payload", {}),
        )


@dataclass
class NodeInfo:
    """Node information for P2P communication"""

    node_id: str
    address: str
    port: int
    capabilities: List[str]
    reputation: float
    health_status: str
    last_seen: float


class P2PProtocol:
    """P2P communication protocol implementation"""

    def __init__(self, node_id: str, listen_port: int = 9334, broadcast_port: int = 9335):
        self.node_id = node_id
        self.listen_port = listen_port
        self.broadcast_port = broadcast_port

        # Network state
        self.known_nodes: Dict[str, NodeInfo] = {}
        self.message_history: Set[str] = set()
        self.running = False

        # Communication socket
        self.udp_socket = None

        # Threading
        self.lock = threading.RLock()

        logger.info(f"P2P Protocol initialized for node {node_id}")

    async def start(self):
        """Start P2P protocol"""
        if self.running:
            return

        self.running = True

        # Create UDP socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.bind(("0.0.0.0", self.listen_port))
        self.udp_socket.settimeout(1.0)

        # Start background tasks
        asyncio.create_task(self._listen_udp())
        asyncio.create_task(self._cleanup_old_messages())
        asyncio.create_task(self._broadcast_presence())

        logger.info(f"P2P Protocol started on port {self.listen_port}")

    async def stop(self):
        """Stop P2P protocol"""
        if not self.running:
            return

        self.running = False

        # Send goodbye message
        await self.broadcast_message(
            MessageType.GOODBYE, {"node_id": self.node_id, "reason": "shutdown"}
        )

        # Close socket
        if self.udp_socket:
            self.udp_socket.close()

        logger.info("P2P Protocol stopped")

    async def broadcast_message(
        self, message_type: MessageType, payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """Broadcast message to all nodes"""
        if not self.running:
            return

        message = P2PMessage(
            message_type=message_type,
            sender_id=self.node_id,
            sender_address=f"0.0.0.0:{self.listen_port}",
            timestamp=time.time(),
            message_id="",
            payload=payload if payload is not None else {},
        )

        try:
            data = json.dumps(message.to_dict()).encode()
            if self.udp_socket:
                self.udp_socket.sendto(data, ("<broadcast>", self.broadcast_port))
            logger.debug(f"Broadcasted {message_type.value} message")
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")

    async def _listen_udp(self):
        """Listen for UDP messages"""
        while self.running:
            try:
                if self.udp_socket:
                    data, addr = self.udp_socket.recvfrom(4096)
                    await self._process_message(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error in UDP listener: {e}")

    async def _process_message(self, data: bytes, addr: Tuple[str, int]):
        """Process incoming message"""
        try:
            message_dict = json.loads(data.decode())
            message = P2PMessage.from_dict(message_dict)

            # Check for message loops
            if message.message_id in self.message_history:
                return

            # Add to history
            self.message_history.add(message.message_id)

            # Handle message
            await self._handle_message(message, addr)

        except Exception as e:
            logger.error(f"Error processing message from {addr}: {e}")

    async def _handle_message(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle incoming message"""
        if message.message_type == MessageType.HELLO:
            await self._handle_hello(message, addr)
        elif message.message_type == MessageType.GOODBYE:
            await self._handle_goodbye(message, addr)
        elif message.message_type == MessageType.HEALTH_BROADCAST:
            await self._handle_health_broadcast(message, addr)
        elif message.message_type == MessageType.PING:
            await self._handle_ping(message, addr)
        elif message.message_type == MessageType.PONG:
            await self._handle_pong(message, addr)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")

    async def _handle_hello(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle hello message"""
        node_info = NodeInfo(
            node_id=message.sender_id,
            address=f"{addr[0]}:{addr[1]}",
            port=addr[1],
            capabilities=message.payload.get("capabilities", []),
            reputation=message.payload.get("reputation", 0.0),
            health_status=message.payload.get("health_status", "unknown"),
            last_seen=time.time(),
        )

        with self.lock:
            self.known_nodes[message.sender_id] = node_info

        logger.info(f"New node discovered: {message.sender_id} at {addr[0]}:{addr[1]}")

    async def _handle_goodbye(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle goodbye message"""
        with self.lock:
            if message.sender_id in self.known_nodes:
                del self.known_nodes[message.sender_id]
                logger.info(f"Node left network: {message.sender_id}")

    async def _handle_health_broadcast(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle health broadcast"""
        node_id = message.sender_id
        health_data = message.payload

        with self.lock:
            if node_id in self.known_nodes:
                node_info = self.known_nodes[node_id]
                node_info.health_status = health_data.get("status", "unknown")
                node_info.last_seen = time.time()

    async def _handle_ping(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle ping message"""
        response = P2PMessage(
            message_type=MessageType.PONG,
            sender_id=self.node_id,
            sender_address=f"0.0.0.0:{self.listen_port}",
            timestamp=time.time(),
            message_id="",
            payload={"original_ping_id": message.message_id},
        )

        target_address = f"{addr[0]}:{addr[1]}"
        await self.send_message(target_address, MessageType.PONG, response.payload)

    async def _handle_pong(self, message: P2PMessage, addr: Tuple[str, int]):
        """Handle pong message"""
        # Could implement latency tracking here
        logger.debug(f"Received pong from {message.sender_id}")

    async def send_message(
        self,
        target_address: str,
        message_type: MessageType,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send message to specific node"""
        if not self.running:
            return False

        message = P2PMessage(
            message_type=message_type,
            sender_id=self.node_id,
            sender_address=f"0.0.0.0:{self.listen_port}",
            timestamp=time.time(),
            message_id="",
            payload=payload if payload is not None else {},
        )

        try:
            data = json.dumps(message.to_dict()).encode()
            host, port = target_address.split(":")
            if self.udp_socket:
                self.udp_socket.sendto(data, (host, int(port)))
            logger.debug(f"Sent {message_type.value} to {target_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to {target_address}: {e}")
            return False

    async def _cleanup_old_messages(self):
        """Clean up old messages from history"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Cleanup every minute

                with self.lock:
                    # Remove old messages from history
                    self.message_history.clear()

                    # Remove old nodes (not seen for 5 minutes)
                    current_time = time.time()
                    expired_nodes = [
                        node_id
                        for node_id, node_info in self.known_nodes.items()
                        if current_time - node_info.last_seen > 300
                    ]
                    for node_id in expired_nodes:
                        del self.known_nodes[node_id]
                        logger.info(f"Removed expired node: {node_id}")
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _broadcast_presence(self):
        """Periodically broadcast node presence"""
        while self.running:
            try:
                await self.broadcast_message(
                    MessageType.HELLO,
                    {
                        "node_id": self.node_id,
                        "capabilities": [],
                        "reputation": 0.0,
                        "health_status": "unknown",
                    },
                )
                await asyncio.sleep(30)  # Broadcast every 30 seconds
            except Exception as e:
                logger.error(f"Error broadcasting presence: {e}")

    def get_known_nodes(self) -> List[NodeInfo]:
        """Get list of known nodes"""
        with self.lock:
            return list(self.known_nodes.values())

    def get_node_info(self, node_id: str) -> Optional[NodeInfo]:
        """Get specific node information"""
        with self.lock:
            return self.known_nodes.get(node_id)

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        with self.lock:
            total_nodes = len(self.known_nodes)
            healthy_nodes = len(
                [n for n in self.known_nodes.values() if n.health_status == "healthy"]
            )
            avg_reputation = (
                sum(n.reputation for n in self.known_nodes.values()) / total_nodes
                if total_nodes > 0
                else 0
            )

            return {
                "total_nodes": total_nodes,
                "healthy_nodes": healthy_nodes,
                "unhealthy_nodes": total_nodes - healthy_nodes,
                "average_reputation": avg_reputation,
                "message_history_size": len(self.message_history),
            }
