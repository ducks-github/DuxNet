# 🚀 DuxNet v2.3.5 Release

## Launcher Service Detection Fix

This release fixes backend service detection by checking for the existence of the `.py` file (e.g., `main.py`, `escrow_service.py`) instead of the directory. This ensures backend services are started correctly on all platforms.

---

## What's Fixed

- **Launcher now checks for `.py` files instead of directories**
- **Backend services are detected and started on Windows, Linux, and Mac**
- **No more skipping services due to directory/file confusion**
- **Improved reliability for all users**

---

## How to Use

1. **Download v2.3.5** from GitHub releases
2. **Extract the ZIP file**
3. **Run the setup script for your OS**
   - Windows: `scripts\setup_windows.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
4. **Start DuxNet**
   - Windows: `scripts\run_duxnet_windows.bat` or `scripts\run_duxnet.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`

---

## Changelog

### Fixed
- Launcher now checks for `.py` files for backend services
- Backend services are started on all platforms
- No more skipping due to path or directory issues

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.5** — Backend services now start reliably everywhere! 🚀 