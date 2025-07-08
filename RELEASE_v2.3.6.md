# 🚀 DuxNet v2.3.6 Release

## Absolute Import Fix for Models

This release fixes import errors in the backend store service by switching to absolute imports for models in service files. This ensures that `Rating`, `Review`, and `Service` are always found, regardless of how or where the code is executed.

---

## What's Fixed

- **Service files now use absolute imports for models:**
  - `from backend.duxnet_store.models import Rating, Review, Service`
- **No more `ModuleNotFoundError` for models**
- **Backend store service starts reliably on all platforms**

---

## How to Use

1. **Download v2.3.6** from GitHub releases
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
- Service files now use absolute imports for models
- No more import errors for `Rating`, `Review`, `Service`
- Backend store service starts reliably

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.6** — No more model import errors! 🚀 