# 🚀 DuxNet v2.3.7 Release

## Absolute Import Fix for User Model

This release fixes a critical import error in the backend store service by switching to an absolute import for the `User` model in `user_routes.py`. This ensures the backend service starts reliably on all platforms.

---

## What's Fixed

- **user_routes.py now uses absolute import for User model:**
  - `from backend.duxnet_store.models import User`
- **No more `ModuleNotFoundError` for duxnet_store.api**
- **Backend store service starts reliably**

---

## How to Use

1. **Download v2.3.7** from GitHub releases
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
- user_routes.py now uses absolute import for User model
- No more import errors for duxnet_store.api
- Backend store service starts reliably

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.7** — No more User model import errors! 🚀 