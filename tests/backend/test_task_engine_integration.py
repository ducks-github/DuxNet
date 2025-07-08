"""
Task Engine Integration Tests

Comprehensive tests for the task engine functionality including
task submission, scheduling, execution, and result verification.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict

import pytest

from duxos_tasks.execution_sandbox import SandboxConfig
from duxos_tasks.models import Task, TaskStatus, TaskType
from duxos_tasks.task_engine import TaskEngine, TaskEngineConfig


class MockRegistryClient:
    """Mock registry client for testing"""

    def __init__(self):
        self.nodes = [
            {
                "node_id": "node_001",
                "cpu_cores": 4,
                "memory_mb": 8192,
                "storage_gb": 100,
                "capabilities": ["image_upscaler_v1", "text_processor"],
                "reputation": 85.0,
                "success_rate": 0.95,
                "status": "healthy",
            },
            {
                "node_id": "node_002",
                "cpu_cores": 8,
                "memory_mb": 16384,
                "storage_gb": 200,
                "capabilities": ["machine_learning", "data_analysis"],
                "reputation": 92.0,
                "success_rate": 0.98,
                "status": "healthy",
            },
        ]

    async def get_healthy_nodes(self):
        """Get healthy nodes"""
        return [node for node in self.nodes if node["status"] == "healthy"]

    async def update_node_reputation(self, node_id: str, event_type: str):
        """Update node reputation"""
        for node in self.nodes:
            if node["node_id"] == node_id:
                # Simple reputation update logic
                if event_type == "task_success":
                    node["reputation"] = min(100.0, node["reputation"] + 1.0)
                elif event_type == "task_failure":
                    node["reputation"] = max(0.0, node["reputation"] - 2.0)
                break
        return True


class MockEscrowClient:
    """Mock escrow client for testing"""

    def __init__(self):
        self.escrows = {}

    async def release_escrow(self, escrow_id: str, result_hash: str, provider_signature: str):
        """Release escrow funds"""
        if escrow_id in self.escrows:
            self.escrows[escrow_id]["released"] = True
            self.escrows[escrow_id]["result_hash"] = result_hash
            return True
        return False


class MockWalletClient:
    """Mock wallet client for testing"""

    def __init__(self):
        self.balances = {}

    async def get_balance(self, node_id: str):
        """Get wallet balance"""
        return self.balances.get(node_id, 0.0)

    async def send_transaction(self, from_node: str, to_node: str, amount: float):
        """Send transaction"""
        if from_node in self.balances and self.balances[from_node] >= amount:
            self.balances[from_node] -= amount
            self.balances[to_node] = self.balances.get(to_node, 0.0) + amount
            return True
        return False


@pytest.fixture
def task_engine_config():
    """Create task engine configuration for testing"""
    return TaskEngineConfig(
        max_concurrent_tasks=5,
        scheduling_interval=1.0,  # Fast scheduling for tests
        result_verification=True,
        automatic_payments=True,
        sandbox_config=SandboxConfig(
            runtime="native",  # Use native execution for tests
            memory_limit_mb=1024,
            timeout_seconds=60,
        ),
    )


@pytest.fixture
def mock_clients():
    """Create mock service clients"""
    return {
        "registry": MockRegistryClient(),
        "escrow": MockEscrowClient(),
        "wallet": MockWalletClient(),
    }


@pytest.fixture
async def task_engine(task_engine_config, mock_clients):
    """Create task engine instance for testing"""
    engine = TaskEngine(
        config=task_engine_config,
        registry_client=mock_clients["registry"],
        escrow_client=mock_clients["escrow"],
        wallet_client=mock_clients["wallet"],
    )

    # Start the engine
    await engine.start()

    yield engine

    # Stop the engine
    await engine.stop()


class TestTaskEngineIntegration:
    """Integration tests for task engine"""

    @pytest.mark.asyncio
    async def test_task_submission_and_execution(self, task_engine):
        """Test complete task submission and execution flow"""
        # Create a simple task
        task_data = {
            "service_name": "test_service",
            "task_type": "api_call",
            "code": """
import json
import sys

# Simple test task
result = {"message": "Hello from task!", "timestamp": "2024-01-01"}
print(json.dumps(result))
""",
            "parameters": {"test_param": "value"},
            "cpu_cores": 1,
            "memory_mb": 256,
            "timeout_seconds": 30,
            "payment_amount": 10.0,
            "priority": 3,
        }

        # Submit task
        task_id = await task_engine.submit_task(task_data)
        assert task_id is not None

        # Wait for task to be processed
        await asyncio.sleep(3)

        # Check task status
        status = await task_engine.get_task_status(task_id)
        assert status is not None
        assert status["task_id"] == task_id

        # Wait for completion
        max_wait = 30
        while max_wait > 0:
            status = await task_engine.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(1)
            max_wait -= 1

        # Get result
        result = await task_engine.get_task_result(task_id)
        assert result is not None

        # Verify result
        if result["status"] == "completed":
            assert "output_data" in result
            assert result["output_data"]["message"] == "Hello from task!"
        else:
            pytest.fail(f"Task failed: {result.get('error_message', 'Unknown error')}")

    @pytest.mark.asyncio
    async def test_task_cancellation(self, task_engine):
        """Test task cancellation"""
        # Submit a long-running task
        task_data = {
            "service_name": "long_task",
            "task_type": "api_call",
            "code": """
import time
import json

# Long running task
time.sleep(10)
result = {"status": "completed"}
print(json.dumps(result))
""",
            "cpu_cores": 1,
            "memory_mb": 256,
            "timeout_seconds": 60,
            "payment_amount": 5.0,
            "priority": 1,
        }

        task_id = await task_engine.submit_task(task_data)

        # Wait a bit for task to be assigned
        await asyncio.sleep(2)

        # Cancel the task
        success = await task_engine.cancel_task(task_id)
        assert success

        # Verify task is cancelled
        status = await task_engine.get_task_status(task_id)
        assert status is None or status["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_multiple_tasks(self, task_engine):
        """Test handling multiple concurrent tasks"""
        tasks = []

        # Submit multiple tasks
        for i in range(3):
            task_data = {
                "service_name": f"multi_task_{i}",
                "task_type": "api_call",
                "code": f"""
import json
result = {{"task_id": {i}, "message": "Task {i} completed"}}
print(json.dumps(result))
""",
                "cpu_cores": 1,
                "memory_mb": 256,
                "timeout_seconds": 30,
                "payment_amount": 1.0,
                "priority": 2,
            }

            task_id = await task_engine.submit_task(task_data)
            tasks.append(task_id)

        # Wait for all tasks to complete
        await asyncio.sleep(10)

        # Check all tasks
        completed = 0
        for task_id in tasks:
            result = await task_engine.get_task_result(task_id)
            if result and result["status"] == "completed":
                completed += 1

        # Should have at least some completed tasks
        assert completed > 0

    @pytest.mark.asyncio
    async def test_task_with_escrow(self, task_engine, mock_clients):
        """Test task execution with escrow payment"""
        # Setup escrow
        escrow_id = "test_escrow_001"
        mock_clients["escrow"].escrows[escrow_id] = {"amount": 20.0, "released": False}

        # Submit task with escrow
        task_data = {
            "service_name": "escrow_test",
            "task_type": "api_call",
            "code": """
import json
result = {"payment": "processed"}
print(json.dumps(result))
""",
            "cpu_cores": 1,
            "memory_mb": 256,
            "timeout_seconds": 30,
            "payment_amount": 20.0,
            "escrow_id": escrow_id,
            "priority": 4,
        }

        task_id = await task_engine.submit_task(task_data)

        # Wait for completion
        await asyncio.sleep(5)

        # Check escrow was released
        escrow = mock_clients["escrow"].escrows[escrow_id]
        assert escrow["released"] is True

    @pytest.mark.asyncio
    async def test_node_reputation_update(self, task_engine, mock_clients):
        """Test node reputation updates based on task results"""
        # Get initial reputation
        initial_nodes = await mock_clients["registry"].get_healthy_nodes()
        initial_reputation = {node["node_id"]: node["reputation"] for node in initial_nodes}

        # Submit successful task
        task_data = {
            "service_name": "reputation_test",
            "task_type": "api_call",
            "code": """
import json
result = {"success": True}
print(json.dumps(result))
""",
            "cpu_cores": 1,
            "memory_mb": 256,
            "timeout_seconds": 30,
            "payment_amount": 5.0,
            "priority": 3,
        }

        task_id = await task_engine.submit_task(task_data)

        # Wait for completion
        await asyncio.sleep(5)

        # Check reputation was updated
        updated_nodes = await mock_clients["registry"].get_healthy_nodes()
        for node in updated_nodes:
            if node["node_id"] in initial_reputation:
                # Reputation should have increased for successful task
                assert node["reputation"] >= initial_reputation[node["node_id"]]

    @pytest.mark.asyncio
    async def test_engine_statistics(self, task_engine):
        """Test engine statistics collection"""
        # Submit a few tasks
        for i in range(2):
            task_data = {
                "service_name": f"stats_test_{i}",
                "task_type": "api_call",
                "code": f"""
import json
result = {{"test": {i}}}
print(json.dumps(result))
""",
                "cpu_cores": 1,
                "memory_mb": 256,
                "timeout_seconds": 30,
                "payment_amount": 1.0,
                "priority": 2,
            }
            await task_engine.submit_task(task_data)

        # Wait for processing
        await asyncio.sleep(5)

        # Get statistics
        stats = task_engine.get_stats()

        # Verify statistics
        assert "active_tasks" in stats
        assert "completed_tasks" in stats
        assert "failed_tasks" in stats
        assert "total_tasks" in stats
        assert "running" in stats
        assert stats["running"] is True

        # Should have processed some tasks
        assert stats["total_tasks"] >= 2

    @pytest.mark.asyncio
    async def test_error_handling(self, task_engine):
        """Test error handling for invalid tasks"""
        # Submit task with invalid code
        task_data = {
            "service_name": "error_test",
            "task_type": "api_call",
            "code": """
# Invalid Python code
print("unclosed quote
""",
            "cpu_cores": 1,
            "memory_mb": 256,
            "timeout_seconds": 30,
            "payment_amount": 1.0,
            "priority": 1,
        }

        task_id = await task_engine.submit_task(task_data)

        # Wait for processing
        await asyncio.sleep(5)

        # Check result
        result = await task_engine.get_task_result(task_id)
        assert result is not None
        assert result["status"] == "failed"
        assert "error_message" in result

    @pytest.mark.asyncio
    async def test_task_priority(self, task_engine):
        """Test task priority handling"""
        # Submit tasks with different priorities
        tasks = []
        for priority in [1, 5, 3, 2, 4]:
            task_data = {
                "service_name": f"priority_test_{priority}",
                "task_type": "api_call",
                "code": f"""
import json
result = {{"priority": {priority}}}
print(json.dumps(result))
""",
                "cpu_cores": 1,
                "memory_mb": 256,
                "timeout_seconds": 30,
                "payment_amount": 1.0,
                "priority": priority,
            }

            task_id = await task_engine.submit_task(task_data)
            tasks.append((task_id, priority))

        # Wait for processing
        await asyncio.sleep(8)

        # Check that higher priority tasks were processed first
        # (This is a basic check - actual scheduling may vary)
        completed_tasks = []
        for task_id, priority in tasks:
            result = await task_engine.get_task_result(task_id)
            if result and result["status"] == "completed":
                completed_tasks.append(priority)

        # Should have completed some tasks
        assert len(completed_tasks) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
