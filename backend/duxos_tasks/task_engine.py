#!/usr/bin/env python3
"""
Task Engine for DuxNet
Manages distributed computing tasks and execution
"""

import logging
import os
import uuid
import json
import docker
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import sqlite3
from dataclasses import dataclass, asdict
import subprocess
import tempfile
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Task:
    """Task data structure"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    priority: TaskPriority
    max_execution_time: int  # seconds
    required_capabilities: List[str]
    reward: Decimal
    currency: str
    submitter_id: str
    assigned_node_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class NodeCapability:
    """Node capability information"""
    node_id: str
    capability: str
    performance_score: float
    availability: float
    last_heartbeat: datetime
    is_active: bool = True


class TaskEngine:
    """Main task engine for managing distributed computing tasks"""
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.docker_client = None
        self._init_database()
        self._init_docker()
    
    def _init_database(self):
        """Initialize the task database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tasks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        max_execution_time INTEGER NOT NULL,
                        required_capabilities TEXT NOT NULL,
                        reward TEXT NOT NULL,
                        currency TEXT NOT NULL,
                        submitter_id TEXT NOT NULL,
                        assigned_node_id TEXT,
                        status TEXT NOT NULL,
                        result TEXT,
                        error_message TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Create node capabilities table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS node_capabilities (
                        node_id TEXT NOT NULL,
                        capability TEXT NOT NULL,
                        performance_score REAL NOT NULL,
                        availability REAL NOT NULL,
                        last_heartbeat TEXT NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        PRIMARY KEY (node_id, capability)
                    )
                """)
                
                # Create task results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_results (
                        result_id TEXT PRIMARY KEY,
                        task_id TEXT NOT NULL,
                        node_id TEXT NOT NULL,
                        result_data TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        resource_usage TEXT,
                        verification_status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                """)
                
                conn.commit()
                logger.info("Task database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize task database: {e}")
            raise
    
    def _init_docker(self):
        """Initialize Docker client for task execution"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: TaskPriority,
        max_execution_time: int,
        required_capabilities: List[str],
        reward: Decimal,
        currency: str,
        submitter_id: str
    ) -> Task:
        """Submit a new task for execution"""
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id,
                task_type=task_type,
                payload=payload,
                priority=priority,
                max_execution_time=max_execution_time,
                required_capabilities=required_capabilities,
                reward=reward,
                currency=currency,
                submitter_id=submitter_id
            )
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (
                        task_id, task_type, payload, priority, max_execution_time,
                        required_capabilities, reward, currency, submitter_id, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.task_id,
                    task.task_type,
                    json.dumps(task.payload),
                    task.priority.value,
                    task.max_execution_time,
                    json.dumps(task.required_capabilities),
                    str(task.reward),
                    task.currency,
                    task.submitter_id,
                    task.status.value,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat()
                ))
                conn.commit()
            
            logger.info(f"Submitted task {task_id} with reward {reward} {currency}")
            return task

        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise

    def get_available_tasks(self, node_capabilities: List[str]) -> List[Task]:
        """Get available tasks for a node with given capabilities"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT task_id, task_type, payload, priority, max_execution_time,
                           required_capabilities, reward, currency, submitter_id, assigned_node_id,
                           status, result, error_message, started_at, completed_at, created_at, updated_at
                    FROM tasks 
                    WHERE status = 'pending'
                    ORDER BY 
                        CASE priority
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'normal' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        created_at ASC
                """)
                
                results = cursor.fetchall()
                available_tasks = []
                
                for result in results:
                    required_caps = json.loads(result[5])
                    
                    # Check if node has all required capabilities
                    if all(cap in node_capabilities for cap in required_caps):
                        task = Task(
                            task_id=result[0],
                            task_type=result[1],
                            payload=json.loads(result[2]),
                            priority=TaskPriority(result[3]),
                            max_execution_time=result[4],
                            required_capabilities=required_caps,
                            reward=Decimal(result[6]),
                            currency=result[7],
                            submitter_id=result[8],
                            assigned_node_id=result[9],
                            status=TaskStatus(result[10]),
                            result=json.loads(result[11]) if result[11] else None,
                            error_message=result[12],
                            started_at=datetime.fromisoformat(result[13]) if result[13] else None,
                            completed_at=datetime.fromisoformat(result[14]) if result[14] else None,
                            created_at=datetime.fromisoformat(result[15]),
                            updated_at=datetime.fromisoformat(result[16])
                        )
                        available_tasks.append(task)
                
                return available_tasks
                
        except Exception as e:
            logger.error(f"Failed to get available tasks: {e}")
            return []
    
    def assign_task(self, task_id: str, node_id: str) -> bool:
        """Assign a task to a specific node"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET assigned_node_id = ?, status = ?, updated_at = ?
                    WHERE task_id = ? AND status = 'pending'
                """, (
                    node_id,
                    TaskStatus.ASSIGNED.value,
                    datetime.utcnow().isoformat(),
                    task_id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Assigned task {task_id} to node {node_id}")
                    return True
                else:
                    logger.warning(f"Failed to assign task {task_id} - not available")
                    return False

        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {e}")
            return False

    def start_task(self, task_id: str, node_id: str) -> bool:
        """Start execution of a task"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, started_at = ?, updated_at = ?
                    WHERE task_id = ? AND assigned_node_id = ?
                """, (
                    TaskStatus.RUNNING.value,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    task_id,
                    node_id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Started task {task_id} on node {node_id}")
                    return True
                else:
                    logger.warning(f"Failed to start task {task_id} - not assigned to node {node_id}")
                    return False
                    
            except Exception as e:
            logger.error(f"Failed to start task {task_id}: {e}")
            return False
    
    def complete_task(self, task_id: str, node_id: str, result: Dict[str, Any], execution_time: float) -> bool:
        """Complete a task with results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

            # Update task status
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, result = ?, completed_at = ?, updated_at = ?
                    WHERE task_id = ? AND assigned_node_id = ?
                """, (
                    TaskStatus.COMPLETED.value,
                    json.dumps(result),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    task_id,
                    node_id
                ))
                
                if cursor.rowcount > 0:
                    # Record task result
                    result_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO task_results (
                            result_id, task_id, node_id, result_data, execution_time,
                            verification_status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result_id,
                        task_id,
                        node_id,
                        json.dumps(result),
                        execution_time,
                        "pending",
                        datetime.utcnow().isoformat()
                    ))
                    
                    conn.commit()
                    logger.info(f"Completed task {task_id} on node {node_id}")
                    return True
                else:
                    logger.warning(f"Failed to complete task {task_id} - not assigned to node {node_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return False
    
    def fail_task(self, task_id: str, node_id: str, error_message: str) -> bool:
        """Mark a task as failed"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks 
                    SET status = ?, error_message = ?, completed_at = ?, updated_at = ?
                    WHERE task_id = ? AND assigned_node_id = ?
                """, (
                    TaskStatus.FAILED.value,
                    error_message,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    task_id,
                    node_id
                ))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Failed task {task_id} on node {node_id}: {error_message}")
                    return True
                else:
                    logger.warning(f"Failed to mark task {task_id} as failed - not assigned to node {node_id}")
                    return False

        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {e}")
            return False
    
    def execute_task_in_sandbox(self, task: Task) -> Tuple[bool, Dict[str, Any], float]:
        """Execute a task in a secure sandbox environment"""
        if not self.docker_client:
            logger.error("Docker client not available for sandbox execution")
            return False, {"error": "Docker not available"}, 0.0
        
        try:
            start_time = datetime.utcnow()
            
            # Create temporary directory for task files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write task payload to file
                payload_file = os.path.join(temp_dir, "payload.json")
                with open(payload_file, 'w') as f:
                    json.dump(task.payload, f)
                
                # Create Docker container for task execution
                container = self.docker_client.containers.run(
                    "python:3.9-slim",
                    command=f"python -c \"import json; import sys; exec(open('/task/payload.json').read())\"",
                    volumes={temp_dir: {'bind': '/task', 'mode': 'ro'}},
                    detach=True,
                    mem_limit="512m",
                    cpu_period=100000,
                    cpu_quota=50000,  # 50% CPU limit
                    network_disabled=True,
                    read_only=True,
                    remove=True
                )
                
                try:
                    # Wait for container to complete with timeout
                    result = container.wait(timeout=task.max_execution_time)
                    
                    if result['StatusCode'] == 0:
                        # Task completed successfully
                        logs = container.logs().decode('utf-8')
                        execution_time = (datetime.utcnow() - start_time).total_seconds()
                        
                        return True, {
                            "success": True,
                            "output": logs,
                            "execution_time": execution_time
                        }, execution_time
            else:
                        # Task failed
                        logs = container.logs().decode('utf-8')
                        execution_time = (datetime.utcnow() - start_time).total_seconds()
                        
                        return False, {
                            "success": False,
                            "error": logs,
                            "execution_time": execution_time
                        }, execution_time
                        
                except Exception as e:
                    # Task timed out or failed
                    container.kill()
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    
                    return False, {
                        "success": False,
                        "error": f"Task execution failed: {str(e)}",
                        "execution_time": execution_time
                    }, execution_time

        except Exception as e:
            logger.error(f"Failed to execute task in sandbox: {e}")
            return False, {"error": str(e)}, 0.0
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT task_id, task_type, payload, priority, max_execution_time,
                           required_capabilities, reward, currency, submitter_id, assigned_node_id,
                           status, result, error_message, started_at, completed_at, created_at, updated_at
                    FROM tasks WHERE task_id = ?
                """, (task_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                return Task(
                    task_id=result[0],
                    task_type=result[1],
                    payload=json.loads(result[2]),
                    priority=TaskPriority(result[3]),
                    max_execution_time=result[4],
                    required_capabilities=json.loads(result[5]),
                    reward=Decimal(result[6]),
                    currency=result[7],
                    submitter_id=result[8],
                    assigned_node_id=result[9],
                    status=TaskStatus(result[10]),
                    result=json.loads(result[11]) if result[11] else None,
                    error_message=result[12],
                    started_at=datetime.fromisoformat(result[13]) if result[13] else None,
                    completed_at=datetime.fromisoformat(result[14]) if result[14] else None,
                    created_at=datetime.fromisoformat(result[15]),
                    updated_at=datetime.fromisoformat(result[16])
                )

        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task engine statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total tasks
                cursor.execute("SELECT COUNT(*) FROM tasks")
                total_tasks = cursor.fetchone()[0]
                
                # Tasks by status
                cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
                status_counts = dict(cursor.fetchall())
                
                # Total rewards
                cursor.execute("SELECT SUM(CAST(reward AS DECIMAL)) FROM tasks WHERE status = 'completed'")
                total_rewards = cursor.fetchone()[0] or 0
                
                # Average execution time
                cursor.execute("""
                    SELECT AVG(CAST(execution_time AS REAL)) 
                    FROM task_results 
                    WHERE verification_status = 'verified'
                """)
                avg_execution_time = cursor.fetchone()[0] or 0
                
                return {
                    "total_tasks": total_tasks,
                    "status_counts": status_counts,
                    "total_rewards": float(total_rewards),
                    "avg_execution_time": float(avg_execution_time),
                    "success_rate": (status_counts.get("completed", 0) / total_tasks * 100) if total_tasks > 0 else 0
                }

        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            return {}


if __name__ == "__main__":
    # Example usage
    task_engine = TaskEngine()
    
    # Submit a test task
    task = task_engine.submit_task(
        task_type="python_script",
        payload={
            "code": "print('Hello from DuxNet Task Engine!'); result = 2 + 2; print(f'Result: {result}')",
            "language": "python"
        },
        priority=TaskPriority.NORMAL,
        max_execution_time=30,
        required_capabilities=["python", "compute"],
        reward=Decimal("5.0"),
        currency="FLOP",
        submitter_id="user-1"
    )
    
    print(f"Submitted task: {task.task_id}")
    
    # Get available tasks
    available_tasks = task_engine.get_available_tasks(["python", "compute"])
    print(f"Available tasks: {len(available_tasks)}")
    
    if available_tasks:
        test_task = available_tasks[0]
        
        # Assign and start task
        task_engine.assign_task(test_task.task_id, "node-1")
        task_engine.start_task(test_task.task_id, "node-1")
        
        # Execute task in sandbox
        success, result, execution_time = task_engine.execute_task_in_sandbox(test_task)
        
        if success:
            task_engine.complete_task(test_task.task_id, "node-1", result, execution_time)
            print(f"Task completed successfully in {execution_time:.2f} seconds")
        else:
            task_engine.fail_task(test_task.task_id, "node-1", result.get("error", "Unknown error"))
            print(f"Task failed: {result.get('error')}")
    
    # Get statistics
    stats = task_engine.get_task_statistics()
    print(f"Task engine statistics: {stats}")
