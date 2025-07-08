# Dux_OS Theme Customization

This document describes the comprehensive theme customization implemented for Dux_OS, including splash images, GRUB themes, GTK/XFCE themes, icon themes, login screen configuration, and system sounds.

## Overview

The Dux_OS theme customization includes:

- ✅ **Splash image and GRUB theme**
- ✅ **GTK/XFCE theme**
- ✅ **Icon theme**
- ✅ **Login screen background and config**
- ✅ **System sounds**

## Directory Structure

```
config/includes.chroot/
├── etc/
│   ├── default/
│   │   └── grub                    # GRUB configuration
│   └── lightdm/
│       ├── lightdm.conf            # LightDM main config
│       └── lightdm-gtk-greeter.conf.d/
│           └── duxos.conf          # Login screen theme
├── usr/
│   ├── share/
│   │   ├── backgrounds/
│   │   │   └── duxos.png          # Desktop background
│   │   ├── grub/
│   │   │   ├── duxos-splash.png   # GRUB splash image
│   │   │   └── themes/
│   │   │       └── duxos/
│   │   │           └── theme.txt   # GRUB theme
│   │   ├── themes/
│   │   │   └── duxos/             # GTK theme
│   │   ├── icons/
│   │   │   └── duxos/             # Icon theme
│   │   └── sounds/
│   │       └── duxos/             # Sound theme
│   └── local/bin/
│       └── setup-duxos-theme      # Theme setup script
└── home/user/.config/
    └── xfce4/xfconf/xfce-perchannel-xml/
        ├── xfce4-desktop.xml      # Desktop background config
        └── xsettings.xml          # XFCE4 theme settings
```

## 1. Splash Image and GRUB Theme

### GRUB Configuration
- **File**: `config/includes.chroot/etc/default/grub`
- **Features**:
  - Custom splash screen: `/usr/share/grub/duxos-splash.png`
  - Custom theme: `/usr/share/grub/themes/duxos/theme.txt`
  - High-resolution display: 1920x1080
  - Quiet boot with splash

### GRUB Theme
- **File**: `config/includes.chroot/usr/share/grub/themes/duxos/theme.txt`
- **Features**:
  - Custom fonts (DejaVu Sans)
  - Color scheme with white text on dark background
  - Custom progress bar styling
  - Menu box with borders

## 2. GTK/XFCE Theme

### GTK3 Theme
- **File**: `config/includes.chroot/usr/share/themes/duxos/gtk-3.0/gtk.css`
- **Features**:
  - Dark theme with blue accents (#4a90d9)
  - Rounded corners for windows
  - Custom button styling with gradients
  - Focus indicators for form elements
  - Custom menu styling

### GTK2 Theme
- **File**: `config/includes.chroot/usr/share/themes/duxos/gtk-2.0/gtkrc`
- **Features**:
  - Compatible styling for GTK2 applications
  - Consistent color scheme with GTK3
  - Custom button and entry styling

### Theme Index
- **File**: `config/includes.chroot/usr/share/themes/duxos/index.theme`
- **Features**:
  - Theme metadata
  - Integration with GNOME/GTK theme system
  - Custom window button layout

## 3. Icon Theme

### Icon Theme Structure
- **Base Directory**: `config/includes.chroot/usr/share/icons/duxos/`
- **Sizes**: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256
- **Categories**: apps, actions, devices, emblems, mimetypes, places, status

### Icon Theme Index
- **File**: `config/includes.chroot/usr/share/icons/duxos/index.theme`
- **Features**:
  - Inherits from Adwaita for fallback icons
  - Complete directory structure definition
  - Proper theme metadata

## 4. Login Screen Background and Config

### LightDM Configuration
- **File**: `config/includes.chroot/etc/lightdm/lightdm.conf`
- **Features**:
  - GTK greeter session
  - XFCE user session
  - Auto-login for user account

### GTK Greeter Theme
- **File**: `config/includes.chroot/etc/lightdm/lightdm-gtk-greeter.conf.d/duxos.conf`
- **Features**:
  - Custom background: `/usr/share/backgrounds/duxos.png`
  - Dux_OS theme and icon theme
  - Custom font (DejaVu Sans 12)
  - System indicators (clock, language, session, power)
  - 24-hour clock format

## 5. System Sounds

### Sound Theme Structure
- **Base Directory**: `config/includes.chroot/usr/share/sounds/duxos/`
- **Format**: OGA (Ogg Vorbis Audio)
- **Channels**: Stereo

### Sound Events
- `message-new-instant.oga` - New instant message
- `message.oga` - General message notification
- `notification.oga` - System notification
- `phone-incoming-call.oga` - Incoming call
- `phone-outgoing-busy.oga` - Outgoing call (busy)
- `phone-outgoing-calling.oga` - Outgoing call (dialing)
- `service-login.oga` - Service login
- `service-logout.oga` - Service logout
- `window-attention.oga` - Window attention

## 6. XFCE4 Configuration

### Desktop Background
- **File**: `config/includes.chroot/home/user/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-desktop.xml`
- **Features**:
  - Custom background image
  - Proper workspace configuration

### Theme Settings
- **File**: `config/includes.chroot/home/user/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml`
- **Features**:
  - GTK theme: duxos
  - Icon theme: duxos
  - Sound theme: duxos
  - Custom font: DejaVu Sans 12
  - Font antialiasing and hinting
  - Event sounds enabled
  - Input feedback sounds enabled

## 7. Package Dependencies

### Theme Packages
- **File**: `config/package-lists/theme-packages.list.chroot`
- **Includes**:
  - LightDM and GTK greeter
  - XFCE4 components and plugins
  - Theme management tools

## 8. Automation Scripts

### Theme Setup Script
- **File**: `config/includes.chroot/usr/local/bin/setup-duxos-theme`
- **Features**:
  - Automatic theme application
  - GRUB configuration update
  - Permission setting
  - GSettings configuration

### Build Hook
- **File**: `config/hooks/duxos-theme.chroot`
- **Features**:
  - Runs during live-build chroot stage
  - Ensures proper directory structure
  - Sets correct permissions

## Usage

### Building Dux_OS with Themes
1. Ensure all theme files are in place
2. Run the live-build process
3. The hook script will automatically configure themes
4. The setup script will be available for post-installation customization

### Manual Theme Application
```bash
# Run the theme setup script
sudo /usr/local/bin/setup-duxos-theme

# Or manually apply themes
xfconf-query -c xsettings -p /Net/ThemeName -s "duxos"
xfconf-query -c xsettings -p /Net/IconThemeName -s "duxos"
xfconf-query -c xsettings -p /Net/SoundThemeName -s "duxos"
```

## Customization

### Adding Custom Icons
Place custom icons in the appropriate size directories:
```
/usr/share/icons/duxos/{size}/{category}/
```

### Modifying Colors
Edit the GTK CSS files:
- GTK3: `/usr/share/themes/duxos/gtk-3.0/gtk.css`
- GTK2: `/usr/share/themes/duxos/gtk-2.0/gtkrc`

### Adding Sound Effects
Place OGA format audio files in:
```
/usr/share/sounds/duxos/stereo/
```

## Troubleshooting

### Theme Not Applying
1. Check file permissions: `chmod -R 755 /usr/share/themes/duxos`
2. Restart XFCE4 session
3. Run theme setup script

### GRUB Theme Issues
1. Ensure splash image is in correct format (PNG)
2. Check GRUB configuration syntax
3. Run `update-grub` after changes

### Sound Issues
1. Verify audio files are in OGA format
2. Check sound theme inheritance
3. Ensure PulseAudio is running

## Notes

- All themes inherit from standard themes (Adwaita, freedesktop) for fallback
- The theme is designed to work with XFCE4 desktop environment
- Customization maintains consistency across all UI elements
- The build process automatically applies all theme configurations 