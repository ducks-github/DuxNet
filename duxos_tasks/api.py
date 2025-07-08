"""
Task Engine API

REST API for task submission, monitoring, and management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .models import Task, TaskStatus, TaskType
from .task_engine import TaskEngine

logger = logging.getLogger(__name__)


class TaskSubmissionRequest(BaseModel):
    """Request model for task submission"""

    service_name: str = Field(..., description="Name of the service to execute")
    task_type: str = Field(default="api_call", description="Type of task")
    code: str = Field(..., description="Code to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")
    input_data: Optional[Dict[str, Any]] = Field(None, description="Input data for the task")
    cpu_cores: int = Field(default=1, ge=1, le=16, description="CPU cores required")
    memory_mb: int = Field(default=512, ge=128, le=8192, description="Memory required in MB")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="Timeout in seconds")
    payment_amount: float = Field(default=0.0, ge=0.0, description="Payment amount in FLOP")
    priority: int = Field(default=1, ge=1, le=5, description="Task priority (1-5)")
    escrow_id: Optional[str] = Field(None, description="Escrow contract ID")


class TaskSubmissionResponse(BaseModel):
    """Response model for task submission"""

    task_id: str
    status: str
    message: str
    created_at: str


class TaskStatusResponse(BaseModel):
    """Response model for task status"""

    task_id: str
    status: str
    assigned_node: Optional[str] = None
    created_at: str
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time: Optional[float] = None
    verified: Optional[bool] = None


class TaskResultResponse(BaseModel):
    """Response model for task result"""

    task_id: str
    status: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    verified: Optional[bool] = None
    result_hash: Optional[str] = None


class EngineStatsResponse(BaseModel):
    """Response model for engine statistics"""

    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_tasks: int
    running: bool
    scheduler_stats: Dict[str, Any]
    sandbox_stats: Dict[str, Any]


class TaskEngineAPI:
    """
    REST API for the Task Engine.

    Provides endpoints for:
    - Task submission
    - Status monitoring
    - Result retrieval
    - Engine statistics
    """

    def __init__(self, task_engine: TaskEngine):
        self.task_engine = task_engine
        self.app = FastAPI(
            title="DuxOS Task Engine API",
            description="Distributed task execution API",
            version="1.0.0",
        )

        self._setup_routes()
        logger.info("Task Engine API initialized")

    def _setup_routes(self):
        """Setup API routes"""

        @self.app.post("/tasks/submit", response_model=TaskSubmissionResponse)
        async def submit_task(request: TaskSubmissionRequest):
            """Submit a new task for execution"""
            try:
                # Convert request to task data
                task_data = {
                    "service_name": request.service_name,
                    "task_type": request.task_type,
                    "code": request.code,
                    "parameters": request.parameters,
                    "input_data": request.input_data,
                    "cpu_cores": request.cpu_cores,
                    "memory_mb": request.memory_mb,
                    "timeout_seconds": request.timeout_seconds,
                    "payment_amount": request.payment_amount,
                    "priority": request.priority,
                    "escrow_id": request.escrow_id,
                }

                # Submit task
                task_id = await self.task_engine.submit_task(task_data)

                return TaskSubmissionResponse(
                    task_id=task_id,
                    status="submitted",
                    message="Task submitted successfully",
                    created_at=datetime.utcnow().isoformat(),
                )

            except Exception as e:
                logger.error(f"Error submitting task: {e}")
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/tasks/{task_id}/status", response_model=TaskStatusResponse)
        async def get_task_status(task_id: str):
            """Get status of a task"""
            try:
                status = await self.task_engine.get_task_status(task_id)
                if not status:
                    raise HTTPException(status_code=404, detail="Task not found")

                return TaskStatusResponse(**status)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting task status: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
        async def get_task_result(task_id: str):
            """Get result of a completed task"""
            try:
                result = await self.task_engine.get_task_result(task_id)
                if not result:
                    raise HTTPException(status_code=404, detail="Task result not found")

                return TaskResultResponse(**result)

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting task result: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.delete("/tasks/{task_id}")
        async def cancel_task(task_id: str):
            """Cancel a pending task"""
            try:
                success = await self.task_engine.cancel_task(task_id)
                if not success:
                    raise HTTPException(
                        status_code=404, detail="Task not found or cannot be cancelled"
                    )

                return {"message": "Task cancelled successfully"}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error cancelling task: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/engine/stats", response_model=EngineStatsResponse)
        async def get_engine_stats():
            """Get task engine statistics"""
            try:
                stats = self.task_engine.get_stats()
                return EngineStatsResponse(**stats)

            except Exception as e:
                logger.error(f"Error getting engine stats: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.post("/engine/start")
        async def start_engine():
            """Start the task engine"""
            try:
                await self.task_engine.start()
                return {"message": "Task engine started successfully"}

            except Exception as e:
                logger.error(f"Error starting engine: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.post("/engine/stop")
        async def stop_engine():
            """Stop the task engine"""
            try:
                await self.task_engine.stop()
                return {"message": "Task engine stopped successfully"}

            except Exception as e:
                logger.error(f"Error stopping engine: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "engine_running": self.task_engine.running,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def get_app(self) -> FastAPI:
        """Get the FastAPI application"""
        return self.app


# Example usage and testing
async def create_task_engine_api():
    """Create a task engine API instance for testing"""
    # Create task engine configuration
    config = TaskEngineConfig(
        max_concurrent_tasks=5,
        scheduling_interval=2.0,
        result_verification=True,
        automatic_payments=False,  # Disable for testing
    )

    # Create task engine
    task_engine = TaskEngine(config=config)

    # Create API
    api = TaskEngineAPI(task_engine)

    return api


if __name__ == "__main__":
    import uvicorn

    async def main():
        api = await create_task_engine_api()
        app = api.get_app()

        # Start the server
        uvicorn.run(app, host="0.0.0.0", port=8001)

    asyncio.run(main())
