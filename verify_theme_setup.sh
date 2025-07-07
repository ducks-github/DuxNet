#!/bin/bash

# Dux_OS Theme Verification Script
# This script verifies that all theme customizations are properly configured

echo "=== Dux_OS Theme Verification ==="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (sudo)"
    exit 1
fi

# Function to check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ $1 (missing)"
    fi
}

# Function to check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ $1 (missing)"
    fi
}

echo "1. Checking GRUB Configuration:"
check_file "config/includes.chroot/etc/default/grub"
check_file "config/includes.chroot/usr/share/grub/themes/duxos/theme.txt"
check_file "config/includes.chroot/usr/share/grub/duxos-splash.png"
echo

echo "2. Checking GTK/XFCE Theme:"
check_dir "config/includes.chroot/usr/share/themes/duxos"
check_file "config/includes.chroot/usr/share/themes/duxos/index.theme"
check_file "config/includes.chroot/usr/share/themes/duxos/gtk-3.0/gtk.css"
check_file "config/includes.chroot/usr/share/themes/duxos/gtk-2.0/gtkrc"
echo

echo "3. Checking Icon Theme:"
check_dir "config/includes.chroot/usr/share/icons/duxos"
check_file "config/includes.chroot/usr/share/icons/duxos/index.theme"
echo

echo "4. Checking Login Screen Configuration:"
check_file "config/includes.chroot/etc/lightdm/lightdm.conf"
check_file "config/includes.chroot/etc/lightdm/lightdm-gtk-greeter.conf.d/duxos.conf"
echo

echo "5. Checking System Sounds:"
check_dir "config/includes.chroot/usr/share/sounds/duxos"
check_file "config/includes.chroot/usr/share/sounds/duxos/index.theme"
check_file "config/includes.chroot/usr/share/sounds/duxos/stereo/index.theme"
echo

echo "6. Checking XFCE4 Configuration:"
check_file "config/includes.chroot/home/user/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml"
check_file "config/includes.chroot/home/user/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml"
echo

echo "7. Checking Package Lists:"
check_file "config/package-lists/theme-packages.list.chroot"
echo

echo "8. Checking Automation Scripts:"
check_file "config/includes.chroot/usr/local/bin/setup-duxos-theme"
check_file "config/hooks/duxos-theme.chroot"
echo

echo "9. Checking Background Images:"
check_file "config/includes.chroot/usr/share/backgrounds/duxos.png"
echo

echo "=== Verification Complete ==="
echo
echo "If all items show ✅, your Dux_OS theme customization is properly configured!"
echo "If any items show ❌, please check the missing files and recreate them." 