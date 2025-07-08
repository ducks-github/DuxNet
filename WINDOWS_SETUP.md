# 🪟 DuxNet Windows Setup Guide

This guide will help you get DuxNet running on Windows.

## 📋 Prerequisites

### 1. Python Installation
- **Download Python 3.7+** from [python.org](https://www.python.org/downloads/)
- **IMPORTANT**: Check "Add Python to PATH" during installation
- Verify installation by opening Command Prompt and typing: `python --version`

### 2. System Requirements
- Windows 10 or later
- At least 2GB RAM
- 500MB free disk space
- Internet connection for dependency installation

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
1. **Download the release** from GitHub
2. **Extract the ZIP file** to a folder (e.g., `C:\DuxNet`)
3. **Double-click** `scripts\setup_windows.bat`
4. **Follow the setup prompts**
5. **Double-click** `scripts\run_duxnet_windows.bat` to start

### Option 2: Manual Setup
1. **Open Command Prompt** as Administrator
2. **Navigate to the DuxNet folder**:
   ```cmd
   cd C:\path\to\DuxNet
   ```
3. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```
4. **Run the launcher**:
   ```cmd
   python scripts\duxnet_launcher_cross_platform.py
   ```

## 🔧 Troubleshooting

### Common Issues

#### ❌ "Python is not recognized"
**Solution**: Python is not in your PATH
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add Python installation directory (e.g., `C:\Python39\`)

#### ❌ "pip is not recognized"
**Solution**: Install pip
```cmd
python -m ensurepip --upgrade
```

#### ❌ "Port already in use"
**Solution**: Free up ports 8000-8010
1. Check what's using the ports:
   ```cmd
   netstat -ano | findstr :8000
   ```
2. Stop the processes or change ports in config files

#### ❌ "Module not found"
**Solution**: Install missing dependencies
```cmd
pip install fastapi uvicorn pyqt5 requests bcrypt
```

#### ❌ "Permission denied"
**Solution**: Run as Administrator
1. Right-click Command Prompt
2. Select "Run as administrator"

### Advanced Troubleshooting

#### Check Python Version
```cmd
python --version
```

#### Check Installed Packages
```cmd
pip list
```

#### Run Individual Services
```cmd
# Desktop GUI
python -m frontend.duxnet_desktop.desktop_manager

# Store Backend
python -m backend.duxnet_store.main --config backend/duxnet_store/config.yaml

# Escrow Service
python -m backend.duxos_escrow.escrow_service
```

#### Enable Debug Mode
Edit `scripts\duxnet_launcher_cross_platform.py` and set:
```python
DEBUG_MODE = True
```

## 📁 File Structure (Windows)

```
DuxNet/
├── backend/                    # Backend services
├── frontend/                   # Desktop GUI and CLI
├── shared/                     # Shared utilities
├── scripts/                    # Windows batch files
│   ├── setup_windows.bat      # Setup script
│   ├── run_duxnet_windows.bat # Enhanced launcher
│   └── run_duxnet.bat         # Simple launcher
├── docs/                       # Documentation
└── requirements.txt            # Python dependencies
```

## 🎯 What Each Script Does

### `setup_windows.bat`
- Checks Python installation
- Installs dependencies
- Verifies required files
- Provides setup feedback

### `run_duxnet_windows.bat`
- Enhanced launcher with error handling
- Automatic dependency checking
- Better error messages
- Graceful shutdown

### `run_duxnet.bat`
- Simple launcher
- Basic error checking
- Quick start option

## 🔍 Debugging

### Enable Verbose Output
```cmd
python scripts\duxnet_launcher_cross_platform.py --verbose
```

### Check Logs
Look for log files in:
- `backend/duxnet_store/logs/`
- `backend/duxos_escrow/logs/`
- `frontend/duxnet_desktop/logs/`

### Test Individual Components
```cmd
# Test Python installation
python -c "print('Python works!')"

# Test imports
python -c "import fastapi; print('FastAPI works!')"
python -c "import PyQt5; print('PyQt5 works!')"
```

## 📞 Getting Help

### Before Asking for Help
1. **Check this guide** for common solutions
2. **Try the setup script** first
3. **Check error messages** carefully
4. **Verify Python installation**

### Where to Get Help
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **GitHub Discussions**: [DuxNet Discussions](https://github.com/ducks-github/DuxNet/discussions)
- **Documentation**: Check the `docs/` folder

### When Reporting Issues
Include:
- Windows version
- Python version (`python --version`)
- Error message (copy-paste exactly)
- Steps to reproduce
- What you've already tried

## 🎉 Success!

Once DuxNet is running, you should see:
- Desktop GUI window
- Multiple service status messages
- "All services started successfully"

The desktop GUI will be your main interface for using DuxNet!

---

**Need more help?** Check the main [README.md](README.md) for additional information. 