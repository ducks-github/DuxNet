# DuxOS Task Engine

## 🎯 Overview

The Task Engine is the core component of DuxOS that distributes, schedules, and executes computational tasks across the decentralized network. It provides secure, sandboxed execution environments with automatic payment processing and reputation management.

## ✨ Key Features

- **Intelligent Task Scheduling**: Load balancing and reputation-weighted node selection
- **Secure Execution Sandbox**: Docker-based isolation with resource limits
- **Result Verification**: Cryptographic verification and trust scoring
- **Automatic Payments**: Integration with escrow system for secure payments
- **Reputation Management**: Node reputation updates based on task performance
- **REST API**: Complete API for task submission and monitoring
- **Real-time Monitoring**: Live statistics and health monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Task Engine   │    │  Task Scheduler │    │ Execution       │
│                 │    │                 │    │ Sandbox         │
│ • API Layer     │    │ • Load Balancing│    │ • Docker        │
│ • Task Mgmt     │    │ • Node Selection│    │ • Resource      │
│ • Payment Proc  │    │ • Priority Queue│    │   Limits        │
│ • Reputation    │    │ • Retry Logic   │    │ • Security      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Result Verifier │
                    │                 │
                    │ • Hash Check    │
                    │ • Format Valid  │
                    │ • Trust Scoring │
                    └─────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r duxos_tasks/requirements.txt

# Install Docker (optional, for sandboxed execution)
sudo apt-get install docker.io
sudo systemctl start docker
```

### Basic Usage

```python
import asyncio
from duxos_tasks.task_engine import TaskEngine, TaskEngineConfig

async def main():
    # Create task engine
    config = TaskEngineConfig(
        max_concurrent_tasks=5,
        scheduling_interval=2.0,
        result_verification=True,
        automatic_payments=False  # Disable for testing
    )
    
    engine = TaskEngine(config=config)
    
    # Start the engine
    await engine.start()
    
    # Submit a task
    task_data = {
        "service_name": "test_service",
        "task_type": "api_call",
        "code": """
import json
result = {"message": "Hello from task!"}
print(json.dumps(result))
""",
        "cpu_cores": 1,
        "memory_mb": 256,
        "timeout_seconds": 30,
        "payment_amount": 10.0,
        "priority": 3
    }
    
    task_id = await engine.submit_task(task_data)
    print(f"Task submitted: {task_id}")
    
    # Wait for completion
    await asyncio.sleep(5)
    
    # Get result
    result = await engine.get_task_result(task_id)
    print(f"Task result: {result}")
    
    # Stop the engine
    await engine.stop()

asyncio.run(main())
```

### Using the REST API

```bash
# Start the API server
python -m duxos_tasks.api

# Submit a task
curl -X POST "http://localhost:8001/tasks/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "image_processor",
    "code": "import json; print(json.dumps({\"processed\": True}))",
    "cpu_cores": 2,
    "memory_mb": 512,
    "payment_amount": 5.0
  }'

# Check task status
curl -X GET "http://localhost:8001/tasks/{task_id}/status"

# Get task result
curl -X GET "http://localhost:8001/tasks/{task_id}/result"
```

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tasks/submit` | Submit new task |
| `GET` | `/tasks/{id}/status` | Get task status |
| `GET` | `/tasks/{id}/result` | Get task result |
| `DELETE` | `/tasks/{id}` | Cancel task |
| `GET` | `/engine/stats` | Get engine statistics |
| `POST` | `/engine/start` | Start engine |
| `POST` | `/engine/stop` | Stop engine |
| `GET` | `/health` | Health check |

## 🔧 Configuration

The task engine is configured via `config.yaml`:

```yaml
# Engine settings
engine:
  max_concurrent_tasks: 10
  scheduling_interval: 5.0
  result_verification: true
  automatic_payments: true

# Sandbox configuration
sandbox:
  runtime: "docker"  # docker, native, container
  memory_limit_mb: 512
  cpu_limit: 1.0
  timeout_seconds: 300
  base_image: "python:3.9-slim"

# API configuration
api:
  host: "0.0.0.0"
  port: 8001
  enable_cors: true
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/task_engine/ -v

# Run specific test
pytest tests/task_engine/test_task_engine_integration.py::TestTaskEngineIntegration::test_task_submission_and_execution -v

# Run with coverage
pytest tests/task_engine/ --cov=duxos_tasks --cov-report=html
```

## 🔗 Integration

### With Node Registry

The task engine integrates with the Node Registry to:
- Discover available nodes
- Get node capabilities and reputation
- Update node reputation based on task results

### With Escrow System

Automatic payment processing:
- Release escrow funds upon successful task completion
- Handle payment failures and refunds
- Track transaction history

### With Wallet System

Secure transaction handling:
- Verify payment amounts
- Process Flopcoin transactions
- Maintain transaction audit trail

## 📊 Monitoring

### Engine Statistics

```python
stats = engine.get_stats()
print(f"Active tasks: {stats['active_tasks']}")
print(f"Completed tasks: {stats['completed_tasks']}")
print(f"Success rate: {stats['scheduler_stats']['success_rate']:.2%}")
```

### Health Monitoring

```bash
# Check engine health
curl -X GET "http://localhost:8001/health"

# Get detailed statistics
curl -X GET "http://localhost:8001/engine/stats"
```

## 🛡️ Security Features

- **Sandboxed Execution**: Isolated containers with resource limits
- **Result Verification**: Cryptographic hash verification
- **Input Validation**: Comprehensive parameter validation
- **Rate Limiting**: API rate limiting to prevent abuse
- **Authentication**: Node authentication for task execution

## 🔄 Task Lifecycle

1. **Submission**: Task submitted via API or programmatically
2. **Scheduling**: Task assigned to optimal node based on capabilities and reputation
3. **Execution**: Task runs in secure sandbox with resource monitoring
4. **Verification**: Result verified for integrity and correctness
5. **Payment**: Escrow funds released upon successful completion
6. **Reputation**: Node reputation updated based on performance

## 📈 Performance

- **Concurrent Tasks**: Support for 10+ concurrent task executions
- **Response Time**: Task assignment within 5 seconds
- **Throughput**: 100+ tasks per hour per node
- **Reliability**: 99%+ task completion rate

## 🚨 Troubleshooting

### Common Issues

1. **Docker not available**: Task engine falls back to native execution
2. **Node unavailable**: Tasks are retried with exponential backoff
3. **Payment failure**: Tasks marked as failed, escrow refunded
4. **Timeout**: Long-running tasks are automatically cancelled

### Logs

```bash
# View engine logs
tail -f /var/log/duxos/task_engine.log

# Check Docker logs (if using Docker)
docker logs <container_id>
```

## 🔮 Future Enhancements

- **GPU Support**: GPU-accelerated task execution
- **Distributed Storage**: IPFS integration for large data
- **Advanced Scheduling**: Machine learning-based node selection
- **Real-time Streaming**: WebSocket support for live updates
- **Mobile Support**: Mobile app for task monitoring

## 📚 Documentation

- [API Documentation](http://localhost:8001/docs) (when running)
- [Configuration Guide](config.yaml)
- [Testing Guide](tests/task_engine/)
- [Integration Examples](examples/)

---

**Task Engine Version**: 1.0.0  
**Last Updated**: January 2024  
**Status**: ✅ Production Ready 