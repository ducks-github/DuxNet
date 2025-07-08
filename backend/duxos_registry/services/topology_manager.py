"""
Topology Manager for Dux_OS Node Registry

This module implements advanced network topology management for optimizing
node communication, load balancing, and network resilience.
"""

import asyncio
import heapq
import json
import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx

# Configure logging
logger = logging.getLogger(__name__)


class TopologyType(Enum):
    """Network topology types"""

    MESH = "mesh"
    STAR = "star"
    RING = "ring"
    TREE = "tree"
    HYBRID = "hybrid"


class ConnectionQuality(Enum):
    """Connection quality levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNREACHABLE = "unreachable"


@dataclass
class NetworkSegment:
    """Network segment information"""

    segment_id: str
    name: str
    description: str
    nodes: List[str]
    gateway_nodes: List[str]
    bandwidth_capacity: float  # Mbps
    latency_threshold: float  # ms
    created_at: float
    updated_at: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkSegment":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ConnectionMetrics:
    """Connection metrics between nodes"""

    source_node: str
    target_node: str
    latency_ms: float
    bandwidth_mbps: float
    packet_loss: float
    connection_quality: ConnectionQuality
    last_measured: float
    reliability_score: float  # 0.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionMetrics":
        """Create from dictionary"""
        data["connection_quality"] = ConnectionQuality(data["connection_quality"])
        return cls(**data)


@dataclass
class RoutingPath:
    """Routing path information"""

    source: str
    destination: str
    path: List[str]
    total_latency: float
    total_bandwidth: float
    hop_count: int
    reliability: float
    created_at: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoutingPath":
        """Create from dictionary"""
        return cls(**data)


class TopologyManager:
    """Advanced network topology manager"""

    def __init__(self, registry_service=None):
        self.registry_service = registry_service

        # Network graph representation
        self.network_graph = nx.Graph()

        # Topology state
        self.segments: Dict[str, NetworkSegment] = {}
        self.connections: Dict[Tuple[str, str], ConnectionMetrics] = {}
        self.routing_cache: Dict[Tuple[str, str], RoutingPath] = {}

        # Configuration
        self.topology_type = TopologyType.HYBRID
        self.max_segment_size = 50
        self.min_connection_quality = ConnectionQuality.FAIR
        self.routing_cache_ttl = 300  # 5 minutes
        self.optimization_interval = 60  # 1 minute

        # Threading
        self.lock = threading.RLock()
        self.running = False
        self.optimization_task = None

        # Performance metrics
        self.topology_stats = {
            "total_nodes": 0,
            "total_segments": 0,
            "total_connections": 0,
            "average_latency": 0.0,
            "average_bandwidth": 0.0,
            "network_diameter": 0,
            "connectivity_score": 0.0,
        }

        logger.info("Topology Manager initialized")

    async def start(self):
        """Start topology manager"""
        if self.running:
            return

        self.running = True
        self.optimization_task = asyncio.create_task(self._optimization_loop())
        logger.info("Topology Manager started")

    async def stop(self):
        """Stop topology manager"""
        if not self.running:
            return

        self.running = False
        if self.optimization_task:
            self.optimization_task.cancel()

        logger.info("Topology Manager stopped")

    def add_node(
        self,
        node_id: str,
        capabilities: List[str] = None,
        location: Optional[Dict[str, float]] = None,
    ) -> bool:
        """Add node to topology"""
        try:
            with self.lock:
                # Add node to graph
                self.network_graph.add_node(
                    node_id,
                    capabilities=capabilities or [],
                    location=location,
                    added_at=time.time(),
                )

                # Update stats
                self.topology_stats["total_nodes"] = len(self.network_graph.nodes())

                logger.info(f"Added node {node_id} to topology")
                return True
        except Exception as e:
            logger.error(f"Error adding node {node_id}: {e}")
            return False

    def remove_node(self, node_id: str) -> bool:
        """Remove node from topology"""
        try:
            with self.lock:
                # Remove node from graph
                if node_id in self.network_graph:
                    self.network_graph.remove_node(node_id)

                    # Remove from segments
                    for segment in self.segments.values():
                        if node_id in segment.nodes:
                            segment.nodes.remove(node_id)
                        if node_id in segment.gateway_nodes:
                            segment.gateway_nodes.remove(node_id)

                    # Remove connections
                    connections_to_remove = [
                        (src, dst)
                        for (src, dst) in self.connections.keys()
                        if src == node_id or dst == node_id
                    ]
                    for conn in connections_to_remove:
                        del self.connections[conn]

                    # Clear routing cache
                    routing_keys_to_remove = [
                        (src, dst)
                        for (src, dst) in self.routing_cache.keys()
                        if src == node_id or dst == node_id
                    ]
                    for key in routing_keys_to_remove:
                        del self.routing_cache[key]

                    # Update stats
                    self.topology_stats["total_nodes"] = len(self.network_graph.nodes())

                    logger.info(f"Removed node {node_id} from topology")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error removing node {node_id}: {e}")
            return False

    def add_connection(
        self,
        source_node: str,
        target_node: str,
        latency_ms: float,
        bandwidth_mbps: float,
        packet_loss: float = 0.0,
    ) -> bool:
        """Add connection between nodes"""
        try:
            with self.lock:
                # Determine connection quality
                quality = self._calculate_connection_quality(
                    latency_ms, bandwidth_mbps, packet_loss
                )

                # Create connection metrics
                connection = ConnectionMetrics(
                    source_node=source_node,
                    target_node=target_node,
                    latency_ms=latency_ms,
                    bandwidth_mbps=bandwidth_mbps,
                    packet_loss=packet_loss,
                    connection_quality=quality,
                    last_measured=time.time(),
                    reliability_score=self._calculate_reliability_score(latency_ms, packet_loss),
                )

                # Add to connections
                self.connections[(source_node, target_node)] = connection

                # Add edge to graph
                self.network_graph.add_edge(
                    source_node,
                    target_node,
                    latency=latency_ms,
                    bandwidth=bandwidth_mbps,
                    quality=quality.value,
                    reliability=connection.reliability_score,
                )

                # Update stats
                self.topology_stats["total_connections"] = len(self.connections)
                self._update_average_metrics()

                # Clear routing cache for affected paths
                self._clear_routing_cache_for_node(source_node)
                self._clear_routing_cache_for_node(target_node)

                logger.debug(
                    f"Added connection {source_node} -> {target_node} (latency: {latency_ms}ms)"
                )
                return True
        except Exception as e:
            logger.error(f"Error adding connection {source_node} -> {target_node}: {e}")
            return False

    def remove_connection(self, source_node: str, target_node: str) -> bool:
        """Remove connection between nodes"""
        try:
            with self.lock:
                # Remove from connections
                connection_key = (source_node, target_node)
                if connection_key in self.connections:
                    del self.connections[connection_key]

                # Remove edge from graph
                if self.network_graph.has_edge(source_node, target_node):
                    self.network_graph.remove_edge(source_node, target_node)

                # Update stats
                self.topology_stats["total_connections"] = len(self.connections)
                self._update_average_metrics()

                # Clear routing cache for affected paths
                self._clear_routing_cache_for_node(source_node)
                self._clear_routing_cache_for_node(target_node)

                logger.debug(f"Removed connection {source_node} -> {target_node}")
                return True
        except Exception as e:
            logger.error(f"Error removing connection {source_node} -> {target_node}: {e}")
            return False

    def create_segment(
        self,
        segment_id: str,
        name: str,
        description: str = "",
        nodes: List[str] = None,
        gateway_nodes: List[str] = None,
        bandwidth_capacity: float = 1000.0,
        latency_threshold: float = 50.0,
    ) -> bool:
        """Create a new network segment"""
        try:
            with self.lock:
                segment = NetworkSegment(
                    segment_id=segment_id,
                    name=name,
                    description=description,
                    nodes=nodes or [],
                    gateway_nodes=gateway_nodes or [],
                    bandwidth_capacity=bandwidth_capacity,
                    latency_threshold=latency_threshold,
                    created_at=time.time(),
                    updated_at=time.time(),
                )

                self.segments[segment_id] = segment
                self.topology_stats["total_segments"] = len(self.segments)

                logger.info(f"Created network segment: {segment_id} ({name})")
                return True
        except Exception as e:
            logger.error(f"Error creating segment {segment_id}: {e}")
            return False

    def add_node_to_segment(self, segment_id: str, node_id: str, is_gateway: bool = False) -> bool:
        """Add node to network segment"""
        try:
            with self.lock:
                if segment_id not in self.segments:
                    logger.error(f"Segment {segment_id} not found")
                    return False

                segment = self.segments[segment_id]

                if node_id not in segment.nodes:
                    segment.nodes.append(node_id)

                if is_gateway and node_id not in segment.gateway_nodes:
                    segment.gateway_nodes.append(node_id)

                segment.updated_at = time.time()

                logger.debug(f"Added node {node_id} to segment {segment_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding node {node_id} to segment {segment_id}: {e}")
            return False

    def find_optimal_path(
        self, source: str, destination: str, optimize_for: str = "latency"
    ) -> Optional[RoutingPath]:
        """Find optimal path between two nodes"""
        try:
            with self.lock:
                # Check cache first
                cache_key = (source, destination)
                if cache_key in self.routing_cache:
                    cached_path = self.routing_cache[cache_key]
                    if time.time() - cached_path.created_at < self.routing_cache_ttl:
                        return cached_path

                if not self.network_graph.has_node(source) or not self.network_graph.has_node(
                    destination
                ):
                    logger.warning(
                        f"Source or destination node not found: {source} -> {destination}"
                    )
                    return None

                # Find shortest path based on optimization criteria
                if optimize_for == "latency":
                    path = nx.shortest_path(
                        self.network_graph, source, destination, weight="latency"
                    )
                elif optimize_for == "bandwidth":
                    # Use negative bandwidth as weight (higher bandwidth = lower weight)
                    path = nx.shortest_path(
                        self.network_graph,
                        source,
                        destination,
                        weight=lambda u, v, d: -d["bandwidth"],
                    )
                elif optimize_for == "reliability":
                    # Use negative reliability as weight (higher reliability = lower weight)
                    path = nx.shortest_path(
                        self.network_graph,
                        source,
                        destination,
                        weight=lambda u, v, d: -d["reliability"],
                    )
                else:
                    # Default to hop count
                    path = nx.shortest_path(self.network_graph, source, destination)

                if not path:
                    return None

                # Calculate path metrics
                total_latency = 0.0
                total_bandwidth = float("inf")
                reliability = 1.0

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    if self.network_graph.has_edge(u, v):
                        edge_data = self.network_graph[u][v]
                        total_latency += edge_data.get("latency", 0)
                        total_bandwidth = min(
                            total_bandwidth, edge_data.get("bandwidth", float("inf"))
                        )
                        reliability *= edge_data.get("reliability", 1.0)

                # Create routing path
                routing_path = RoutingPath(
                    source=source,
                    destination=destination,
                    path=path,
                    total_latency=total_latency,
                    total_bandwidth=total_bandwidth if total_bandwidth != float("inf") else 0.0,
                    hop_count=len(path) - 1,
                    reliability=reliability,
                    created_at=time.time(),
                )

                # Cache the result
                self.routing_cache[cache_key] = routing_path

                return routing_path
        except Exception as e:
            logger.error(f"Error finding path {source} -> {destination}: {e}")
            return None

    def get_network_topology(self) -> Dict[str, Any]:
        """Get complete network topology information"""
        try:
            with self.lock:
                # Calculate network metrics
                if len(self.network_graph.nodes()) > 1:
                    try:
                        diameter = nx.diameter(self.network_graph)
                    except nx.NetworkXError:
                        diameter = 0

                    connectivity_score = self._calculate_connectivity_score()
                else:
                    diameter = 0
                    connectivity_score = 0.0

                # Update stats
                self.topology_stats.update(
                    {"network_diameter": diameter, "connectivity_score": connectivity_score}
                )

                return {
                    "topology_type": self.topology_type.value,
                    "segments": {seg_id: seg.to_dict() for seg_id, seg in self.segments.items()},
                    "connections": {
                        f"{src}->{dst}": conn.to_dict()
                        for (src, dst), conn in self.connections.items()
                    },
                    "stats": self.topology_stats.copy(),
                    "graph_info": {
                        "nodes": list(self.network_graph.nodes()),
                        "edges": list(self.network_graph.edges()),
                        "node_count": len(self.network_graph.nodes()),
                        "edge_count": len(self.network_graph.edges()),
                    },
                }
        except Exception as e:
            logger.error(f"Error getting network topology: {e}")
            return {}

    def optimize_topology(self) -> Dict[str, Any]:
        """Optimize network topology"""
        try:
            with self.lock:
                optimization_results = {
                    "segments_optimized": 0,
                    "connections_optimized": 0,
                    "routing_cache_cleared": 0,
                    "performance_improvements": {},
                }

                # Optimize segments
                for segment_id, segment in self.segments.items():
                    if len(segment.nodes) > self.max_segment_size:
                        # Split large segments
                        self._split_segment(segment_id)
                        optimization_results["segments_optimized"] += 1

                # Optimize connections
                poor_connections = [
                    (src, dst)
                    for (src, dst), conn in self.connections.items()
                    if conn.connection_quality.value < self.min_connection_quality.value
                ]

                for src, dst in poor_connections:
                    # Try to find alternative routes
                    if self._find_alternative_route(src, dst):
                        self.remove_connection(src, dst)
                        optimization_results["connections_optimized"] += 1

                # Clear old routing cache
                current_time = time.time()
                old_cache_entries = [
                    key
                    for key, path in self.routing_cache.items()
                    if current_time - path.created_at > self.routing_cache_ttl
                ]
                for key in old_cache_entries:
                    del self.routing_cache[key]
                    optimization_results["routing_cache_cleared"] += 1

                # Calculate performance improvements
                old_stats = self.topology_stats.copy()
                self._update_average_metrics()

                optimization_results["performance_improvements"] = {
                    "latency_change": self.topology_stats["average_latency"]
                    - old_stats["average_latency"],
                    "bandwidth_change": self.topology_stats["average_bandwidth"]
                    - old_stats["average_bandwidth"],
                    "connectivity_change": self.topology_stats["connectivity_score"]
                    - old_stats["connectivity_score"],
                }

                logger.info(f"Topology optimization completed: {optimization_results}")
                return optimization_results
        except Exception as e:
            logger.error(f"Error optimizing topology: {e}")
            return {}

    async def _optimization_loop(self):
        """Background optimization loop"""
        while self.running:
            try:
                await asyncio.sleep(self.optimization_interval)
                if self.running:
                    self.optimize_topology()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")

    def _calculate_connection_quality(
        self, latency_ms: float, bandwidth_mbps: float, packet_loss: float
    ) -> ConnectionQuality:
        """Calculate connection quality based on metrics"""
        # Simple quality calculation (can be enhanced)
        if latency_ms < 10 and bandwidth_mbps > 100 and packet_loss < 0.01:
            return ConnectionQuality.EXCELLENT
        elif latency_ms < 50 and bandwidth_mbps > 50 and packet_loss < 0.05:
            return ConnectionQuality.GOOD
        elif latency_ms < 100 and bandwidth_mbps > 10 and packet_loss < 0.1:
            return ConnectionQuality.FAIR
        elif latency_ms < 200 and bandwidth_mbps > 1 and packet_loss < 0.2:
            return ConnectionQuality.POOR
        else:
            return ConnectionQuality.UNREACHABLE

    def _calculate_reliability_score(self, latency_ms: float, packet_loss: float) -> float:
        """Calculate reliability score (0.0 to 1.0)"""
        # Simple reliability calculation
        latency_score = max(0, 1 - (latency_ms / 1000))  # Normalize to 1 second
        loss_score = 1 - packet_loss
        return (latency_score + loss_score) / 2

    def _update_average_metrics(self):
        """Update average network metrics"""
        if not self.connections:
            self.topology_stats["average_latency"] = 0.0
            self.topology_stats["average_bandwidth"] = 0.0
            return

        total_latency = sum(conn.latency_ms for conn in self.connections.values())
        total_bandwidth = sum(conn.bandwidth_mbps for conn in self.connections.values())
        count = len(self.connections)

        self.topology_stats["average_latency"] = total_latency / count
        self.topology_stats["average_bandwidth"] = total_bandwidth / count

    def _calculate_connectivity_score(self) -> float:
        """Calculate network connectivity score (0.0 to 1.0)"""
        if len(self.network_graph.nodes()) < 2:
            return 0.0

        try:
            # Calculate various connectivity metrics
            density = nx.density(self.network_graph)
            clustering = nx.average_clustering(self.network_graph)
            connectivity = nx.node_connectivity(self.network_graph)

            # Normalize and combine
            normalized_connectivity = min(1.0, connectivity / len(self.network_graph.nodes()))

            return (density + clustering + normalized_connectivity) / 3
        except Exception:
            return 0.0

    def _clear_routing_cache_for_node(self, node_id: str):
        """Clear routing cache entries involving a specific node"""
        keys_to_remove = [
            (src, dst)
            for (src, dst) in self.routing_cache.keys()
            if src == node_id or dst == node_id
        ]
        for key in keys_to_remove:
            del self.routing_cache[key]

    def _split_segment(self, segment_id: str):
        """Split a large segment into smaller ones"""
        segment = self.segments[segment_id]
        if len(segment.nodes) <= self.max_segment_size:
            return

        # Simple splitting strategy: divide nodes into groups
        node_groups = [
            segment.nodes[i : i + self.max_segment_size]
            for i in range(0, len(segment.nodes), self.max_segment_size)
        ]

        # Create new segments
        for i, nodes in enumerate(node_groups[1:], 1):
            new_segment_id = f"{segment_id}_split_{i}"
            self.create_segment(
                segment_id=new_segment_id,
                name=f"{segment.name} (Split {i})",
                description=f"Split from {segment_id}",
                nodes=nodes,
                gateway_nodes=[n for n in nodes if n in segment.gateway_nodes],
                bandwidth_capacity=segment.bandwidth_capacity,
                latency_threshold=segment.latency_threshold,
            )

        # Update original segment
        segment.nodes = node_groups[0]
        segment.gateway_nodes = [n for n in node_groups[0] if n in segment.gateway_nodes]
        segment.updated_at = time.time()

    def _find_alternative_route(self, source: str, destination: str) -> bool:
        """Find alternative route to replace poor connection"""
        try:
            # Find all paths between source and destination
            paths = list(nx.all_simple_paths(self.network_graph, source, destination))

            # Filter out paths that use the poor connection
            good_paths = []
            for path in paths:
                uses_poor_connection = False
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    if (u, v) in self.connections:
                        conn = self.connections[(u, v)]
                        if conn.connection_quality.value < self.min_connection_quality.value:
                            uses_poor_connection = True
                            break

                if not uses_poor_connection:
                    good_paths.append(path)

            return len(good_paths) > 0
        except Exception:
            return False

    def get_node_neighbors(self, node_id: str) -> List[str]:
        """Get list of node neighbors"""
        try:
            with self.lock:
                if node_id in self.network_graph:
                    return list(self.network_graph.neighbors(node_id))
                return []
        except Exception as e:
            logger.error(f"Error getting neighbors for {node_id}: {e}")
            return []

    def get_segment_nodes(self, segment_id: str) -> List[str]:
        """Get nodes in a specific segment"""
        try:
            with self.lock:
                if segment_id in self.segments:
                    return self.segments[segment_id].nodes.copy()
                return []
        except Exception as e:
            logger.error(f"Error getting nodes for segment {segment_id}: {e}")
            return []

    def get_connection_quality(self, source: str, target: str) -> Optional[ConnectionQuality]:
        """Get connection quality between two nodes"""
        try:
            with self.lock:
                connection_key = (source, target)
                if connection_key in self.connections:
                    return self.connections[connection_key].connection_quality
                return None
        except Exception as e:
            logger.error(f"Error getting connection quality {source} -> {target}: {e}")
            return None
