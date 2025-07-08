# 🚀 DuxNet v2.3.9 Release

## Debug Print for Desktop GUI Startup

This release adds a print statement to `desktop_manager.py` to confirm script execution and help diagnose why the desktop GUI window may not appear. This will help users and developers verify that the script is running and that the QApplication event loop is present.

---

## What's Added

- **Print statement at the top of `desktop_manager.py`:**
  - Prints `Starting DuxNet Desktop Manager...` when the script runs
  - Confirms script execution and helps debug GUI startup issues
- **QApplication event loop is present and correct**

---

## How to Use

1. **Download v2.3.9** from GitHub releases
2. **Extract the ZIP file**
3. **Run the setup script for your OS**
   - Windows: `scripts\setup_windows.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
4. **Start DuxNet**
   - Windows: `scripts\run_duxnet_windows.bat` or `scripts\run_duxnet.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
5. **Run the desktop GUI directly to check for the print statement:**
   ```cmd
   python -m frontend.duxnet_desktop.desktop_manager
   ```
   - You should see `Starting DuxNet Desktop Manager...` in the terminal

---

## Changelog

### Added
- Print statement to `desktop_manager.py` for debugging GUI startup

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.9** — Debugging made easier for desktop GUI startup! 🚀 