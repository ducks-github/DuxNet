#!/bin/bash

# This script builds a custom Debian-based Dux_OS with XFCE desktop GUI.
# It customizes the boot splash and desktop background using PNG files.
# Usage: sudo ./build_duxos.sh [splash.png] [background.png]
# If no arguments are provided, it uses duxos.png for both.

# Check if the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script as root (e.g., using sudo)."
  exit 1
fi

# Get the directory of the script
SCRIPT_DIR=$(dirname "$0")
WORK_DIR="$SCRIPT_DIR/../build-workspace"
ISO_OUTPUT="$SCRIPT_DIR/../Dux_OS.iso"

# Default to duxos.png if no arguments provided
SPLASH_PNG="${1:-$SCRIPT_DIR/duxos.png}"
BACKGROUND_PNG="${2:-$SCRIPT_DIR/duxos.png}"

# Check if the provided or default PNG files exist
if [ ! -f "$SPLASH_PNG" ]; then
  echo "Splash PNG not found: $SPLASH_PNG"
  exit 1
fi

if [ ! -f "$BACKGROUND_PNG" ]; then
  echo "Background PNG not found: $BACKGROUND_PNG"
  exit 1
fi

# Ensure working directory exists
mkdir -p "$WORK_DIR"

# Install required tools
apt update
apt install -y live-build debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin

# Configure live-build
lb config --distribution bookworm --debian-installer live --architectures amd64 --archive-areas "main contrib non-free" \
  --mirror-bootstrap http://deb.debian.org/debian/ \
  --mirror-chroot http://deb.debian.org/debian/ \
  --mirror-binary http://deb.debian.org/debian/ \
  --mirror-binary-security http://security.debian.org/debian-security/ \
  --initramfs live-boot

# Create package list for XFCE desktop
mkdir -p config/package-lists
echo "task-xfce-desktop" > config/package-lists/desktop.list.chroot

# Copy splash PNG for the boot loader
mkdir -p config/includes.binary/isolinux
cp "$SPLASH_PNG" config/includes.binary/isolinux/splash.png

# Copy background PNG for the desktop
mkdir -p config/includes.chroot/usr/share/backgrounds
cp "$BACKGROUND_PNG" config/includes.chroot/usr/share/backgrounds/duxos.png

# Create XFCE configuration to set the default desktop background
XFCE_CONFIG_DIR=config/includes.chroot/home/user/.config/xfce4/xfconf/xfce-perchannel-xml
mkdir -p "$XFCE_CONFIG_DIR"
cat > "$XFCE_CONFIG_DIR/xfce4-desktop.xml" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-desktop" version="1.0">
  <property name="backdrop" type="empty">
    <property name="screen0" type="empty">
      <property name="monitor0" type="empty">
        <property name="workspace0" type="empty">
          <property name="last-image" type="string" value="/usr/share/backgrounds/duxos.png"/>
        </property>
      </property>
    </property>
  </property>
</channel>
EOL

# Set ownership of the configuration files to the live user (UID 1000)
chown -R 1000:1000 config/includes.chroot/home/user

# Build the live ISO
lb build

# Move the resulting ISO to the specified output location
mv live-image-amd64.hybrid.iso "$ISO_OUTPUT"

echo "Build complete! ISO file created at: $ISO_OUTPUT"