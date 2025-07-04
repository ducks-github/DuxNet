#!/usr/bin/env python3
"""
DuxOS Desktop Environment Setup

This script installs and configures a desktop environment for DuxOS.
"""

import os
import subprocess
import sys
from pathlib import Path

class DuxOSDesktopSetup:
    def __init__(self):
        self.desktop_packages = [
            "xfce4",
            "xfce4-goodies",
            "lightdm",
            "lightdm-gtk-greeter",
            "python3-tk",
            "python3-psutil",
            "python3-requests",
            "htop",
            "gnome-terminal",
            "gnome-control-center",
            "file-roller",
            "gthumb",
            "firefox",
            "vlc"
        ]
        
    def check_system(self):
        """Check system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check if running as root
        if os.geteuid() == 0:
            print("✅ Running with root privileges")
        else:
            print("⚠️ Not running as root. Some operations may require sudo.")
            
        # Check Python version
        if sys.version_info >= (3, 8):
            print("✅ Python 3.8+ detected")
        else:
            print("❌ Python 3.8+ required")
            return False
            
        # Check if we're on a supported system
        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read().lower()
                if 'ubuntu' in content or 'debian' in content:
                    print("✅ Ubuntu/Debian system detected")
                else:
                    print("⚠️ System may not be fully supported")
        except:
            print("⚠️ Could not detect system type")
            
        return True
        
    def install_desktop_packages(self):
        """Install desktop environment packages"""
        print("\n📦 Installing desktop environment packages...")
        
        try:
            # Update package list
            print("   Updating package list...")
            subprocess.run(["apt", "update"], check=True)
            
            # Install packages
            print("   Installing XFCE and desktop packages...")
            subprocess.run(["apt", "install", "-y"] + self.desktop_packages, check=True)
            
            print("✅ Desktop packages installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
            
    def configure_desktop_manager(self):
        """Configure DuxOS desktop manager"""
        print("\n⚙️ Configuring DuxOS desktop manager...")
        
        try:
            # Create desktop manager directory
            desktop_dir = Path("/opt/duxos/desktop")
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy desktop manager
            source_file = Path("duxos_desktop/desktop_manager.py")
            if source_file.exists():
                dest_file = desktop_dir / "desktop_manager.py"
                with open(source_file, 'r') as src:
                    with open(dest_file, 'w') as dst:
                        dst.write(src.read())
                
                # Make executable
                os.chmod(dest_file, 0o755)
                print("✅ Desktop manager installed")
            else:
                print("⚠️ Desktop manager source not found")
                
            # Create desktop entry
            desktop_entry = f"""[Desktop Entry]
Name=DuxOS Desktop
Comment=DuxOS Desktop Environment
Exec=python3 {dest_file}
Icon=computer
Terminal=false
Type=Application
Categories=System;
"""
            
            desktop_file = Path("/usr/share/applications/duxos-desktop.desktop")
            with open(desktop_file, 'w') as f:
                f.write(desktop_entry)
                
            print("✅ Desktop entry created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure desktop manager: {e}")
            return False
            
    def setup_autostart(self):
        """Setup autostart for DuxOS services"""
        print("\n🚀 Setting up autostart services...")
        
        try:
            # Create autostart directory
            autostart_dir = Path.home() / ".config/autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            
            # Create autostart entries
            autostart_entries = [
                ("duxos-desktop.desktop", f"""[Desktop Entry]
Name=DuxOS Desktop
Comment=DuxOS Desktop Environment
Exec=python3 /opt/duxos/desktop/desktop_manager.py
Icon=computer
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
"""),
                ("duxos-flopcoin.desktop", f"""[Desktop Entry]
Name=Flopcoin Core
Comment=Flopcoin Core Daemon
Exec=flopcoind -daemon
Icon=network-server
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
"""),
                ("duxos-registry.desktop", f"""[Desktop Entry]
Name=DuxOS Registry
Comment=DuxOS Node Registry
Exec=python3 -m duxos_registry.main
Icon=network-workgroup
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
""")
            ]
            
            for filename, content in autostart_entries:
                autostart_file = autostart_dir / filename
                with open(autostart_file, 'w') as f:
                    f.write(content)
                    
            print("✅ Autostart services configured")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup autostart: {e}")
            return False
            
    def configure_display_manager(self):
        """Configure display manager"""
        print("\n🖥️ Configuring display manager...")
        
        try:
            # Enable lightdm
            subprocess.run(["systemctl", "enable", "lightdm"], check=True)
            print("✅ LightDM enabled")
            
            # Configure lightdm
            lightdm_config = """[SeatDefaults]
greeter-session=lightdm-gtk-greeter
user-session=xfce
autologin-user=duck
autologin-user-timeout=0
"""
            
            config_file = Path("/etc/lightdm/lightdm.conf.d/50-duxos.conf")
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                f.write(lightdm_config)
                
            print("✅ Display manager configured")
            return True
            
        except Exception as e:
            print(f"❌ Failed to configure display manager: {e}")
            return False
            
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts"""
        print("\n📋 Creating desktop shortcuts...")
        
        try:
            desktop_dir = Path.home() / "Desktop"
            desktop_dir.mkdir(exist_ok=True)
            
            shortcuts = [
                ("DuxOS Desktop.desktop", f"""[Desktop Entry]
Name=DuxOS Desktop
Comment=DuxOS Desktop Environment
Exec=python3 /opt/duxos/desktop/desktop_manager.py
Icon=computer
Terminal=false
Type=Application
Categories=System;
"""),
                ("Wallet Manager.desktop", f"""[Desktop Entry]
Name=Wallet Manager
Comment=DuxOS Wallet Manager
Exec=python3 -m duxos_wallet.cli
Icon=wallet
Terminal=true
Type=Application
Categories=Office;
"""),
                ("Node Registry.desktop", f"""[Desktop Entry]
Name=Node Registry
Comment=DuxOS Node Registry
Exec=python3 -m duxos_registry.main
Icon=network-workgroup
Terminal=true
Type=Application
Categories=Network;
"""),
                ("Health Monitor.desktop", f"""[Desktop Entry]
Name=Health Monitor
Comment=DuxOS Health Monitor
Exec=python3 health_monitor_gui.py
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=System;
""")
            ]
            
            for filename, content in shortcuts:
                shortcut_file = desktop_dir / filename
                with open(shortcut_file, 'w') as f:
                    f.write(content)
                os.chmod(shortcut_file, 0o755)
                
            print("✅ Desktop shortcuts created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create shortcuts: {e}")
            return False
            
    def setup_wallpaper(self):
        """Setup DuxOS wallpaper"""
        print("\n🖼️ Setting up DuxOS wallpaper...")
        
        try:
            # Create wallpaper directory
            wallpaper_dir = Path("/usr/share/backgrounds/duxos")
            wallpaper_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple DuxOS wallpaper (text-based for now)
            wallpaper_content = """# DuxOS Wallpaper
# This would be replaced with an actual image file
# For now, we'll use a solid color background
"""
            
            wallpaper_file = wallpaper_dir / "duxos-wallpaper.txt"
            with open(wallpaper_file, 'w') as f:
                f.write(wallpaper_content)
                
            print("✅ Wallpaper directory created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup wallpaper: {e}")
            return False
            
    def create_user_guide(self):
        """Create user guide"""
        print("\n📖 Creating user guide...")
        
        try:
            guide_content = """# DuxOS Desktop User Guide

## Welcome to DuxOS Desktop Environment!

### Getting Started
1. **Desktop Manager**: The main interface for managing your DuxOS system
2. **Applications**: Access all DuxOS applications from the sidebar
3. **System Tray**: Monitor system resources and Flopcoin status
4. **Quick Actions**: Perform common system tasks

### Applications
- **System Monitor**: Monitor CPU, RAM, and system performance
- **Wallet Manager**: Manage your Flopcoin wallet
- **Node Registry**: Access the DuxOS node registry
- **Health Monitor**: Monitor system and network health
- **Terminal**: Access command line interface
- **Settings**: Configure system settings

### Quick Actions
- **Refresh**: Update system status
- **Backup**: Create system backup
- **Security**: Run security check

### Keyboard Shortcuts
- `Ctrl+Alt+T`: Open terminal
- `Ctrl+Alt+Delete`: System menu
- `F11`: Toggle fullscreen
- `Alt+F4`: Close application

### Support
- Documentation: /opt/duxos/docs
- Issues: https://github.com/ducks-github/Dux_OS/issues

---
DuxOS Desktop Environment v2.2.0
"""
            
            guide_file = Path("/opt/duxos/docs/user-guide.md")
            guide_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(guide_file, 'w') as f:
                f.write(guide_content)
                
            print("✅ User guide created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create user guide: {e}")
            return False
            
    def setup_complete(self):
        """Complete setup"""
        print("\n🎉 DuxOS Desktop Environment Setup Complete!")
        print("\n📋 Summary:")
        print("   ✅ Desktop packages installed")
        print("   ✅ Desktop manager configured")
        print("   ✅ Autostart services setup")
        print("   ✅ Display manager configured")
        print("   ✅ Desktop shortcuts created")
        print("   ✅ Wallpaper setup")
        print("   ✅ User guide created")
        
        print("\n🚀 Next Steps:")
        print("   1. Restart your system")
        print("   2. Login to DuxOS Desktop")
        print("   3. Use the sidebar to access applications")
        print("   4. Check the system tray for status")
        
        print("\n💡 Tips:")
        print("   - Press F11 to toggle fullscreen")
        print("   - Use Ctrl+Alt+T for terminal access")
        print("   - Check the user guide for more information")
        
    def run(self):
        """Run the complete setup"""
        print("🚀 DuxOS Desktop Environment Setup")
        print("=" * 50)
        
        if not self.check_system():
            print("❌ System requirements not met")
            return False
            
        steps = [
            ("Installing desktop packages", self.install_desktop_packages),
            ("Configuring desktop manager", self.configure_desktop_manager),
            ("Setting up autostart", self.setup_autostart),
            ("Configuring display manager", self.configure_display_manager),
            ("Creating desktop shortcuts", self.create_desktop_shortcuts),
            ("Setting up wallpaper", self.setup_wallpaper),
            ("Creating user guide", self.create_user_guide)
        ]
        
        for step_name, step_func in steps:
            print(f"\n🔄 {step_name}...")
            if not step_func():
                print(f"❌ {step_name} failed")
                return False
                
        self.setup_complete()
        return True

def main():
    setup = DuxOSDesktopSetup()
    success = setup.run()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("🔄 Please restart your system to apply changes.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 