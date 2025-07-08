# 🛠️ DuxNet v2.3.3 Release

## Default Store Backend Config & Out-of-the-Box Fixes

This release ensures DuxNet works out-of-the-box on all platforms by including a default configuration for the store backend service.

---

## What's New

- **Added `backend/duxnet_store/config.yaml`**
  - Minimal, safe default configuration for the store backend
  - Ensures the service can start immediately after extraction
  - Users should update `secret_key` and `database` settings for production

- **Improved Out-of-the-Box Experience**
  - No more missing config errors for the store backend
  - Launcher will now start all services if files are present

---

## How to Use

1. **Download v2.3.3** from GitHub releases
2. **Extract the ZIP file**
3. **Run the setup script for your OS**
   - Windows: `scripts\setup_windows.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
4. **Start DuxNet**
   - Windows: `scripts\run_duxnet_windows.bat` or `scripts\run_duxnet.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`

---

## Security Note
- The default `secret_key` in `config.yaml` is for development only.
- **Change it before deploying to production!**

---

## Changelog

### Added
- `backend/duxnet_store/config.yaml`: Default config for store backend

### Fixed
- Store backend now starts out-of-the-box
- No more missing config errors

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.3** — Now truly works out-of-the-box! 🛠️🚀 