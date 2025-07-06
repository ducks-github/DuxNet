"""
Task Scheduler

Responsible for assigning tasks to appropriate nodes based on capabilities,
load balancing, and reputation scoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import heapq
import random

from .models import Task, TaskStatus, NodeCapability, TaskAssignment

logger = logging.getLogger(__name__)


@dataclass
class SchedulingMetrics:
    """Metrics for scheduling decisions"""
    total_tasks: int = 0
    assigned_tasks: int = 0
    failed_assignments: int = 0
    avg_assignment_time: float = 0.0
    load_distribution: Dict[str, int] = field(default_factory=dict)


class TaskScheduler:
    """
    Intelligent task scheduler that assigns tasks to optimal nodes.
    
    Features:
    - Load balancing across available nodes
    - Capability-based filtering
    - Reputation-weighted assignment
    - Priority queue for urgent tasks
    - Retry logic for failed assignments
    """
    
    def __init__(self, registry_client=None, max_retries: int = 3):
        self.registry_client = registry_client
        self.max_retries = max_retries
        
        # Task queues by priority (stored as tuples for heapq)
        self.priority_queues: Dict[int, List[Tuple[int, float, Task]]] = {
            1: [],  # Low priority
            2: [],
            3: [],
            4: [],
            5: []   # High priority
        }
        
        # Node assignments tracking
        self.node_assignments: Dict[str, List[TaskAssignment]] = {}
        self.task_assignments: Dict[str, TaskAssignment] = {}
        
        # Scheduling metrics
        self.metrics = SchedulingMetrics()
        
        # Configuration
        self.enable_load_balancing = True
        self.enable_reputation_weighting = True
        self.max_tasks_per_node = 10
        self.assignment_timeout = 300  # seconds
        
        logger.info("Task Scheduler initialized")
    
    async def submit_task(self, task: Task) -> bool:
        """Submit a task for scheduling"""
        try:
            # Add task to appropriate priority queue
            priority = min(max(task.priority, 1), 5)
            heapq.heappush(self.priority_queues[priority], (-priority, task.created_at.timestamp(), task))
            
            self.metrics.total_tasks += 1
            logger.info(f"Task {task.task_id} submitted with priority {priority}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {e}")
            return False
    
    async def schedule_tasks(self) -> List[TaskAssignment]:
        """Schedule pending tasks to available nodes"""
        assignments = []
        
        try:
            # Get available nodes from registry
            available_nodes = await self._get_available_nodes()
            if not available_nodes:
                logger.warning("No available nodes for task scheduling")
                return assignments
            
            # Process tasks by priority (highest first)
            for priority in range(5, 0, -1):
                while self.priority_queues[priority]:
                    # Get next task
                    _, _, task = heapq.heappop(self.priority_queues[priority])
                    
                    # Try to assign task
                    assignment = await self._assign_task_to_node(task, available_nodes)
                    if assignment:
                        assignments.append(assignment)
                        self.metrics.assigned_tasks += 1
                    else:
                        # Re-queue task if assignment failed
                        retry_count = task.metadata.get('retry_count', 0)
                        if retry_count < self.max_retries:
                            task.metadata['retry_count'] = retry_count + 1
                            heapq.heappush(self.priority_queues[priority], (-priority, task.created_at.timestamp(), task))
                            logger.warning(f"Re-queuing task {task.task_id} for retry")
                        else:
                            self.metrics.failed_assignments += 1
                            logger.error(f"Task {task.task_id} failed after {self.max_retries} retries")
            
            # Update metrics
            self._update_metrics()
            
        except Exception as e:
            logger.error(f"Error in task scheduling: {e}")
        
        return assignments
    
    async def _get_available_nodes(self) -> List[NodeCapability]:
        """Get available nodes from registry"""
        try:
            if not self.registry_client:
                # Return mock nodes for testing
                return self._get_mock_nodes()
            
            # Query registry for healthy nodes
            nodes = await self.registry_client.get_healthy_nodes()
            
            # Convert to NodeCapability objects
            capabilities = []
            for node in nodes:
                capability = NodeCapability(
                    node_id=node.get('node_id'),
                    cpu_cores=node.get('cpu_cores', 1),
                    memory_mb=node.get('memory_mb', 512),
                    storage_gb=node.get('storage_gb', 10),
                    gpu_enabled=node.get('gpu_enabled', False),
                    supported_services=node.get('capabilities', []),
                    reputation_score=node.get('reputation', 50.0),
                    success_rate=node.get('success_rate', 0.8)
                )
                capabilities.append(capability)
            
            return capabilities
            
        except Exception as e:
            logger.error(f"Error getting available nodes: {e}")
            return self._get_mock_nodes()
    
    async def _assign_task_to_node(self, task: Task, available_nodes: List[NodeCapability]) -> Optional[TaskAssignment]:
        """Assign a specific task to the best available node"""
        try:
            # Filter nodes by capability
            suitable_nodes = [node for node in available_nodes if node.can_execute(task)]
            if not suitable_nodes:
                logger.warning(f"No suitable nodes for task {task.task_id}")
                return None
            
            # Score nodes for this task
            scored_nodes = []
            for node in suitable_nodes:
                score = self._calculate_node_score(node, task)
                scored_nodes.append((score, node))
            
            # Sort by score (highest first)
            scored_nodes.sort(reverse=True)
            
            # Try to assign to best node
            for score, node in scored_nodes:
                if await self._can_assign_to_node(node.node_id, task):
                    assignment = TaskAssignment(
                        task_id=task.task_id,
                        node_id=node.node_id,
                        priority=task.priority
                    )
                    
                    # Update task status
                    task.status = TaskStatus.ASSIGNED
                    task.assigned_node_id = node.node_id
                    task.assigned_at = datetime.utcnow()
                    
                    # Track assignment
                    self.task_assignments[task.task_id] = assignment
                    if node.node_id not in self.node_assignments:
                        self.node_assignments[node.node_id] = []
                    self.node_assignments[node.node_id].append(assignment)
                    
                    logger.info(f"Assigned task {task.task_id} to node {node.node_id} (score: {score:.2f})")
                    return assignment
            
            logger.warning(f"Could not assign task {task.task_id} to any suitable node")
            return None
            
        except Exception as e:
            logger.error(f"Error assigning task {task.task_id}: {e}")
            return None
    
    def _calculate_node_score(self, node: NodeCapability, task: Task) -> float:
        """Calculate node score for task assignment"""
        score = 0.0
        
        # Base capability score
        score += node.get_score()
        
        # Load balancing (fewer current assignments = higher score)
        current_load = len(self.node_assignments.get(node.node_id, []))
        load_penalty = current_load * 10
        score -= load_penalty
        
        # Reputation weighting
        if self.enable_reputation_weighting and node.reputation_score:
            score += node.reputation_score * 0.5
        
        # Service affinity (nodes that support the specific service get bonus)
        if task.service_name in node.supported_services:
            score += 100
        
        # Performance history
        if node.success_rate:
            score += node.success_rate * 50
        if node.avg_execution_time:
            score += max(0, 100 - node.avg_execution_time)
        
        # Random factor to prevent ties
        score += random.uniform(0, 1)
        
        return score
    
    async def _can_assign_to_node(self, node_id: str, task: Task) -> bool:
        """Check if node can accept the task assignment"""
        # Check current load
        current_assignments = self.node_assignments.get(node_id, [])
        if len(current_assignments) >= self.max_tasks_per_node:
            return False
        
        # Check for duplicate assignment
        if task.task_id in self.task_assignments:
            return False
        
        return True
    
    def _update_metrics(self):
        """Update scheduling metrics"""
        total_assignments = sum(len(assignments) for assignments in self.node_assignments.values())
        self.metrics.load_distribution = {
            node_id: len(assignments) 
            for node_id, assignments in self.node_assignments.items()
        }
    
    def _get_mock_nodes(self) -> List[NodeCapability]:
        """Return mock nodes for testing"""
        return [
            NodeCapability(
                node_id="node_001",
                cpu_cores=4,
                memory_mb=8192,
                storage_gb=100,
                supported_services=["image_upscaler_v1", "text_processor"],
                reputation_score=85.0,
                success_rate=0.95
            ),
            NodeCapability(
                node_id="node_002", 
                cpu_cores=8,
                memory_mb=16384,
                storage_gb=200,
                gpu_enabled=True,
                supported_services=["machine_learning", "data_analysis"],
                reputation_score=92.0,
                success_rate=0.98
            ),
            NodeCapability(
                node_id="node_003",
                cpu_cores=2,
                memory_mb=4096,
                storage_gb=50,
                supported_services=["api_call", "batch_processing"],
                reputation_score=75.0,
                success_rate=0.88
            )
        ]
    
    def get_scheduling_stats(self) -> Dict[str, Any]:
        """Get current scheduling statistics"""
        return {
            "total_tasks": self.metrics.total_tasks,
            "assigned_tasks": self.metrics.assigned_tasks,
            "failed_assignments": self.metrics.failed_assignments,
            "success_rate": self.metrics.assigned_tasks / max(self.metrics.total_tasks, 1),
            "load_distribution": self.metrics.load_distribution,
            "queue_sizes": {
                priority: len(queue) for priority, queue in self.priority_queues.items()
            }
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        try:
            # Remove from all priority queues
            for priority, queue in self.priority_queues.items():
                self.priority_queues[priority] = [
                    item for item in queue 
                    if getattr(item[2], 'task_id', None) != task_id
                ]
            
            # Remove from assignments
            if task_id in self.task_assignments:
                assignment = self.task_assignments[task_id]
                if assignment.node_id in self.node_assignments:
                    self.node_assignments[assignment.node_id] = [
                        a for a in self.node_assignments[assignment.node_id]
                        if a.task_id != task_id
                    ]
                del self.task_assignments[task_id]
            
            logger.info(f"Task {task_id} cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False 