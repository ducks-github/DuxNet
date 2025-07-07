#!/bin/bash

# Simplified Dux_OS Build Script with Theme Customizations
# This script builds Dux_OS with all theme customizations included

# Check if the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (e.g., using sudo)."
  exit 1
fi

echo "=== Dux_OS Build with Theme Customizations ==="
echo

# Get the directory of the script
SCRIPT_DIR=$(dirname "$0")
WORK_DIR="$SCRIPT_DIR/build-workspace"
ISO_OUTPUT="$SCRIPT_DIR/Dux_OS.iso"

# Ensure working directory exists
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "1. Installing required packages..."
apt update
apt install -y live-build debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin

echo "2. Configuring live-build..."
lb config --distribution bookworm --debian-installer live --architectures amd64 \
  --archive-areas "main contrib non-free" \
  --mirror-bootstrap http://deb.debian.org/debian/ \
  --mirror-chroot http://deb.debian.org/debian/ \
  --mirror-binary http://deb.debian.org/debian/ \
  --mirror-binary-security http://security.debian.org/debian-security/ \
  --initramfs live-boot

echo "3. Setting up package lists..."
mkdir -p config/package-lists
echo "task-xfce-desktop" > config/package-lists/desktop.list.chroot

# Add theme packages
cat > config/package-lists/theme-packages.list.chroot << 'EOF'
lightdm
lightdm-gtk-greeter
lightdm-gtk-greeter-settings
xfce4-settings
xfce4-appfinder
xfce4-panel
xfce4-session
xfce4-terminal
# xfce4-volumed
xfce4-power-manager
xfce4-notifyd
xfce4-screenshooter
xfce4-taskmanager
xfce4-whiskermenu-plugin
xfce4-datetime-plugin
xfce4-cpufreq-plugin
xfce4-cpugraph-plugin
xfce4-diskperf-plugin
xfce4-fsguard-plugin
xfce4-genmon-plugin
xfce4-indicator-plugin
xfce4-mailwatch-plugin
xfce4-mount-plugin
xfce4-mpc-plugin
xfce4-netload-plugin
# xfce4-notes-plugin
xfce4-places-plugin
xfce4-pulseaudio-plugin
# xfce4-screensaver
xfce4-sensors-plugin
xfce4-smartbookmark-plugin
xfce4-systemload-plugin
# xfce4-time-out-plugin
xfce4-timer-plugin
xfce4-verve-plugin
xfce4-weather-plugin
xfce4-wavelan-plugin
xfce4-xkb-plugin
xfce4-battery-plugin
xfce4-clipman-plugin
EOF

echo "4. Copying theme customizations..."
# Fix: Only copy includes.chroot if source and destination differ
if [ "$SCRIPT_DIR/config/includes.chroot" != "config/includes.chroot" ]; then
  cp -r "$SCRIPT_DIR/config/includes.chroot" config/
fi

# Check for required files before proceeding
if [ ! -f "config/includes.chroot/usr/share/backgrounds/duxos.png" ]; then
  echo "❌ Required background image not found: config/includes.chroot/usr/share/backgrounds/duxos.png"
  exit 1
fi
if [ ! -d "config/includes.chroot/home/user" ]; then
  echo "❌ Required user config directory not found: config/includes.chroot/home/user"
  exit 1
fi

echo "5. Setting up GRUB splash..."
mkdir -p config/includes.binary/isolinux
cp "$SCRIPT_DIR/config/includes.chroot/usr/share/backgrounds/duxos.png" config/includes.binary/isolinux/splash.png

echo "6. Setting file permissions..."
chown -R 1000:1000 config/includes.chroot/home/user

echo "7. Building the ISO..."
lb build

echo "8. Moving ISO to output location..."
if [ -f "live-image-amd64.hybrid.iso" ]; then
    mv live-image-amd64.hybrid.iso "$ISO_OUTPUT"
    echo "✅ Build complete! ISO file created at: $ISO_OUTPUT"
    echo "   File size: $(du -h "$ISO_OUTPUT" | cut -f1)"
else
    echo "❌ Build failed - ISO file not found"
    exit 1
fi

echo
echo "=== Build Summary ==="
echo "✅ All theme customizations included:"
echo "   - GRUB splash and theme"
echo "   - GTK/XFCE dark theme with blue accents"
echo "   - Custom icon theme"
echo "   - Login screen configuration"
echo "   - System sounds"
echo "   - Desktop background"
echo
echo "🎉 Dux_OS is ready for testing!" 