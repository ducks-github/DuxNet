# Wallet System Integration (Phase 2.2)

## Overview

The Wallet System Integration extends the DuxOS Node Registry with comprehensive blockchain wallet functionality, enabling nodes to create wallets, manage balances, send transactions, and interact with the Flopcoin blockchain.

## Features

### Core Wallet Functionality
- **Wallet Creation**: Create Flopcoin wallets for registered nodes
- **Balance Management**: Check wallet balances in real-time
- **Transaction Sending**: Send Flopcoin transactions to other addresses
- **Address Generation**: Generate new addresses for existing wallets
- **Transaction History**: View complete transaction history for wallets

### Security & Integration
- **Node Authentication**: All wallet operations require node authentication
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Registry Integration**: Seamless integration with existing node registry
- **Database Persistence**: All wallet data stored in database
- **RPC Integration**: Direct integration with Flopcoin Core RPC

## Architecture

### Components

1. **WalletService** (`duxos_registry/services/wallet_service.py`)
   - Core wallet business logic
   - RPC communication with Flopcoin Core
   - Authentication and security
   - Rate limiting and validation

2. **Database Models** (`duxos_registry/models/database_models.py`)
   - `Wallet`: Wallet information and metadata
   - `Transaction`: Transaction records and history
   - `WalletCapability`: Node wallet capability tracking

3. **Repository Layer** (`duxos_registry/db/repository.py`)
   - `WalletRepository`: Wallet CRUD operations
   - `TransactionRepository`: Transaction management

4. **API Layer** (`duxos_registry/api/wallet_routes.py`)
   - RESTful endpoints for wallet operations
   - Request/response validation
   - Error handling

## API Endpoints

### Wallet Management

#### Create Wallet
```http
POST /wallet/create
```

**Request Body:**
```json
{
  "node_id": "node_001",
  "wallet_name": "my_wallet",
  "auth_data": {
    "signature": "abc123...",
    "timestamp": 1640995200
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Wallet my_wallet created successfully",
  "wallet": {
    "id": 1,
    "node_id": "node_001",
    "wallet_name": "my_wallet",
    "address": "FLOP123456789abcdef",
    "wallet_type": "flopcoin",
    "balance": 0.0,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Get Wallet Information
```http
GET /wallet/{node_id}
```

**Response:**
```json
{
  "id": 1,
  "node_id": "node_001",
  "wallet_name": "my_wallet",
  "address": "FLOP123456789abcdef",
  "wallet_type": "flopcoin",
  "balance": 150.75,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

#### Get Wallet Balance
```http
GET /wallet/{node_id}/balance
```

**Response:**
```json
{
  "success": true,
  "node_id": "node_001",
  "wallet_name": "my_wallet",
  "address": "FLOP123456789abcdef",
  "balance": 150.75,
  "currency": "FLOP"
}
```

### Transaction Operations

#### Send Transaction
```http
POST /wallet/{node_id}/send
```

**Request Body:**
```json
{
  "node_id": "node_001",
  "recipient_address": "FLOP987654321fedcba",
  "amount": 50.0,
  "auth_data": {
    "signature": "abc123...",
    "timestamp": 1640995200
  }
}
```

**Response:**
```json
{
  "success": true,
  "txid": "txid123456789",
  "amount": 50.0,
  "recipient": "FLOP987654321fedcba",
  "transaction": {
    "id": 1,
    "wallet_id": 1,
    "txid": "txid123456789",
    "recipient_address": "FLOP987654321fedcba",
    "amount": 50.0,
    "transaction_type": "send",
    "status": "confirmed",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

#### Get Transaction History
```http
GET /wallet/{node_id}/transactions?limit=50
```

**Response:**
```json
{
  "success": true,
  "node_id": "node_001",
  "wallet_name": "my_wallet",
  "transactions": [
    {
      "id": 1,
      "wallet_id": 1,
      "txid": "txid123456789",
      "recipient_address": "FLOP987654321fedcba",
      "amount": 50.0,
      "transaction_type": "send",
      "status": "confirmed",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Address Management

#### Generate New Address
```http
POST /wallet/{node_id}/new-address
```

**Response:**
```json
{
  "success": true,
  "node_id": "node_001",
  "new_address": "FLOPnewaddress123",
  "wallet_name": "my_wallet"
}
```

### Health Check
```http
GET /wallet/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "wallet",
  "version": "1.0.0"
}
```

## Configuration

### Wallet Configuration
The wallet service uses the configuration from `duxos/wallet/config.yaml`:

```yaml
rpc:
  host: 127.0.0.1
  port: 32553
  user: flopcoinrpc
  password: your_secure_password
wallet:
  encryption: true
  backup_interval: 3600
  max_transaction_amount: 1000.0
  rate_limit_window: 3600
  max_transactions_per_window: 10
logging:
  level: INFO
  file: /var/log/duxnet/wallet.log
```

### Security Settings
- `max_transaction_amount`: Maximum amount per transaction (default: 1000.0 FLOP)
- `rate_limit_window`: Time window for rate limiting in seconds (default: 3600)
- `max_transactions_per_window`: Maximum transactions per time window (default: 10)

## Database Schema

### Wallet Table
```sql
CREATE TABLE wallets (
    id INTEGER PRIMARY KEY,
    node_id VARCHAR NOT NULL UNIQUE,
    wallet_name VARCHAR NOT NULL,
    address VARCHAR NOT NULL,
    wallet_type VARCHAR DEFAULT 'flopcoin',
    balance FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Transaction Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    wallet_id INTEGER NOT NULL,
    txid VARCHAR NOT NULL UNIQUE,
    recipient_address VARCHAR NOT NULL,
    amount FLOAT NOT NULL,
    transaction_type VARCHAR DEFAULT 'send',
    status VARCHAR DEFAULT 'pending',
    fee FLOAT DEFAULT 0.0,
    block_height INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP
);
```

## Usage Examples

### Python Client Example
```python
import requests
import json

# Base URL for the registry
BASE_URL = "http://localhost:8000"

# Create a wallet for a node
def create_wallet(node_id, wallet_name):
    url = f"{BASE_URL}/wallet/create"
    data = {
        "node_id": node_id,
        "wallet_name": wallet_name
    }
    response = requests.post(url, json=data)
    return response.json()

# Get wallet balance
def get_balance(node_id):
    url = f"{BASE_URL}/wallet/{node_id}/balance"
    response = requests.get(url)
    return response.json()

# Send transaction
def send_transaction(node_id, recipient, amount):
    url = f"{BASE_URL}/wallet/{node_id}/send"
    data = {
        "node_id": node_id,
        "recipient_address": recipient,
        "amount": amount
    }
    response = requests.post(url, json=data)
    return response.json()

# Example usage
if __name__ == "__main__":
    # Create wallet
    result = create_wallet("node_001", "my_wallet")
    print(f"Wallet created: {result}")
    
    # Check balance
    balance = get_balance("node_001")
    print(f"Balance: {balance}")
    
    # Send transaction
    tx_result = send_transaction("node_001", "FLOP987654321fedcba", 10.0)
    print(f"Transaction: {tx_result}")
```

### cURL Examples

#### Create Wallet
```bash
curl -X POST "http://localhost:8000/wallet/create" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node_001",
    "wallet_name": "my_wallet"
  }'
```

#### Get Balance
```bash
curl -X GET "http://localhost:8000/wallet/node_001/balance"
```

#### Send Transaction
```bash
curl -X POST "http://localhost:8000/wallet/node_001/send" \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node_001",
    "recipient_address": "FLOP987654321fedcba",
    "amount": 10.0
  }'
```

## Error Handling

### Common Error Responses

#### Authentication Failed
```json
{
  "success": false,
  "message": "Authentication failed"
}
```

#### Wallet Not Found
```json
{
  "success": false,
  "message": "No wallet found for node node_001"
}
```

#### Insufficient Balance
```json
{
  "success": false,
  "message": "Insufficient balance"
}
```

#### Rate Limit Exceeded
```json
{
  "success": false,
  "message": "Rate limit exceeded. Maximum 10 transactions per 3600 seconds"
}
```

#### Invalid Amount
```json
{
  "success": false,
  "message": "Invalid amount"
}
```

## Testing

### Running Tests
```bash
# Run wallet integration tests
pytest tests/test_wallet_integration.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage
The wallet integration includes comprehensive tests for:
- Wallet service functionality
- API endpoint validation
- Error handling
- Database operations
- RPC integration (mocked)
- Authentication and security

## Security Considerations

### Authentication
- All wallet operations require node authentication
- Authentication data must be provided in requests
- Failed authentication results in operation rejection

### Rate Limiting
- Built-in rate limiting prevents abuse
- Configurable limits per time window
- Automatic rejection of excessive requests

### Input Validation
- All inputs are validated before processing
- Amount validation (positive numbers only)
- Address format validation
- Node ID validation

### Database Security
- SQL injection protection through ORM
- Transaction rollback on errors
- Proper error handling and logging

## Integration with Registry

### Node Capabilities
When a wallet is created for a node, the "wallet" capability is automatically added to the node's capabilities list.

### P2P Integration
The wallet system integrates with the existing P2P protocol:
- Wallet information can be shared via P2P messages
- Transaction notifications can be broadcast
- Balance updates can be synchronized

### Health Monitoring
Wallet health is integrated with the overall node health monitoring:
- Wallet status affects node health score
- Transaction success/failure impacts reputation
- Balance monitoring for suspicious activity

## Future Enhancements

### Planned Features
1. **Multi-Currency Support**: Support for additional cryptocurrencies
2. **Smart Contracts**: Integration with smart contract functionality
3. **DeFi Integration**: Support for DeFi protocols and yield farming
4. **Advanced Analytics**: Transaction analytics and reporting
5. **Mobile Support**: Mobile wallet integration
6. **Hardware Wallet Support**: Integration with hardware wallets

### Performance Optimizations
1. **Caching**: Redis-based caching for frequently accessed data
2. **Async Processing**: Background processing for transaction updates
3. **Connection Pooling**: Optimized database connection management
4. **Load Balancing**: Support for multiple wallet service instances

## Troubleshooting

### Common Issues

#### RPC Connection Failed
- Check Flopcoin Core is running
- Verify RPC credentials in config
- Ensure firewall allows RPC connections

#### Database Errors
- Check database connection
- Verify table schema is up to date
- Check database permissions

#### Authentication Issues
- Verify node authentication is properly configured
- Check authentication data format
- Ensure node exists in registry

### Logs
Wallet service logs are written to:
- File: `/var/log/duxnet/wallet.log`
- Console: Standard output
- Level: INFO (configurable)

### Monitoring
Monitor wallet service health via:
- Health check endpoint: `/wallet/health`
- Database connection status
- RPC connection status
- Transaction success rates

## Support

For issues and questions:
1. Check the logs for error details
2. Review the configuration settings
3. Run the test suite to verify functionality
4. Consult the API documentation
5. Open an issue in the project repository 