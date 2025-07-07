import datetime
from datetime import timedelta, UTC
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable

@dataclass
class NodeCapabilities:
    """Represents the computational capabilities of a node."""
    cpu_cores: int = 0
    memory_gb: float = 0.0
    storage_gb: float = 0.0
    gpu_enabled: bool = False
    gpu_model: Optional[str] = None

@dataclass
class NodeHealth:
    """Represents the health status of a node."""
    load_average: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    is_healthy: bool = True
    last_heartbeat: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(UTC))

    def update(self, 
               load_average: Optional[float] = None, 
               memory_usage: Optional[float] = None, 
               disk_usage: Optional[float] = None):
        """
        Update health metrics and recalculate node health status.
        
        :param load_average: System load average
        :param memory_usage: Memory usage percentage
        :param disk_usage: Disk usage percentage
        """
        if load_average is not None:
            self.load_average = load_average
        if memory_usage is not None:
            self.memory_usage = memory_usage
        if disk_usage is not None:
            self.disk_usage = disk_usage
        
        # Update last heartbeat
        self.last_heartbeat = datetime.datetime.now(UTC)
        
        # Determine overall health (customizable thresholds)
        self.is_healthy = (
            self.load_average < 2.0 and
            self.memory_usage < 90.0 and
            self.disk_usage < 90.0
        )

@dataclass
class Node:
    """Represents a node in the Dux OS network."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str = ''
    ip_address: str = ''
    port: int = 0
    public_key: Optional[str] = None
    
    # Node metadata
    hostname: str = ''
    os_version: str = ''
    duxnet_version: str = ''
    
    # Capabilities
    capabilities: NodeCapabilities = field(default_factory=NodeCapabilities)
    
    # Health tracking
    health: NodeHealth = field(default_factory=NodeHealth)
    
    # Reputation scoring
    reputation_score: float = 1.0  # Default neutral score
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    
    # Additional metadata
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def update_health(self, 
                      load_average: float, 
                      memory_usage: float, 
                      disk_usage: float) -> None:
        """Update node health metrics."""
        self.health.last_heartbeat = datetime.datetime.now(UTC)
        self.health.load_average = load_average
        self.health.memory_usage = memory_usage
        self.health.disk_usage = disk_usage
        
        # Simple health check logic
        self.health.is_healthy = (
            load_average < 2.0 and 
            memory_usage < 90.0 and 
            disk_usage < 95.0
        )
    
    def update_reputation(self, task_successful: bool) -> None:
        """
        Update node reputation based on task performance.
        
        :param task_successful: Whether the task was completed successfully
        """
        if task_successful:
            self.reputation_score = min(5.0, self.reputation_score * 1.1)
            self.total_tasks_completed += 1
        else:
            self.reputation_score = max(0.1, self.reputation_score * 0.9)
            self.total_tasks_failed += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert node to a dictionary representation.
        
        :return: Dictionary representation of the node
        """
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'ip_address': self.ip_address,
            'port': self.port,
            'hostname': self.hostname,
            'os_version': self.os_version,
            'duxnet_version': self.duxnet_version,
            'capabilities': {
                'cpu_cores': self.capabilities.cpu_cores,
                'memory_gb': self.capabilities.memory_gb,
                'storage_gb': self.capabilities.storage_gb,
                'gpu_enabled': self.capabilities.gpu_enabled,
                'gpu_model': self.capabilities.gpu_model
            },
            'health': {
                'load_average': self.health.load_average,
                'memory_usage': self.health.memory_usage,
                'disk_usage': self.health.disk_usage,
                'is_healthy': self.health.is_healthy,
                'last_heartbeat': self.health.last_heartbeat.isoformat()
            },
            'reputation_score': self.reputation_score,
            'total_tasks_completed': self.total_tasks_completed,
            'total_tasks_failed': self.total_tasks_failed,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """
        Create a Node instance from a dictionary.
        
        :param data: Dictionary representation of a node
        :return: Node instance
        """
        node = cls(
            id=data.get('id', str(uuid.uuid4())),
            wallet_address=data.get('wallet_address', ''),
            ip_address=data.get('ip_address', ''),
            port=data.get('port', 0),
            hostname=data.get('hostname', ''),
            os_version=data.get('os_version', ''),
            duxnet_version=data.get('duxnet_version', '')
        )
        
        # Set capabilities
        capabilities_data = data.get('capabilities', {})
        node.capabilities = NodeCapabilities(
            cpu_cores=capabilities_data.get('cpu_cores', 0),
            memory_gb=capabilities_data.get('memory_gb', 0.0),
            storage_gb=capabilities_data.get('storage_gb', 0.0),
            gpu_enabled=capabilities_data.get('gpu_enabled', False),
            gpu_model=capabilities_data.get('gpu_model')
        )
        
        # Set health
        health_data = data.get('health', {})
        node.health.last_heartbeat = datetime.datetime.fromisoformat(
            health_data.get('last_heartbeat', datetime.datetime.now(UTC).isoformat())
        )
        node.health.load_average = health_data.get('load_average', 0.0)
        node.health.memory_usage = health_data.get('memory_usage', 0.0)
        node.health.disk_usage = health_data.get('disk_usage', 0.0)
        node.health.is_healthy = health_data.get('is_healthy', True)
        
        # Set reputation
        node.reputation_score = data.get('reputation_score', 1.0)
        node.total_tasks_completed = data.get('total_tasks_completed', 0)
        node.total_tasks_failed = data.get('total_tasks_failed', 0)
        node.tags = data.get('tags', {})
        
        return node 