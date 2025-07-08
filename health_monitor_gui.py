#!/usr/bin/env python3
"""
Dux_OS Health Monitor GUI Client
A simple GUI client for displaying real-time node health information.
"""

import asyncio
import json
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Dict, List

# Optional import for websockets
try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("Warning: websockets library not available, GUI will not function")


class HealthMonitorGUI:
    """Simple GUI client for health monitor WebSocket integration"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Dux_OS Health Monitor")
        self.root.geometry("800x600")

        # WebSocket connection
        self.websocket = None
        self.connected = False
        self.ws_url = "ws://localhost:8080/ws"

        # Data storage
        self.health_data = {}
        self.filter_type = "all"

        self.setup_ui()
        if WEBSOCKETS_AVAILABLE:
            self.connect_websocket()
        else:
            self.status_label.config(text="WebSockets not available", foreground="orange")

    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Connection status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.status_label = ttk.Label(status_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=0, sticky="w")

        # Filter controls
        filter_frame = ttk.LabelFrame(main_frame, text="Filter Options", padding="5")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        filter_options = ["all", "healthy", "unhealthy", "offline"]
        self.filter_var = tk.StringVar(value="all")

        for i, option in enumerate(filter_options):
            ttk.Radiobutton(
                filter_frame,
                text=option.title(),
                variable=self.filter_var,
                value=option,
                command=self.on_filter_change,
            ).grid(row=0, column=i, padx=10)

        # Health data display
        data_frame = ttk.LabelFrame(main_frame, text="Node Health Status", padding="5")
        data_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        # Treeview for health data
        columns = (
            "Node ID",
            "Status",
            "Uptime",
            "Load",
            "Memory",
            "CPU",
            "Success Rate",
            "Last Update",
        )
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)

        # Refresh button
        refresh_btn = ttk.Button(main_frame, text="Refresh", command=self.refresh_data)
        refresh_btn.grid(row=3, column=0, columnspan=2, pady=(10, 0))

    def connect_websocket(self):
        """Connect to WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            return

        def run_websocket():
            asyncio.run(self.websocket_client())

        self.ws_thread = threading.Thread(target=run_websocket, daemon=True)
        self.ws_thread.start()

    async def websocket_client(self):
        """WebSocket client for real-time updates"""
        while True:
            try:
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    self.root.after(0, self.update_status, "Connected", "green")

                    # Send initial filter request
                    await websocket.send(
                        json.dumps({"type": "filter_request", "filter": self.filter_type})
                    )

                    # Listen for messages
                    async for message in websocket:
                        data = json.loads(message)
                        if data.get("type") == "health_update":
                            self.root.after(0, self.handle_health_update, data["data"])
                        elif data.get("type") == "filter_response":
                            self.root.after(0, self.handle_filter_response, data["data"])

            except Exception as e:
                self.connected = False
                self.root.after(0, self.update_status, f"Disconnected: {e}", "red")
                await asyncio.sleep(5)  # Retry after 5 seconds

    def update_status(self, text: str, color: str):
        """Update connection status"""
        self.status_label.config(text=text, foreground=color)

    def on_filter_change(self):
        """Handle filter change"""
        self.filter_type = self.filter_var.get()
        if self.connected and self.websocket and WEBSOCKETS_AVAILABLE:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(
                    json.dumps({"type": "filter_request", "filter": self.filter_type})
                ),
                asyncio.get_event_loop(),
            )

    def handle_health_update(self, health_data: Dict[str, Any]):
        """Handle real-time health update"""
        node_id = health_data["node_id"]
        self.health_data[node_id] = health_data
        self.update_treeview()

    def handle_filter_response(self, data: List[Dict[str, Any]]):
        """Handle filter response"""
        self.health_data.clear()
        for item in data:
            self.health_data[item["node_id"]] = item
        self.update_treeview()

    def update_treeview(self):
        """Update the treeview with current health data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add filtered items
        for node_id, data in self.health_data.items():
            if self.filter_type == "all" or data["status"] == self.filter_type:
                metrics = data.get("metrics", {})

                # Format uptime
                uptime_seconds = metrics.get("uptime", 0)
                uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m"

                # Format load average
                load_avg = metrics.get("load_average", [0, 0, 0])
                load_str = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"

                # Format memory
                memory_mb = metrics.get("available_memory", 0)
                memory_str = f"{memory_mb} MB"

                # Format success rate
                success_rate = metrics.get("success_rate", 0)
                success_str = f"{success_rate:.1%}"

                # Format timestamp
                timestamp = data.get("last_heartbeat", "")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = timestamp
                else:
                    time_str = "Unknown"

                # Set row color based on status
                tags = (data["status"],)

                self.tree.insert(
                    "",
                    "end",
                    values=(
                        node_id[:8] + "...",  # Truncate node ID
                        data["status"].title(),
                        uptime_str,
                        load_str,
                        memory_str,
                        metrics.get("available_cpu", 0),
                        success_str,
                        time_str,
                    ),
                    tags=tags,
                )

        # Configure row colors
        self.tree.tag_configure("healthy", background="lightgreen")
        self.tree.tag_configure("unhealthy", background="lightcoral")
        self.tree.tag_configure("offline", background="lightgray")

    def refresh_data(self):
        """Refresh data from server"""
        if self.connected and self.websocket and WEBSOCKETS_AVAILABLE:
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(
                    json.dumps({"type": "filter_request", "filter": self.filter_type})
                ),
                asyncio.get_event_loop(),
            )
        else:
            messagebox.showwarning("Connection Error", "Not connected to health monitor server")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = HealthMonitorGUI(root)

    # Handle window close
    def on_closing():
        if app.websocket and WEBSOCKETS_AVAILABLE:
            asyncio.run_coroutine_threadsafe(app.websocket.close(), asyncio.get_event_loop())
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
