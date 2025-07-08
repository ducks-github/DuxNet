# Dux OS Daemon Template

A Python template for Dux OS modular daemons (wallet, escrow, airdrop, etc.).

## Features
- Config file loading (YAML)
- Logging to file and console
- Command-line interface: start/stop/status
- PID file management
- Example systemd service file

## Files
- `daemon.py` — Main daemon script
- `config.yaml` — Example configuration
- `daemon.log` — Log file (created at runtime)
- `daemon.pid` — PID file (created at runtime)
- `duxnet-daemon.service` — Example systemd unit file

## Usage

```sh
# Start the daemon (runs in background)
python3 daemon.py start

# Stop the daemon
python3 daemon.py stop

# Check status
python3 daemon.py status
```

## Customization
- Edit `config.yaml` for settings (e.g., heartbeat interval)
- Extend `DuxOSDaemon` class in `daemon.py` for your logic

## systemd Integration
Copy `duxnet-daemon.service` to `/etc/systemd/system/` and edit paths as needed:

```sh
sudo systemctl daemon-reload
sudo systemctl enable duxnet-daemon
sudo systemctl start duxnet-daemon
```

## DuxNetDaemon Example

The `DuxNetDaemon` class (in `daemon.py`) provides a template for building DuxNet peer-to-peer network daemons. It listens on a configurable TCP port (default: 9333) for incoming node connections, similar to how Bitcoin nodes operate.

### Usage

To use the DuxNetDaemon, set the `duxnet_port` option in `config.yaml`:

```yaml
heartbeat_interval: 10  # seconds
duxnet_port: 9333       # TCP port for DuxNet peer-to-peer connections
```

You can extend or instantiate `DuxNetDaemon` in your own daemon scripts to handle peer discovery, messaging, and protocol logic.

### Example

```python
from daemon import DuxNetDaemon, load_config, setup_logging

config = load_config("config.yaml")
setup_logging("daemon.log")
daemon = DuxNetDaemon(config)
daemon.run()
``` 