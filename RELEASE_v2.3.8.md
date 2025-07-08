# 🚀 DuxNet v2.3.8 Release

## Absolute Import Fixes for Desktop GUI

This release fixes all import errors in the desktop GUI by switching to absolute imports for all `frontend.duxnet_desktop` modules. This ensures the desktop GUI starts reliably on all platforms.

---

## What's Fixed

- **All frontend/duxnet_desktop modules now use absolute imports:**
  - e.g., `from frontend.duxnet_desktop.api_client import StoreApiClient`
- **No more `ModuleNotFoundError` for duxnet_desktop modules**
- **Desktop GUI starts reliably on all platforms**

---

## How to Use

1. **Download v2.3.8** from GitHub releases
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
- All frontend/duxnet_desktop modules now use absolute imports
- No more import errors for desktop GUI
- Desktop GUI starts reliably

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.8** — Desktop GUI import errors are history! 🚀 