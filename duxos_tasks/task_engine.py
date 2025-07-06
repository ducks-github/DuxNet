"""
Task Engine

Main orchestrator for distributed task execution across the DuxOS network.
Coordinates task scheduling, execution, result verification, and payment processing.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .models import Task, TaskResult, TaskStatus, TaskType
from .task_scheduler import TaskScheduler
from .execution_sandbox import ExecutionSandbox, SandboxConfig
from .result_verifier import ResultVerifier

logger = logging.getLogger(__name__)


@dataclass
class TaskEngineConfig:
    """Configuration for the task engine"""
    max_concurrent_tasks: int = 10
    scheduling_interval: float = 5.0  # seconds
    result_verification: bool = True
    automatic_payments: bool = True
    sandbox_config: Optional[SandboxConfig] = None


class TaskEngine:
    """
    Main task engine that coordinates distributed task execution.
    
    Features:
    - Task submission and scheduling
    - Secure execution in sandboxed environments
    - Result verification and trust scoring
    - Automatic payment processing
    - Integration with registry and escrow systems
    """
    
    def __init__(self, config: Optional[TaskEngineConfig] = None, registry_client=None, 
                 escrow_client=None, wallet_client=None):
        self.config = config if config is not None else TaskEngineConfig()
        
        # External service clients
        self.registry_client = registry_client
        self.escrow_client = escrow_client
        self.wallet_client = wallet_client
        
        # Core components
        self.scheduler = TaskScheduler(registry_client)
        self.sandbox = ExecutionSandbox(self.config.sandbox_config)
        self.verifier = ResultVerifier()
        
        # Task tracking
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        
        # Engine state
        self.running = False
        self.scheduling_task = None
        
        logger.info("Task Engine initialized")
    
    async def start(self):
        """Start the task engine"""
        if self.running:
            logger.warning("Task Engine already running")
            return
        
        self.running = True
        self.scheduling_task = asyncio.create_task(self._scheduling_loop())
        
        logger.info("Task Engine started")
    
    async def stop(self):
        """Stop the task engine"""
        if not self.running:
            return
        
        self.running = False
        
        if self.scheduling_task:
            self.scheduling_task.cancel()
            try:
                await self.scheduling_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup active tasks
        await self._cleanup_active_tasks()
        
        logger.info("Task Engine stopped")
    
    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """Submit a new task for execution"""
        try:
            # Create task from data
            task = Task.from_dict(task_data)
            
            # Validate task
            if not self._validate_task(task):
                raise ValueError("Invalid task configuration")
            
            # Submit to scheduler
            success = await self.scheduler.submit_task(task)
            if not success:
                raise RuntimeError("Failed to submit task to scheduler")
            
            # Track task
            self.active_tasks[task.task_id] = task
            
            logger.info(f"Task {task.task_id} submitted successfully")
            return task.task_id
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        # Check active tasks
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "task_id": task.task_id,
                "status": task.status.value,
                "assigned_node": task.assigned_node_id,
                "created_at": task.created_at.isoformat(),
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None
            }
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": result.task_id,
                "status": result.status.value,
                "node_id": result.node_id,
                "execution_time": result.execution_time_seconds,
                "verified": result.verified,
                "created_at": result.created_at.isoformat()
            }
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            result = self.failed_tasks[task_id]
            return {
                "task_id": result.task_id,
                "status": result.status.value,
                "node_id": result.node_id,
                "error_message": result.error_message,
                "created_at": result.created_at.isoformat()
            }
        
        return None
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get result of a completed task"""
        if task_id in self.completed_tasks:
            result = self.completed_tasks[task_id]
            return {
                "task_id": result.task_id,
                "status": result.status.value,
                "output_data": result.output_data,
                "execution_time": result.execution_time_seconds,
                "verified": result.verified,
                "result_hash": result.result_hash
            }
        
        if task_id in self.failed_tasks:
            result = self.failed_tasks[task_id]
            return {
                "task_id": result.task_id,
                "status": result.status.value,
                "error_message": result.error_message,
                "execution_time": result.execution_time_seconds
            }
        
        return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        try:
            # Cancel in scheduler
            success = await self.scheduler.cancel_task(task_id)
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            logger.info(f"Task {task_id} cancelled")
            return success
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def _scheduling_loop(self):
        """Main scheduling loop"""
        while self.running:
            try:
                # Schedule pending tasks
                assignments = await self.scheduler.schedule_tasks()
                
                # Execute assigned tasks
                for assignment in assignments:
                    await self._execute_assigned_task(assignment)
                
                # Wait for next scheduling cycle
                await asyncio.sleep(self.config.scheduling_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _execute_assigned_task(self, assignment):
        """Execute a task that has been assigned to a node"""
        task_id = assignment.task_id
        node_id = assignment.node_id
        
        try:
            # Get task
            if task_id not in self.active_tasks:
                logger.error(f"Task {task_id} not found in active tasks")
                return
            
            task = self.active_tasks[task_id]
            
            # Update task status
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            logger.info(f"Executing task {task_id} on node {node_id}")
            
            # Execute in sandbox
            result = await self.sandbox.execute_task(task)
            
            # Verify result if enabled
            if self.config.result_verification:
                result.verified = await self.verifier.verify_result(result)
            
            # Process result
            await self._process_task_result(result)
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            
            # Create failure result
            result = TaskResult(
                task_id=task_id,
                node_id=node_id,
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
            
            await self._process_task_result(result)
    
    async def _process_task_result(self, result: TaskResult):
        """Process a completed task result"""
        try:
            # Update task status
            if result.task_id in self.active_tasks:
                task = self.active_tasks[result.task_id]
                task.status = result.status
                task.completed_at = datetime.utcnow()
                
                # Remove from active tasks
                del self.active_tasks[result.task_id]
            
            # Store result
            if result.status == TaskStatus.COMPLETED:
                self.completed_tasks[result.task_id] = result
                logger.info(f"Task {result.task_id} completed successfully")
                
                # Process payment if enabled
                if self.config.automatic_payments:
                    await self._process_payment(result)
                
                # Update node reputation
                await self._update_node_reputation(result)
                
            else:
                self.failed_tasks[result.task_id] = result
                logger.warning(f"Task {result.task_id} failed: {result.error_message}")
                
                # Update node reputation for failure
                await self._update_node_reputation(result)
            
        except Exception as e:
            logger.error(f"Error processing task result {result.task_id}: {e}")
    
    async def _process_payment(self, result: TaskResult):
        """Process payment for completed task"""
        try:
            if not self.escrow_client or not self.wallet_client:
                logger.warning("Payment processing disabled - no escrow/wallet clients")
                return
            
            # Get task details
            if result.task_id in self.active_tasks:
                task = self.active_tasks[result.task_id]
            else:
                # Task might have been removed, skip payment
                return
            
            if not task.escrow_id:
                logger.warning(f"No escrow ID for task {result.task_id}")
                return
            
            # Release escrow funds
            success = await self.escrow_client.release_escrow(
                escrow_id=task.escrow_id,
                result_hash=result.result_hash,
                provider_signature="signature_placeholder"  # TODO: Implement real signature
            )
            
            if success:
                logger.info(f"Payment processed for task {result.task_id}")
            else:
                logger.error(f"Failed to process payment for task {result.task_id}")
                
        except Exception as e:
            logger.error(f"Error processing payment for task {result.task_id}: {e}")
    
    async def _update_node_reputation(self, result: TaskResult):
        """Update node reputation based on task result"""
        try:
            if not self.registry_client:
                return
            
            # Determine reputation event type
            if result.status == TaskStatus.COMPLETED:
                event_type = "task_success"
            elif result.status == TaskStatus.TIMEOUT:
                event_type = "task_timeout"
            else:
                event_type = "task_failure"
            
            # Update reputation
            await self.registry_client.update_node_reputation(
                node_id=result.node_id,
                event_type=event_type
            )
            
            logger.info(f"Updated reputation for node {result.node_id}: {event_type}")
            
        except Exception as e:
            logger.error(f"Error updating node reputation: {e}")
    
    def _validate_task(self, task: Task) -> bool:
        """Validate task configuration"""
        if not task.service_name:
            logger.error("Task must have a service name")
            return False
        
        if not task.code:
            logger.error("Task must have code to execute")
            return False
        
        if task.payment_amount < 0:
            logger.error("Payment amount cannot be negative")
            return False
        
        if task.timeout_seconds <= 0:
            logger.error("Timeout must be positive")
            return False
        
        return True
    
    async def _cleanup_active_tasks(self):
        """Clean up active tasks when stopping"""
        for task_id in list(self.active_tasks.keys()):
            await self.cancel_task(task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task engine statistics"""
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "failed_tasks": len(self.failed_tasks),
            "total_tasks": len(self.active_tasks) + len(self.completed_tasks) + len(self.failed_tasks),
            "scheduler_stats": self.scheduler.get_scheduling_stats(),
            "sandbox_stats": self.sandbox.get_stats(),
            "running": self.running
        } 