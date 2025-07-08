# 🚀 DuxNet v2.3.4 Release

## True Cross-Platform Launcher Fix

This release fixes backend and frontend service detection on Windows by using cross-platform path handling in the launcher. All services should now start correctly on both Windows and Linux.

---

## What's Fixed

- **Launcher now uses `os.path.join` for all file and directory checks**
- **Backend and frontend services are detected and started on Windows and Linux**
- **Full absolute path is printed for missing files for easier debugging**
- **No more 'not found, skipping' errors due to path separator issues**

---

## How to Use

1. **Download v2.3.4** from GitHub releases
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
- Launcher now works on all platforms (Windows, Linux, Mac)
- Backend and frontend services are detected and started correctly
- Prints full path for missing files for easier debugging

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.4** — True cross-platform support for all users! 🚀 