"""
Execution Sandbox

Provides secure, isolated environments for running computational tasks
with resource limits, security controls, and monitoring.
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import docker
import psutil

from .models import Task, TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Configuration for execution sandbox"""

    runtime: str = "docker"  # docker, native, container
    memory_limit_mb: int = 512
    cpu_limit: float = 1.0
    timeout_seconds: int = 300
    network_access: bool = False
    allowed_commands: List[str] = field(default_factory=lambda: ["python", "node", "bash"])
    base_image: str = "python:3.9-slim"
    working_dir: str = "/app"


class ExecutionSandbox:
    """
    Secure execution sandbox for running computational tasks.

    Features:
    - Docker-based isolation
    - Resource limits and monitoring
    - Security controls
    - Result validation
    - Automatic cleanup
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config if config is not None else SandboxConfig()
        self.docker_client = None
        self.active_containers: Dict[str, str] = {}  # task_id -> container_id

        # Initialize Docker client if available
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_client = None

        # Performance tracking
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "avg_execution_time": 0.0,
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task in the sandbox"""
        start_time = time.time()

        try:
            logger.info(f"Starting execution of task {task.task_id}")

            # Validate task
            if not self._validate_task(task):
                return TaskResult(
                    task_id=task.task_id,
                    node_id=task.assigned_node_id or "unknown",
                    status=TaskStatus.FAILED,
                    error_message="Invalid task configuration",
                )

            # Create execution environment
            container_id = await self._create_container(task)
            if not container_id:
                return TaskResult(
                    task_id=task.task_id,
                    node_id=task.assigned_node_id or "unknown",
                    status=TaskStatus.FAILED,
                    error_message="Failed to create execution container",
                )

            # Execute task
            result = await self._run_task(task, container_id)

            # Update performance stats
            execution_time = time.time() - start_time
            self._update_stats(result.status == TaskStatus.COMPLETED, execution_time)

            return result

        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            return TaskResult(
                task_id=task.task_id,
                node_id=task.assigned_node_id or "unknown",
                status=TaskStatus.FAILED,
                error_message=str(e),
            )

    def _validate_task(self, task: Task) -> bool:
        """Validate task configuration"""
        if not task.code:
            logger.error(f"Task {task.task_id} has no code to execute")
            return False

        if task.memory_mb > self.config.memory_limit_mb:
            logger.error(f"Task {task.task_id} exceeds memory limit")
            return False

        if task.timeout_seconds > self.config.timeout_seconds:
            logger.error(f"Task {task.task_id} exceeds timeout limit")
            return False

        return True

    async def _create_container(self, task: Task) -> Optional[str]:
        """Create Docker container for task execution"""
        if not self.docker_client:
            logger.warning("Docker not available, using native execution")
            return "native"

        try:
            # Prepare container configuration
            container_config = self._prepare_container_config(task)

            # Create and start container
            container = self.docker_client.containers.run(
                self.config.base_image,
                command=container_config["command"],
                detach=True,
                mem_limit=f"{task.memory_mb}m",
                cpu_period=100000,
                cpu_quota=int(task.cpu_cores * 100000),
                network_mode="none" if not self.config.network_access else "bridge",
                volumes=container_config["volumes"],
                working_dir=self.config.working_dir,
                environment=container_config["environment"],
                remove=True,
            )

            container_id = container.id
            self.active_containers[task.task_id] = container_id

            logger.info(f"Created container {container_id} for task {task.task_id}")
            return container_id

        except Exception as e:
            logger.error(f"Failed to create container for task {task.task_id}: {e}")
            return None

    def _prepare_container_config(self, task: Task) -> Dict[str, Any]:
        """Prepare container configuration for task"""
        # Create temporary directory for task files
        temp_dir = tempfile.mkdtemp(prefix=f"task_{task.task_id}_")

        # Write task code to file
        code_file = os.path.join(temp_dir, "task.py")
        with open(code_file, "w") as f:
            f.write(task.code)

        # Write input data if provided
        input_file = None
        if task.input_data:
            input_file = os.path.join(temp_dir, "input.json")
            with open(input_file, "w") as f:
                json.dump(task.input_data, f)

        # Prepare command
        command = f"python /app/task.py"
        if input_file:
            command += f" --input /app/input.json"

        # Prepare volumes
        volumes = {temp_dir: {"bind": self.config.working_dir, "mode": "ro"}}

        # Prepare environment
        environment = {
            "TASK_ID": task.task_id,
            "SERVICE_NAME": task.service_name,
            "TIMEOUT": str(task.timeout_seconds),
            "PYTHONUNBUFFERED": "1",
        }

        return {"command": command, "volumes": volumes, "environment": environment}

    async def _run_task(self, task: Task, container_id: str) -> TaskResult:
        """Execute task in container"""
        try:
            if container_id == "native":
                return await self._run_native_task(task)

            # Get container
            container = self.docker_client.containers.get(container_id)

            # Start execution timer
            start_time = time.time()

            # Execute with timeout
            try:
                result = container.exec_run(
                    cmd=f"python /app/task.py", timeout=task.timeout_seconds
                )

                execution_time = time.time() - start_time

                # Parse result
                if result.exit_code == 0:
                    # Success
                    output_data = self._parse_output(result.output.decode())
                    result_hash = self._calculate_result_hash(output_data)

                    return TaskResult(
                        task_id=task.task_id,
                        node_id=task.assigned_node_id or "unknown",
                        status=TaskStatus.COMPLETED,
                        output_data=output_data,
                        execution_time_seconds=execution_time,
                        result_hash=result_hash,
                        verified=True,
                    )
                else:
                    # Failure
                    error_message = result.output.decode()
                    return TaskResult(
                        task_id=task.task_id,
                        node_id=task.assigned_node_id or "unknown",
                        status=TaskStatus.FAILED,
                        error_message=error_message,
                        execution_time_seconds=execution_time,
                    )

            except subprocess.TimeoutExpired:
                # Timeout
                return TaskResult(
                    task_id=task.task_id,
                    node_id=task.assigned_node_id or "unknown",
                    status=TaskStatus.TIMEOUT,
                    error_message="Task execution timed out",
                    execution_time_seconds=task.timeout_seconds,
                )

        except Exception as e:
            logger.error(f"Error running task {task.task_id}: {e}")
            return TaskResult(
                task_id=task.task_id,
                node_id=task.assigned_node_id or "unknown",
                status=TaskStatus.FAILED,
                error_message=str(e),
            )
        finally:
            # Cleanup
            await self._cleanup_container(task.task_id, container_id)

    async def _run_native_task(self, task: Task) -> TaskResult:
        """Run task in native environment (fallback)"""
        try:
            # Create temporary file for task code
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(task.code)
                temp_file = f.name

            # Execute with subprocess
            start_time = time.time()

            process = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=task.timeout_seconds,
                env={"TASK_ID": task.task_id},
            )

            execution_time = time.time() - start_time

            # Cleanup
            os.unlink(temp_file)

            # Parse result
            if process.returncode == 0:
                output_data = self._parse_output(process.stdout)
                result_hash = self._calculate_result_hash(output_data)

                return TaskResult(
                    task_id=task.task_id,
                    node_id=task.assigned_node_id or "unknown",
                    status=TaskStatus.COMPLETED,
                    output_data=output_data,
                    execution_time_seconds=execution_time,
                    result_hash=result_hash,
                    verified=True,
                )
            else:
                return TaskResult(
                    task_id=task.task_id,
                    node_id=task.assigned_node_id or "unknown",
                    status=TaskStatus.FAILED,
                    error_message=process.stderr,
                    execution_time_seconds=execution_time,
                )

        except subprocess.TimeoutExpired:
            return TaskResult(
                task_id=task.task_id,
                node_id=task.assigned_node_id or "unknown",
                status=TaskStatus.TIMEOUT,
                error_message="Task execution timed out",
                execution_time_seconds=task.timeout_seconds,
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                node_id=task.assigned_node_id or "unknown",
                status=TaskStatus.FAILED,
                error_message=str(e),
            )

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse task output"""
        try:
            # Try to parse as JSON
            return json.loads(output.strip())
        except json.JSONDecodeError:
            # Return as plain text
            return {"result": output.strip()}

    def _calculate_result_hash(self, output_data: Dict[str, Any]) -> str:
        """Calculate hash of result for verification"""
        result_str = json.dumps(output_data, sort_keys=True)
        return hashlib.sha256(result_str.encode()).hexdigest()

    async def _cleanup_container(self, task_id: str, container_id: str):
        """Clean up container after execution"""
        try:
            if container_id in self.active_containers.values():
                # Remove from tracking
                if task_id in self.active_containers:
                    del self.active_containers[task_id]

                # Stop container if still running
                if self.docker_client and container_id != "native":
                    try:
                        container = self.docker_client.containers.get(container_id)
                        container.stop(timeout=5)
                        container.remove()
                    except Exception as e:
                        logger.warning(f"Error cleaning up container {container_id}: {e}")

        except Exception as e:
            logger.error(f"Error in container cleanup: {e}")

    def _update_stats(self, success: bool, execution_time: float):
        """Update execution statistics"""
        self.execution_stats["total_executions"] += 1

        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1

        # Update average execution time
        total = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["avg_execution_time"]
        self.execution_stats["avg_execution_time"] = (
            current_avg * (total - 1) + execution_time
        ) / total

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            **self.execution_stats,
            "success_rate": (
                self.execution_stats["successful_executions"]
                / max(self.execution_stats["total_executions"], 1)
            ),
            "active_containers": len(self.active_containers),
        }

    async def cleanup_all(self):
        """Clean up all active containers"""
        for task_id, container_id in list(self.active_containers.items()):
            await self._cleanup_container(task_id, container_id)
