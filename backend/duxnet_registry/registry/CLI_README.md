# Dux OS Node Registry CLI

## Overview

The `duxnet-node-registry` CLI provides a command-line interface for managing nodes in the Dux OS network. It allows you to register, deregister, list, and update node information easily.

## Installation

Ensure you have the Dux OS project installed. The CLI is included as part of the project's entry points.

## Usage

### Basic Commands

```bash
# Register a new node
duxnet-node-registry register \
    --wallet-address 0x1234... \
    --ip-address 192.168.1.100 \
    --hostname my-node \
    --cpu-cores 4 \
    --memory-gb 16 \
    --storage-gb 500 \
    --gpu-enabled

# Deregister a node
duxnet-node-registry deregister NODE_ID

# List nodes
duxnet-node-registry list \
    --min-reputation 3.0 \
    --only-healthy \
    --min-cpu 4 \
    --min-memory 8 \
    --min-storage 250

# Get node details
duxnet-node-registry get NODE_ID

# Update node health
duxnet-node-registry update-health NODE_ID \
    --load-average 1.5 \
    --memory-usage 50.0 \
    --disk-usage 30.0

# Update node reputation
duxnet-node-registry update-reputation NODE_ID --task-success
```

## Command Reference

### `register`
- `--wallet-address`: (Required) Node's wallet address
- `--ip-address`: (Required) Node's IP address
- `--hostname`: Node's hostname
- `--os-version`: Operating system version
- `--duxnet-version`: Dux OS version
- `--cpu-cores`: Number of CPU cores
- `--memory-gb`: Memory in GB
- `--storage-gb`: Storage in GB
- `--gpu-enabled`: Flag to indicate GPU availability
- `--gpu-model`: GPU model name

### `deregister`
- `NODE_ID`: ID of the node to deregister

### `list`
- `--min-reputation`: Minimum reputation score
- `--only-healthy`: Show only healthy nodes
- `--min-cpu`: Minimum CPU cores
- `--min-memory`: Minimum memory in GB
- `--min-storage`: Minimum storage in GB
- `--min-gpu`: Require GPU availability

### `get`
- `NODE_ID`: Node ID or wallet address to retrieve

### `update-health`
- `NODE_ID`: Node ID to update
- `--load-average`: System load average
- `--memory-usage`: Memory usage percentage
- `--disk-usage`: Disk usage percentage

### `update-reputation`
- `NODE_ID`: Node ID to update
- `--task-success`: Flag to indicate task success

## Configuration

By default, the CLI uses `/var/lib/duxnet/nodes.json` for persistent storage. You can modify this by setting the `DUXOS_NODE_REGISTRY_PATH` environment variable.

## Examples

### Register a High-Performance Node
```bash
duxnet-node-registry register \
    --wallet-address 0x9876... \
    --ip-address 10.0.0.50 \
    --hostname high-performance-node \
    --cpu-cores 16 \
    --memory-gb 64 \
    --storage-gb 2000 \
    --gpu-enabled \
    --gpu-model "NVIDIA RTX 3090"
```

### List Nodes for a Specific Task
```bash
duxnet-node-registry list \
    --min-reputation 4.0 \
    --only-healthy \
    --min-cpu 8 \
    --min-memory 32 \
    --min-gpu
```

## Troubleshooting

- Ensure you have the necessary permissions to read/write the node registry file
- Check that your wallet address and IP address are valid
- Verify network connectivity when updating node health

## Contributing

Contributions to improve the CLI are welcome! Please submit issues or pull requests to the Dux OS project repository.

## License

Part of the Dux OS project. See project LICENSE for details. 