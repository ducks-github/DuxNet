import subprocess
import sys
import os
import time
import signal

# List of (script, args) for each service
SERVICES = [
    ("duxnet_store/main.py", ["--config", "duxnet_store/config.yaml"]),
    ("duxnet_wallet/main.py", ["--config", "duxnet_wallet/config.yaml"]),
    ("duxos_escrow/escrow_service.py", []),
    ("duxnet_registry/main.py", ["--config", "duxnet_registry/config.yaml"]),
    # Add more services as needed
    # ("duxos_tasks/main.py", ["--config", "duxos_tasks/config.yaml"]),
]

DESKTOP_GUI = ("duxnet_desktop/desktop_manager.py", [])

def start_service(script, args):
    # Use sys.executable to ensure the right Python is used
    return subprocess.Popen([sys.executable, script] + args)

def main():
    procs = []
    print("Starting DuxNet core services...")
    for script, args in SERVICES:
        if not os.path.exists(script):
            print(f"Warning: {script} not found, skipping.")
            continue
        print(f"Launching {script}...")
        procs.append(start_service(script, args))
        time.sleep(1)  # Stagger startup

    # Optionally, start the Desktop GUI
    if os.path.exists(DESKTOP_GUI[0]):
        print("Launching Desktop GUI...")
        gui_proc = start_service(DESKTOP_GUI[0], DESKTOP_GUI[1])
        procs.append(gui_proc)
    else:
        print("Desktop GUI not found, skipping.")

    print("All DuxNet services started. Press Ctrl+C to stop everything.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down all DuxNet services...")
        for proc in procs:
            proc.terminate()
        for proc in procs:
            proc.wait()
        print("All services stopped.")

if __name__ == "__main__":
    main() 