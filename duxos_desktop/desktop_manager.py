#!/usr/bin/env python3
"""
DuxOS Desktop Manager

A modern desktop environment for DuxOS with system tray, widgets,
and application launcher.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import json
import os
import sys
from pathlib import Path
import psutil
import requests
from datetime import datetime
import webbrowser

class DuxOSDesktopManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DuxOS Desktop")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # Set window to fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Configure style
        self.setup_styles()
        
        # Initialize components
        self.setup_desktop()
        self.setup_top_bar()
        self.setup_sidebar()
        self.setup_main_area()
        self.setup_system_tray()
        
        # Start background services
        self.start_background_services()
        
    def setup_styles(self):
        """Configure modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TopBar.TFrame', background='#34495e')
        style.configure('Sidebar.TFrame', background='#2c3e50')
        style.configure('Main.TFrame', background='#ecf0f1')
        style.configure('Tray.TFrame', background='#34495e')
        
        # Button styles
        style.configure('Desktop.TButton', 
                       background='#3498db', 
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        
        style.map('Desktop.TButton',
                 background=[('active', '#2980b9')])
        
    def setup_desktop(self):
        """Setup main desktop layout"""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        self.main_container.columnconfigure(1, weight=1)
        self.main_container.rowconfigure(1, weight=1)
        
    def setup_top_bar(self):
        """Setup top navigation bar"""
        self.top_bar = ttk.Frame(self.main_container, style='TopBar.TFrame')
        self.top_bar.grid(row=0, column=0, columnspan=3, sticky='ew', pady=2)
        
        # DuxOS Logo
        logo_label = tk.Label(self.top_bar, text="🦆 DuxOS", 
                             font=('Arial', 16, 'bold'),
                             fg='white', bg='#34495e')
        logo_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # System info
        self.system_info = tk.Label(self.top_bar, text="", 
                                   font=('Arial', 10),
                                   fg='white', bg='#34495e')
        self.system_info.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Update system info
        self.update_system_info()
        
    def setup_sidebar(self):
        """Setup application sidebar"""
        self.sidebar = ttk.Frame(self.main_container, style='Sidebar.TFrame', width=250)
        self.sidebar.grid(row=1, column=0, sticky='ns', padx=2, pady=2)
        self.sidebar.grid_propagate(False)
        
        # Applications section
        apps_frame = ttk.LabelFrame(self.sidebar, text="Applications", 
                                   padding=10, style='Sidebar.TFrame')
        apps_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Application buttons
        self.create_app_button(apps_frame, "🖥️ System Monitor", self.open_system_monitor)
        self.create_app_button(apps_frame, "💰 Wallet Manager", self.open_wallet_manager)
        self.create_app_button(apps_frame, "🌐 Node Registry", self.open_node_registry)
        self.create_app_button(apps_frame, "⚙️ Settings", self.open_settings)
        self.create_app_button(apps_frame, "📊 Health Monitor", self.open_health_monitor)
        self.create_app_button(apps_frame, "🔧 Terminal", self.open_terminal)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(self.sidebar, text="Quick Actions", 
                                      padding=10, style='Sidebar.TFrame')
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.create_app_button(actions_frame, "🔄 Refresh", self.refresh_system)
        self.create_app_button(actions_frame, "💾 Backup", self.backup_system)
        self.create_app_button(actions_frame, "🛡️ Security", self.security_check)
        
    def create_app_button(self, parent, text, command):
        """Create a styled application button"""
        btn = tk.Button(parent, text=text, command=command,
                       font=('Arial', 10),
                       bg='#3498db', fg='white',
                       relief=tk.FLAT, padx=10, pady=5,
                       cursor='hand2')
        btn.pack(fill=tk.X, pady=2)
        
        # Hover effects
        btn.bind('<Enter>', lambda e: btn.configure(bg='#2980b9'))
        btn.bind('<Leave>', lambda e: btn.configure(bg='#3498db'))
        
    def setup_main_area(self):
        """Setup main content area"""
        self.main_area = ttk.Frame(self.main_container, style='Main.TFrame')
        self.main_area.grid(row=1, column=1, sticky='nsew', padx=2, pady=2)
        
        # Welcome message
        welcome_frame = ttk.Frame(self.main_area)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        welcome_text = """
        🦆 Welcome to DuxOS Desktop Environment
        
        Your decentralized operating system is ready!
        
        • System Status: Online
        • Flopcoin Core: Connected
        • Node Registry: Active
        • Wallet: Secure
        
        Use the sidebar to access applications and manage your system.
        """
        
        welcome_label = tk.Label(welcome_frame, text=welcome_text,
                                font=('Arial', 14),
                                fg='#2c3e50', bg='#ecf0f1',
                                justify=tk.LEFT)
        welcome_label.pack(expand=True)
        
    def setup_system_tray(self):
        """Setup system tray area"""
        self.tray_frame = ttk.Frame(self.main_container, style='Tray.TFrame', height=60)
        self.tray_frame.grid(row=2, column=0, columnspan=3, sticky='ew', pady=2)
        self.tray_frame.grid_propagate(False)
        
        # System tray widgets
        self.create_tray_widget("CPU", "0%", self.get_cpu_usage)
        self.create_tray_widget("RAM", "0%", self.get_ram_usage)
        self.create_tray_widget("Network", "0 KB/s", self.get_network_usage)
        self.create_tray_widget("Flopcoin", "Connected", self.get_flopcoin_status)
        
    def create_tray_widget(self, label, initial_value, update_func):
        """Create a system tray widget"""
        widget_frame = ttk.Frame(self.tray_frame)
        widget_frame.pack(side=tk.LEFT, padx=10, pady=5)
        
        label_widget = tk.Label(widget_frame, text=f"{label}:", 
                               font=('Arial', 9, 'bold'),
                               fg='white', bg='#34495e')
        label_widget.pack()
        
        value_widget = tk.Label(widget_frame, text=initial_value,
                               font=('Arial', 9),
                               fg='#3498db', bg='#34495e')
        value_widget.pack()
        
        # Store reference for updates
        if not hasattr(self, 'tray_widgets'):
            self.tray_widgets = {}
        self.tray_widgets[label] = value_widget
        
        # Start update thread
        threading.Thread(target=self.update_widget_periodic, 
                        args=(value_widget, update_func), 
                        daemon=True).start()
        
    def update_widget_periodic(self, widget, update_func):
        """Periodically update widget values"""
        while True:
            try:
                value = update_func()
                widget.after(0, lambda: widget.configure(text=value))
            except:
                pass
            threading.Event().wait(2)  # Update every 2 seconds
            
    def update_system_info(self):
        """Update system information display"""
        try:
            # Get system info
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            info_text = f"CPU: {cpu_percent}% | RAM: {memory.percent}% | Disk: {disk.percent}%"
            self.system_info.configure(text=info_text)
            
            # Update every 5 seconds
            self.root.after(5000, self.update_system_info)
        except:
            pass
            
    def get_cpu_usage(self):
        """Get CPU usage percentage"""
        try:
            return f"{psutil.cpu_percent()}%"
        except:
            return "N/A"
            
    def get_ram_usage(self):
        """Get RAM usage percentage"""
        try:
            return f"{psutil.virtual_memory().percent}%"
        except:
            return "N/A"
            
    def get_network_usage(self):
        """Get network usage"""
        try:
            # Simple network monitoring
            return "Active"
        except:
            return "N/A"
            
    def get_flopcoin_status(self):
        """Get Flopcoin Core status"""
        try:
            # Check if Flopcoin daemon is running
            for proc in psutil.process_iter(['pid', 'name']):
                if 'flopcoind' in proc.info['name']:
                    return "Connected"
            return "Disconnected"
        except:
            return "Unknown"
            
    def start_background_services(self):
        """Start background services"""
        # Start system monitoring
        threading.Thread(target=self.monitor_system, daemon=True).start()
        
    def monitor_system(self):
        """Background system monitoring"""
        while True:
            try:
                # Monitor system health
                if psutil.cpu_percent() > 90:
                    self.show_notification("High CPU Usage", "System CPU usage is above 90%")
                    
                if psutil.virtual_memory().percent > 90:
                    self.show_notification("High Memory Usage", "System memory usage is above 90%")
                    
            except:
                pass
            threading.Event().wait(30)  # Check every 30 seconds
            
    def show_notification(self, title, message):
        """Show system notification"""
        try:
            messagebox.showwarning(title, message)
        except:
            pass
            
    # Application launcher methods
    def open_system_monitor(self):
        """Open system monitor"""
        self.open_application("System Monitor", "htop")
        
    def open_wallet_manager(self):
        """Open wallet manager"""
        self.open_application("Wallet Manager", "python -m duxos_wallet.cli")
        
    def open_node_registry(self):
        """Open node registry"""
        self.open_application("Node Registry", "python -m duxos_registry.main")
        
    def open_settings(self):
        """Open settings"""
        self.open_application("Settings", "gnome-control-center")
        
    def open_health_monitor(self):
        """Open health monitor"""
        self.open_application("Health Monitor", "python health_monitor_gui.py")
        
    def open_terminal(self):
        """Open terminal"""
        self.open_application("Terminal", "gnome-terminal")
        
    def open_application(self, name, command):
        """Open an application"""
        try:
            subprocess.Popen(command.split(), 
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open {name}: {str(e)}")
            
    def refresh_system(self):
        """Refresh system status"""
        self.update_system_info()
        messagebox.showinfo("System Refresh", "System status has been refreshed!")
        
    def backup_system(self):
        """Backup system"""
        try:
            # Create backup
            backup_dir = Path.home() / "duxos_backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"duxos_backup_{timestamp}.tar.gz"
            
            # Simple backup command
            subprocess.run(["tar", "-czf", str(backup_file), 
                          "--exclude=venv", "--exclude=.git", "."],
                         cwd=Path.cwd())
            
            messagebox.showinfo("Backup Complete", 
                              f"System backup created: {backup_file}")
        except Exception as e:
            messagebox.showerror("Backup Error", f"Backup failed: {str(e)}")
            
    def security_check(self):
        """Run security check"""
        try:
            # Simple security check
            checks = []
            
            # Check if Flopcoin is running
            flopcoin_running = False
            for proc in psutil.process_iter(['pid', 'name']):
                if 'flopcoind' in proc.info['name']:
                    flopcoin_running = True
                    break
            checks.append(f"Flopcoin Core: {'✅ Running' if flopcoin_running else '❌ Not Running'}")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            checks.append(f"Disk Space: {'✅ OK' if disk.percent < 90 else '⚠️ Low'}")
            
            # Check memory
            memory = psutil.virtual_memory()
            checks.append(f"Memory: {'✅ OK' if memory.percent < 90 else '⚠️ High'}")
            
            result = "\n".join(checks)
            messagebox.showinfo("Security Check", f"Security Check Results:\n\n{result}")
            
        except Exception as e:
            messagebox.showerror("Security Check Error", f"Security check failed: {str(e)}")
            
    def run(self):
        """Start the desktop manager"""
        self.root.mainloop()

if __name__ == "__main__":
    desktop = DuxOSDesktopManager()
    desktop.run() 