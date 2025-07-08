#!/usr/bin/env python3
"""
Build Release Artifacts

This script creates release packages for DuxOS Node Registry.
"""

import os
import shutil
import subprocess
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path


def create_release_directory():
    """Create release directory structure"""
    release_dir = Path("release_artifacts")
    if release_dir.exists():
        shutil.rmtree(release_dir)

    release_dir.mkdir()
    return release_dir


def copy_documentation(release_dir):
    """Copy documentation files"""
    docs_dir = release_dir / "docs"
    docs_dir.mkdir()

    # Copy main documentation
    docs_files = [
        "README.md",
        "docs/development_plan.md",
        "docs/architecture.md",
        "duxos_wallet/README.md",
        "duxos_registry/README.md",
    ]

    for doc_file in docs_files:
        if Path(doc_file).exists():
            shutil.copy2(doc_file, docs_dir / Path(doc_file).name)


def copy_configuration_templates(release_dir):
    """Copy configuration templates"""
    config_dir = release_dir / "config"
    config_dir.mkdir()

    # Copy config files
    config_files = [
        "duxos_wallet/config.yaml",
        "registry.yaml",
        "requirements.txt",
        "requirements_health_monitor.txt",
        "requirements_desktop.txt",
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            shutil.copy2(config_file, config_dir / Path(config_file).name)


def copy_scripts(release_dir):
    """Copy utility scripts"""
    scripts_dir = release_dir / "scripts"
    scripts_dir.mkdir()

    # Copy scripts
    script_files = [
        "scripts/setup_flopcoin.py",
        "scripts/test_real_flopcoin.py",
        "scripts/setup_desktop.py",
        "install.sh",
        "build_script/build_duxos.sh",
    ]

    # Copy desktop components
    desktop_files = ["duxos_desktop/desktop_manager.py"]

    for script_file in script_files:
        if Path(script_file).exists():
            shutil.copy2(script_file, scripts_dir / Path(script_file).name)
            # Make scripts executable
            os.chmod(scripts_dir / Path(script_file).name, 0o755)

    # Copy desktop components
    desktop_dir = release_dir / "desktop"
    desktop_dir.mkdir()

    for desktop_file in desktop_files:
        if Path(desktop_file).exists():
            shutil.copy2(desktop_file, desktop_dir / Path(desktop_file).name)


def create_quick_start_guide(release_dir):
    """Create a quick start guide"""
    guide_content = """# DuxOS Node Registry - Quick Start Guide

## Prerequisites
- Python 3.8+
- Git
- Flopcoin Core (v2.x)
- Ubuntu/Debian system (for desktop environment)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ducks-github/Dux_OS.git
   cd Dux_OS
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_desktop.txt
   ```

3. **Install Flopcoin Core:**
   - Download from: https://github.com/Flopcoin/Flopcoin/releases
   - Extract and install to /usr/local/bin

4. **Setup Flopcoin daemon:**
   ```bash
   python scripts/setup_flopcoin.py
   ```

5. **Setup Desktop Environment (Optional):**
   ```bash
   sudo python scripts/setup_desktop.py
   ```

6. **Test integration:**
   ```bash
   python scripts/test_real_flopcoin.py
   ```

## Configuration

- Edit `config/config.yaml` for wallet settings
- Edit `config/registry.yaml` for registry settings

## Usage

### Command Line
- Start the registry: `python -m duxos_registry.main`
- Use wallet CLI: `python -m duxos_wallet.cli`

### Desktop Environment
- Start DuxOS Desktop: `python desktop/desktop_manager.py`
- Or login to the desktop environment after setup

## Support

- Documentation: See `docs/` directory
- Issues: https://github.com/ducks-github/Dux_OS/issues

---
Generated on: {date}
Version: v2.2.0
""".format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    with open(release_dir / "QUICK_START.md", "w") as f:
        f.write(guide_content)


def create_changelog(release_dir):
    """Create a changelog for this release"""
    changelog_content = """# Changelog - v2.2.0

## 🚀 New Features

### Real Flopcoin Core Integration
- **Full Flopcoin Core daemon integration** - Connect to live Flopcoin blockchain
- **Live wallet operations** - Address generation, balance checks, send/receive FLOP
- **Transaction management** - History, status tracking, fee estimation
- **Blockchain integration** - Network info, mempool data, sync status

### Enhanced Wallet System
- **Secure RPC communication** - Configurable credentials and encryption
- **Address management** - Generate and validate Flopcoin addresses
- **Transaction history** - Complete audit trail and status tracking
- **Fee estimation** - Smart fee calculation for optimal transaction costs

### Developer Tools
- **Setup automation** - `scripts/setup_flopcoin.py` for easy daemon configuration
- **Integration testing** - `scripts/test_real_flopcoin.py` for end-to-end validation
- **Configuration management** - Updated wallet and registry configs
- **Documentation** - Comprehensive setup and usage guides

### Desktop Environment
- **Modern GUI** - Full desktop environment with XFCE integration
- **Desktop Manager** - Custom DuxOS desktop manager with system monitoring
- **Application Launcher** - Easy access to all DuxOS applications
- **System Tray** - Real-time system resource monitoring
- **Desktop Shortcuts** - Quick access to key applications
- **Autostart Services** - Automatic startup of DuxOS services

## 🔧 Technical Improvements

### Code Quality
- Enhanced error handling and logging
- Type safety improvements
- Better exception management
- Comprehensive test coverage

### Security
- Secure RPC authentication
- Configurable security settings
- Wallet backup automation
- Input validation and sanitization

### Performance
- Optimized RPC calls
- Efficient transaction processing
- Improved memory management
- Better resource utilization

## 📚 Documentation

- Updated README with real Flopcoin integration
- Comprehensive development plan
- Quick start guide
- Configuration templates
- Troubleshooting guides

## 🐛 Bug Fixes

- Fixed indentation issues in repository files
- Resolved type conversion warnings
- Improved error messages
- Enhanced debugging capabilities

## 🔄 Migration Notes

- **Breaking Changes**: None
- **Deprecations**: Mock Flopcoin daemon removed
- **New Dependencies**: Flopcoin Core v2.x required
- **Configuration**: Updated wallet config format

## 📦 Release Artifacts

This release includes:
- Source code
- Configuration templates
- Setup and test scripts
- Documentation
- Quick start guide

## 🎯 Next Steps

- Test live FLOP transactions
- Enable wallet encryption for production
- Monitor blockchain sync status
- Integrate with Node Registry API/UI

---
Release Date: {date}
Version: v2.2.0
""".format(
        date=datetime.now().strftime("%Y-%m-%d")
    )

    with open(release_dir / "CHANGELOG.md", "w") as f:
        f.write(changelog_content)


def create_archive(release_dir, version):
    """Create compressed archives"""
    # Create ZIP archive
    zip_filename = f"duxos-node-registry-{version}.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(release_dir)
                zipf.write(file_path, arcname)

    # Create TAR.GZ archive
    tar_filename = f"duxos-node-registry-{version}.tar.gz"
    with tarfile.open(tar_filename, "w:gz") as tar:
        tar.add(release_dir, arcname=f"duxos-node-registry-{version}")

    return zip_filename, tar_filename


def main():
    """Main build function"""
    print("🚀 Building DuxOS Node Registry Release Artifacts")
    print("=" * 50)

    version = "v2.2.0"

    # Create release directory
    print("📁 Creating release directory...")
    release_dir = create_release_directory()

    # Copy files
    print("📋 Copying documentation...")
    copy_documentation(release_dir)

    print("⚙️ Copying configuration templates...")
    copy_configuration_templates(release_dir)

    print("🔧 Copying scripts...")
    copy_scripts(release_dir)

    # Create guides
    print("📖 Creating quick start guide...")
    create_quick_start_guide(release_dir)

    print("📝 Creating changelog...")
    create_changelog(release_dir)

    # Create archives
    print("📦 Creating release archives...")
    zip_file, tar_file = create_archive(release_dir, version)

    # Cleanup
    print("🧹 Cleaning up...")
    shutil.rmtree(release_dir)

    print(f"✅ Release artifacts created:")
    print(f"   📦 {zip_file}")
    print(f"   📦 {tar_file}")
    print(f"\n📋 Files included:")
    print(f"   - Documentation (README, guides, changelog)")
    print(f"   - Configuration templates")
    print(f"   - Setup and test scripts")
    print(f"   - Quick start guide")

    print(f"\n🎉 Release v{version} artifacts ready for upload!")


if __name__ == "__main__":
    main()
