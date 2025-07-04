# Dux_OS Node Health Monitoring System

A comprehensive health monitoring system for Dux_OS decentralized Linux distribution nodes, featuring anti-sybil protection, dynamic thresholds, scalability optimizations, and real-time GUI integration.

## Features

### Core Health Monitoring
- **Heartbeat System**: Configurable 60-second heartbeats with push/pull models
- **Comprehensive Metrics**: Uptime, load average, memory, CPU, success rate, reputation score
- **Health Thresholds**: Configurable thresholds for load, memory, success rate, and reputation
- **Status Tracking**: Real-time status updates (healthy, unhealthy, offline)

### Anti-Sybil Protection
- **Proof-of-Computation**: Signed task results to verify node activity
- **Rate Limiting**: Configurable rate limits (1 heartbeat/minute per node)
- **Signature Verification**: Ed25519 signatures for all health data
- **Task Result Verification**: Prevents fake nodes from spoofing heartbeats

### Dynamic Thresholds
- **Governance Integration**: Thresholds updated via Dux_OS governance layer
- **Configurable Updates**: Hourly threshold updates from governance endpoint
- **Runtime Adaptation**: System adapts to network-wide policy changes

### Scalability Features
- **Batch Processing**: Bulk processing of health data for large networks
- **IPFS Optimization**: Compression, deduplication, and caching for low latency
- **Connection Pooling**: Efficient database connections and resource management
- **Async Processing**: Non-blocking operations for high throughput

### Error Handling
- **Exponential Backoff**: Intelligent retry logic for failed requests
- **Graceful Degradation**: System continues operating with partial failures
- **Comprehensive Logging**: Structured logging to `/var/log/duxnet/registry.log`
- **Alert System**: Webhook notifications for unhealthy/offline nodes

### GUI Integration
- **Real-time Updates**: WebSocket-based live health data display
- **Filter Options**: Filter by healthy, unhealthy, offline, or all nodes
- **Visual Indicators**: Color-coded status display
- **Responsive Interface**: Modern Tkinter-based GUI

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Health        │    │   Registry      │    │   GUI Client    │
│   Monitor       │◄──►│   API           │◄──►│   (WebSocket)   │
│   Daemon        │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   IPFS/DHT      │    │   SQLite DB     │    │   Task Engine   │
│   Storage       │    │   (Local)       │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Installation

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements_health_monitor.txt

# Create necessary directories
sudo mkdir -p /etc/duxnet /var/log/duxnet /var/lib/duxnet /opt/duxos

# Create duxnet user
sudo useradd -r -s /bin/false duxnet
sudo chown -R duxnet:duxnet /etc/duxnet /var/log/duxnet /var/lib/duxnet
```

### Configuration
1. Copy `registry.yaml` to `/etc/duxnet/registry.yaml`
2. Update configuration with your node details:
   ```yaml
   health_monitor:
     node_id: "your-unique-node-id"
     wallet_address: "your-flop-coin-address"
     ip_address: "your-node-ip"
     port: 8080
   ```

3. Generate cryptographic keys:
   ```bash
   # Generate Ed25519 key pair
   openssl genpkey -algorithm ed25519 -out /etc/duxnet/private_key.pem
   openssl pkey -in /etc/duxnet/private_key.pem -pubout -out /etc/duxnet/public_key.pem
   sudo chown duxnet:duxnet /etc/duxnet/*.pem
   sudo chmod 600 /etc/duxnet/private_key.pem
   ```

### Systemd Service
1. Copy `dux-registryd.service` to `/etc/systemd/system/`
2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable dux-registryd
   sudo systemctl start dux-registryd
   ```

## Usage

### Command Line Interface
```bash
# Start the health monitor daemon
python3 health_monitor.py start --config /etc/duxnet/registry.yaml

# Check daemon status
python3 health_monitor.py status

# Stop the daemon
python3 health_monitor.py stop
```

### GUI Client
```bash
# Start the GUI client
python3 health_monitor_gui.py
```

### API Endpoints
The health monitor integrates with the registry API:

- `POST /nodes/health` - Send heartbeat with health data
- `GET /nodes/{node_id}/health` - Poll node health (registry-side)
- `GET /nodes/` - List all nodes with health status

## Configuration Reference

### Health Monitor Settings
```yaml
health_monitor:
  heartbeat_interval: 60          # Heartbeat frequency in seconds
  max_missed_heartbeats: 3        # Missed heartbeats before unhealthy
  poll_interval: 300              # Registry polling interval
  retry_attempts: 2               # Number of retry attempts
  retry_interval: 30              # Retry interval in seconds
  health_history_retention: 604800 # 7 days retention in seconds
```

### Thresholds
```yaml
thresholds:
  load_average: 0.8               # Maximum load average
  min_memory_mb: 512              # Minimum available memory (MB)
  min_success_rate: 0.9           # Minimum task success rate
  min_reputation_score: 0.5       # Minimum reputation score
```

### Anti-Sybil Protection
```yaml
anti_sybil:
  proof_of_computation_required: true
  task_result_verification: true
  signature_verification: true
  rate_limiting:
    max_heartbeats_per_minute: 1
    max_requests_per_minute: 60
```

### Scalability
```yaml
scalability:
  batch_processing:
    enabled: true
    batch_size: 100
    batch_timeout: 5
  ipfs_optimization:
    compression: true
    deduplication: true
    cache_size_mb: 100
```

## Security Features

### Cryptographic Signatures
- All health data is signed with Ed25519 private keys
- Signatures are verified by the registry
- Prevents tampering and ensures data integrity

### Rate Limiting
- Prevents spam and DoS attacks
- Configurable limits per node
- Automatic blocking of excessive requests

### Proof-of-Computation
- Nodes must provide signed task results
- Verifies actual computational work
- Prevents fake nodes from joining the network

### Secure Storage
- Private keys stored with restricted permissions
- Health data encrypted in transit
- IPFS provides decentralized, tamper-resistant storage

## Monitoring and Logging

### Log Files
- Primary log: `/var/log/duxnet/registry.log`
- Structured JSON logging for easy parsing
- Configurable log levels and rotation

### Metrics Collection
- System metrics via `psutil`
- Task execution success rates
- Reputation scores from reputation system
- Network connectivity status

### Alert System
- Webhook notifications for status changes
- Configurable alert thresholds
- Integration with external monitoring systems

## Troubleshooting

### Common Issues

1. **Daemon won't start**
   - Check configuration file permissions
   - Verify cryptographic keys exist
   - Check log files for errors

2. **Heartbeats failing**
   - Verify network connectivity
   - Check rate limiting settings
   - Ensure registry endpoint is accessible

3. **GUI not connecting**
   - Verify WebSocket server is running
   - Check firewall settings
   - Ensure websockets library is installed

### Debug Mode
Enable debug logging by setting log level to DEBUG in configuration:
```yaml
logging:
  level: "DEBUG"
```

### Health Checks
```bash
# Check daemon status
sudo systemctl status dux-registryd

# View recent logs
sudo journalctl -u dux-registryd -f

# Check database
sqlite3 /var/lib/duxnet/health_monitor.db "SELECT * FROM health_history ORDER BY timestamp DESC LIMIT 10;"
```

## Development

### Adding New Metrics
1. Extend the `NodeMetrics` dataclass
2. Update the `collect_metrics()` method
3. Add corresponding thresholds in configuration
4. Update health evaluation logic

### Custom Alert Handlers
Implement custom alert handlers by extending the alert system:
```python
class CustomAlertHandler:
    def send_alert(self, node_id: str, status: str, metrics: Dict):
        # Custom alert logic
        pass
```

### Integration with Task Engine
The health monitor integrates with the task engine for:
- Success rate calculation
- Proof-of-computation generation
- Task result verification

## Performance Considerations

### Optimization Tips
- Use batch processing for large networks
- Enable IPFS compression and caching
- Configure appropriate database connection pools
- Monitor memory usage and adjust cache sizes

### Scaling Guidelines
- For networks > 1000 nodes: Enable batch processing
- For high-frequency updates: Increase batch sizes
- For low-latency requirements: Optimize IPFS settings
- For high availability: Use multiple registry instances

## Contributing

1. Follow Dux_OS coding standards
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure security best practices are followed

## License

This project is part of Dux_OS and follows the same licensing terms. 