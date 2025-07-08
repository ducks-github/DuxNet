"""
DuxOS Task Engine

A distributed task execution system that coordinates computational tasks
across the DuxOS network with secure sandboxing and automatic payments.
"""

from .api import TaskEngineAPI
from .execution_sandbox import ExecutionSandbox
from .models import Task, TaskResult, TaskStatus, TaskType
from .result_verifier import ResultVerifier
from .task_engine import TaskEngine
from .task_scheduler import TaskScheduler

__version__ = "1.0.0"
__all__ = [
    "TaskEngine",
    "TaskScheduler",
    "ExecutionSandbox",
    "ResultVerifier",
    "Task",
    "TaskResult",
    "TaskStatus",
    "TaskType",
    "TaskEngineAPI",
]
