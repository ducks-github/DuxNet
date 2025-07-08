# DuxNet API Reference

This document provides comprehensive API documentation for all DuxNet modules, including Python APIs, CLI commands, REST endpoints, and configuration schemas.

## Table of Contents

- [Python APIs](#python-apis)
  - [Wallet API](#wallet-api)
  - [Store API](#store-api)
  - [Registry API](#registry-api)
  - [Daemon API](#daemon-api)
- [CLI Commands](#cli-commands)
  - [Wallet CLI](#wallet-cli)
  - [Registry CLI](#registry-cli)
  - [Store CLI](#store-cli)
- [REST API Endpoints](#rest-api-endpoints)
  - [Store Service API](#store-service-api)
  - [Task Engine API](#task-engine-api)
- [Configuration Schemas](#configuration-schemas)
  - [Wallet Configuration](#wallet-configuration)
  - [Store Configuration](#store-configuration)
  - [Daemon Configuration](#daemon-configuration)

---

## Python APIs

### Wallet API

The `FlopcoinWallet` class provides secure wallet operations for Flopcoin transactions.

#### Class: `FlopcoinWallet`

**Location:** `duxnet_wallet/wallet.py`

**Constructor:**
```python
FlopcoinWallet(config_path: Optional[str] = None)
```

**Parameters:**
- `config_path` (Optional[str]): Path to configuration file. Defaults to `config.yaml` in the same directory.

**Methods:**

##### `get_new_address() -> str`
Generates a new Flopcoin address.

**Returns:**
- `str`: Newly generated wallet address

**Example:**
```python
from duxnet_wallet.wallet import FlopcoinWallet

wallet = FlopcoinWallet()
address = wallet.get_new_address()
print(f"New address: {address}")
```

##### `get_balance() -> float`
Retrieves the current wallet balance.

**Returns:**
- `float`: Current balance in Flopcoin

**Example:**
```python
balance = wallet.get_balance()
print(f"Balance: {balance} FLOP")
```

##### `send_to_address(address: str, amount: float) -> str`
Sends Flopcoin to a specified address.

**Parameters:**
- `address` (str): Destination wallet address
- `amount` (float): Amount to send in Flopcoin

**Returns:**
- `str`: Transaction ID

**Example:**
```python
txid = wallet.send_to_address("FLOP123...", 10.5)
print(f"Transaction ID: {txid}")
```

### Store API

The `StoreService` class manages decentralized app/API metadata and discovery.

#### Class: `StoreService`

**Location:** `duxnet_store/store_service.py`

**Constructor:**
```python
StoreService(config: dict)
```

**Methods:**

##### `register_api(api_data: dict) -> str`
Registers a new API in the store.

**Parameters:**
- `api_data` (dict): API metadata including name, description, version, etc.

**Returns:**
- `str`: API registration ID

**Example:**
```python
from duxnet_store.store_service import StoreService

store = StoreService(config)
api_id = store.register_api({
    "name": "image_upscale",
    "version": "1.0.0",
    "description": "AI-powered image upscaling service",
    "price": 0.1,
    "category": "image_processing"
})
```

##### `search_apis(query: str, limit: int = 20) -> List[dict]`
Searches for APIs in the store.

**Parameters:**
- `query` (str): Search query
- `limit` (int): Maximum number of results

**Returns:**
- `List[dict]`: List of matching APIs

**Example:**
```python
results = store.search_apis("image processing", limit=10)
for api in results:
    print(f"{api['name']}: {api['description']}")
```

### Registry API

The `RegistryService` class manages node registration and health monitoring.

#### Class: `RegistryService`

**Location:** `duxnet_registry/services/registry_service.py`

**Methods:**

##### `register_node(node_data: dict) -> str`
Registers a new node in the network.

**Parameters:**
- `node_data` (dict): Node information including ID, address, capabilities

**Returns:**
- `str`: Node registration ID

**Example:**
```python
from duxnet_registry.services.registry_service import RegistryService

registry = RegistryService()
node_id = registry.register_node({
    "node_id": "node_001",
    "ip_address": "192.168.1.100",
    "port": 8000,
    "capabilities": ["api_execution", "task_processing"]
})
```

##### `get_active_nodes() -> List[dict]`
Retrieves all active nodes in the network.

**Returns:**
- `List[dict]`: List of active nodes

**Example:**
```python
active_nodes = registry.get_active_nodes()
print(f"Active nodes: {len(active_nodes)}")
```

### Daemon API

The `DuxOSDaemon` class provides a standardized foundation for system daemons.

#### Class: `DuxOSDaemon`

**Location:** `duxnet_daemon_template/daemon.py`

**Constructor:**
```python
DuxOSDaemon(name: str, config: dict = None)
```

**Methods:**

##### `start()`
Starts the daemon service.

**Example:**
```python
from duxnet_daemon_template.daemon import DuxOSDaemon

class MyDaemon(DuxOSDaemon):
    def run(self):
        # Daemon logic here
        pass

daemon = MyDaemon("my-service")
daemon.start()
```

##### `stop()`
Stops the daemon service.

##### `restart()`
Restarts the daemon service.

---

## CLI Commands

### Wallet CLI

**Location:** `duxnet_wallet_cli/cli.py`

#### Commands:

##### `new-address`
Generates a new wallet address.

```bash
python duxnet_wallet_cli/cli.py new-address
```

**Output:**
```
New address: FLOP1234567890abcdef...
```

##### `balance`
Shows current wallet balance.

```bash
python duxnet_wallet_cli/cli.py balance
```

**Output:**
```
Current balance: 150.75 FLOP
```

##### `send <address> <amount>`
Sends Flopcoin to a specified address.

```bash
python duxnet_wallet_cli/cli.py send FLOP123... 10.5
```

**Output:**
```
Transaction sent successfully
Transaction ID: abc123def456...
```

### Registry CLI

**Location:** `duxnet_registry/cli.py`

#### Commands:

##### `register`
Registers a new node in the network.

```bash
python duxnet_registry/cli.py register --node-id node_001 --ip 192.168.1.100 --port 8000
```

##### `list`
Lists all registered nodes.

```bash
python duxnet_registry/cli.py list
```

##### `update`
Updates node information.

```bash
python duxnet_registry/cli.py update --node-id node_001 --status active
```

##### `deregister`
Removes a node from the registry.

```bash
python duxnet_registry/cli.py deregister --node-id node_001
```

### Store CLI

**Location:** `duxnet_store/main.py`

#### Commands:

##### `--demo`
Runs the store in demo mode with sample data.

```bash
python3 -m duxnet_store.main --demo
```

##### `--config <path>`
Specifies a custom configuration file.

```bash
python3 -m duxnet_store.main --config /path/to/config.yaml
```

##### `--port <port>`
Specifies a custom port.

```bash
python3 -m duxnet_store.main --port 8001
```

---

## REST API Endpoints

### Store Service API

**Base URL:** `http://localhost:8000`

#### Authentication
Most endpoints require no authentication. For protected endpoints, use API key in header:
```
Authorization: Bearer <api_key>
```

#### Endpoints:

##### `GET /api/v1/apis`
List all available APIs.

**Query Parameters:**
- `limit` (int): Maximum number of results (default: 20)
- `offset` (int): Number of results to skip (default: 0)
- `category` (str): Filter by category
- `search` (str): Search query

**Response:**
```json
{
  "apis": [
    {
      "id": "api_001",
      "name": "image_upscale",
      "version": "1.0.0",
      "description": "AI-powered image upscaling",
      "price": 0.1,
      "category": "image_processing",
      "rating": 4.5,
      "reviews_count": 25
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

##### `POST /api/v1/apis`
Register a new API.

**Request Body:**
```json
{
  "name": "text_summarizer",
  "version": "1.0.0",
  "description": "AI text summarization service",
  "price": 0.05,
  "category": "text_processing",
  "endpoint": "https://api.example.com/summarize",
  "documentation": "https://docs.example.com/summarizer"
}
```

**Response:**
```json
{
  "id": "api_002",
  "status": "registered",
  "message": "API registered successfully"
}
```

##### `GET /api/v1/apis/{api_id}`
Get detailed information about a specific API.

**Response:**
```json
{
  "id": "api_001",
  "name": "image_upscale",
  "version": "1.0.0",
  "description": "AI-powered image upscaling",
  "price": 0.1,
  "category": "image_processing",
  "rating": 4.5,
  "reviews_count": 25,
  "endpoint": "https://api.example.com/upscale",
  "documentation": "https://docs.example.com/upscaler",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:45:00Z"
}
```

##### `POST /api/v1/apis/{api_id}/reviews`
Add a review for an API.

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Excellent service, very fast and accurate!"
}
```

### Task Engine API

**Base URL:** `http://localhost:8001`

#### Endpoints:

##### `POST /api/v1/tasks`
Submit a new task for execution.

**Request Body:**
```json
{
  "task_type": "api_call",
  "api_id": "api_001",
  "parameters": {
    "image_url": "https://example.com/image.jpg",
    "scale_factor": 2
  },
  "budget": 0.1
}
```

**Response:**
```json
{
  "task_id": "task_123",
  "status": "submitted",
  "estimated_cost": 0.1,
  "estimated_time": 30
}
```

##### `GET /api/v1/tasks/{task_id}`
Get task status and results.

**Response:**
```json
{
  "task_id": "task_123",
  "status": "completed",
  "result": {
    "upscaled_image_url": "https://example.com/upscaled.jpg"
  },
  "cost": 0.1,
  "execution_time": 25,
  "completed_at": "2024-01-20T15:30:00Z"
}
```

---

## Configuration Schemas

### Wallet Configuration

**File:** `duxnet_wallet/config.yaml`

```yaml
rpc:
  host: "127.0.0.1"
  port: 32553
  user: "flopcoinrpc"
  password: "your_secure_password"

wallet:
  encryption: true
  backup_interval: 3600
  max_transaction_amount: 1000.0
  rate_limit_window: 3600
  max_transactions_per_window: 10
```

### Store Configuration

**File:** `duxnet_store/config.yaml`

```yaml
api:
  host: "0.0.0.0"
  port: 8000
  debug: false
  cors_origins: ["*"]
  rate_limit_per_minute: 100

storage:
  path: "./store_metadata"
  use_ipfs: false
  backup_enabled: true
  backup_interval_hours: 24
  backup_retention_days: 7

rating:
  min_reviews_for_weighted: 5
  recency_weight_days: 30
  confidence_boost_factor: 0.2
  recency_boost_factor: 0.1

search:
  default_limit: 20
  max_limit: 100
  relevance_weights:
    name_match: 10.0
    description_match: 5.0
    tag_match: 3.0
    rating_boost: 0.5
    popularity_boost: 5.0

integration:
  task_engine_url: "http://localhost:8001"
  task_engine_timeout: 30
  wallet_url: "http://localhost:8002"
  wallet_timeout: 10
  registry_url: "http://localhost:8003"
  registry_timeout: 10
  escrow_url: "http://localhost:8004"
  escrow_timeout: 15

security:
  api_key_required: false
  rate_limiting_enabled: true
  content_validation: true
  max_file_size_mb: 10

logging:
  level: "INFO"
  file: "./logs/store.log"
  max_size_mb: 10
  backup_count: 5

performance:
  cache_enabled: true
  cache_ttl_seconds: 300
  max_connections: 100
  connection_timeout: 30
```

### Daemon Configuration

**File:** `duxnet_daemon_template/config.yaml`

```yaml
daemon:
  name: "duxnet-daemon"
  log_level: "INFO"
  heartbeat_interval: 60
  max_retries: 3
  enable_load_balancing: true
  enable_reputation_weighting: true

api:
  host: "0.0.0.0"
  port: 8001
  enable_cors: true
  rate_limit_enabled: true
  rate_limit_requests: 100
  rate_limit_window: 60

services:
  registry:
    url: "http://localhost:8000"
    timeout: 30
    retry_attempts: 3
  
  escrow:
    url: "http://localhost:8002"
    timeout: 30
    retry_attempts: 3
  
  wallet:
    url: "http://localhost:8003"
    timeout: 30
    retry_attempts: 3

security:
  enable_signature_verification: true
  enable_result_encryption: false

monitoring:
  enable_metrics: true
  metrics_port: 9090
  enable_health_checks: true
  health_check_interval: 30

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/duxnet/daemon.log"
  max_size: "10MB"
  backup_count: 5
```

---

## Error Codes

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid parameter provided",
    "details": {
      "field": "price",
      "reason": "Must be a positive number"
    }
  }
}
```

---

## Rate Limiting

Most APIs implement rate limiting to prevent abuse:

- **Default limit:** 100 requests per minute per IP
- **Headers returned:**
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

---

## SDK Examples

### Python SDK

```python
from duxnet_sdk import DuxNetClient

# Initialize client
client = DuxNetClient(
    store_url="http://localhost:8000",
    wallet_url="http://localhost:8002"
)

# Search for APIs
apis = client.store.search_apis("image processing")

# Get wallet balance
balance = client.wallet.get_balance()

# Submit a task
task = client.tasks.submit(
    api_id="api_001",
    parameters={"image_url": "https://example.com/image.jpg"}
)
```

### JavaScript SDK

```javascript
const { DuxNetClient } = require('duxnet-sdk');

// Initialize client
const client = new DuxNetClient({
    storeUrl: 'http://localhost:8000',
    walletUrl: 'http://localhost:8002'
});

// Search for APIs
const apis = await client.store.searchApis('image processing');

// Get wallet balance
const balance = await client.wallet.getBalance();

// Submit a task
const task = await client.tasks.submit({
    apiId: 'api_001',
    parameters: { imageUrl: 'https://example.com/image.jpg' }
});
```

---

For more detailed information about specific modules, see the individual module documentation in their respective directories. 