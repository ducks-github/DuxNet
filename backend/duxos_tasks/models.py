"""
Task Engine Data Models

Defines the core data structures for task management, execution, and results.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of computational tasks"""

    API_CALL = "api_call"
    BATCH_PROCESSING = "batch_processing"
    MACHINE_LEARNING = "machine_learning"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_PROCESSING = "image_processing"
    CUSTOM = "custom"


@dataclass
class Task:
    """Represents a computational task to be executed"""

    # Core identification
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    task_type: TaskType = TaskType.API_CALL

    # Execution parameters
    code: str = ""  # Code to execute or API endpoint
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_data: Optional[Dict[str, Any]] = None

    # Resource requirements
    cpu_cores: int = 1
    memory_mb: int = 512
    timeout_seconds: int = 300
    max_retries: int = 3

    # Financial
    payment_amount: float = 0.0
    escrow_id: Optional[str] = None

    # Assignment and execution
    assigned_node_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1  # 1=low, 5=high

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization"""
        return {
            "task_id": self.task_id,
            "service_name": self.service_name,
            "task_type": self.task_type.value,
            "code": self.code,
            "parameters": self.parameters,
            "input_data": self.input_data,
            "cpu_cores": self.cpu_cores,
            "memory_mb": self.memory_mb,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "payment_amount": self.payment_amount,
            "escrow_id": self.escrow_id,
            "assigned_node_id": self.assigned_node_id,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary"""
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            service_name=data.get("service_name", ""),
            task_type=TaskType(data.get("task_type", "api_call")),
            code=data.get("code", ""),
            parameters=data.get("parameters", {}),
            input_data=data.get("input_data"),
            cpu_cores=data.get("cpu_cores", 1),
            memory_mb=data.get("memory_mb", 512),
            timeout_seconds=data.get("timeout_seconds", 300),
            max_retries=data.get("max_retries", 3),
            payment_amount=data.get("payment_amount", 0.0),
            escrow_id=data.get("escrow_id"),
            assigned_node_id=data.get("assigned_node_id"),
            status=TaskStatus(data.get("status", "pending")),
            priority=data.get("priority", 1),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.utcnow()
            ),
            assigned_at=(
                datetime.fromisoformat(data["assigned_at"]) if data.get("assigned_at") else None
            ),
            started_at=(
                datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TaskResult:
    """Result of task execution"""

    task_id: str
    node_id: str
    status: TaskStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None
    memory_used_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Verification
    result_hash: Optional[str] = None
    signature: Optional[str] = None
    verified: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "task_id": self.task_id,
            "node_id": self.node_id,
            "status": self.status.value,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "execution_time_seconds": self.execution_time_seconds,
            "memory_used_mb": self.memory_used_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "result_hash": self.result_hash,
            "signature": self.signature,
            "verified": self.verified,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class NodeCapability:
    """Node capability for task execution"""

    node_id: str
    cpu_cores: int
    memory_mb: int
    storage_gb: int
    gpu_enabled: bool = False
    gpu_memory_mb: Optional[int] = None
    supported_languages: List[str] = field(default_factory=list)
    supported_services: List[str] = field(default_factory=list)

    # Performance metrics
    avg_execution_time: Optional[float] = None
    success_rate: Optional[float] = None
    reputation_score: Optional[float] = None

    def can_execute(self, task: Task) -> bool:
        """Check if node can execute the given task"""
        # Check resource requirements
        if self.cpu_cores < task.cpu_cores:
            return False
        if self.memory_mb < task.memory_mb:
            return False

        # Check service support
        if task.service_name and task.service_name not in self.supported_services:
            return False

        return True

    def get_score(self) -> float:
        """Calculate node score for task assignment"""
        score = 0.0

        # Resource availability (higher is better)
        score += (self.cpu_cores * 10) + (self.memory_mb / 100)

        # Performance metrics
        if self.success_rate:
            score += self.success_rate * 50
        if self.reputation_score:
            score += self.reputation_score * 20
        if self.avg_execution_time:
            score += max(0, 100 - self.avg_execution_time)

        return score


@dataclass
class TaskAssignment:
    """Task assignment to a specific node"""

    task_id: str
    node_id: str
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    expected_start_time: Optional[datetime] = None
    expected_completion_time: Optional[datetime] = None
    priority: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert assignment to dictionary"""
        return {
            "task_id": self.task_id,
            "node_id": self.node_id,
            "assigned_at": self.assigned_at.isoformat(),
            "expected_start_time": (
                self.expected_start_time.isoformat() if self.expected_start_time else None
            ),
            "expected_completion_time": (
                self.expected_completion_time.isoformat() if self.expected_completion_time else None
            ),
            "priority": self.priority,
        }
