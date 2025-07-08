# 🚀 DuxNet v2.3.2 Release

## Launcher Path Handling & Debugging Fixes

This release fixes issues with the cross-platform launcher not finding backend and frontend services on Windows and Linux. It also adds better debugging and user feedback for missing files and services.

---

## 🛠️ What's Fixed

- **Launcher now changes working directory to project root** for correct module resolution
- **Improved file existence checks** for backend and frontend services
- **Better debugging output** to help diagnose missing files or misconfigurations
- **Ensures backend and frontend services are found and started correctly**
- **Improved user feedback** for missing files and services

---

## 🪟 Windows & 🐧 Linux Compatibility

- Works on both Windows and Linux
- No more path confusion when running from the `scripts/` directory
- Clear error messages if a service or file is missing

---

## How to Use

1. **Download v2.3.2** from GitHub releases
2. **Extract the ZIP file**
3. **Run the setup script for your OS**
   - Windows: `scripts\setup_windows.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
4. **Start DuxNet**
   - Windows: `scripts\run_duxnet_windows.bat` or `scripts\run_duxnet.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`

---

## Troubleshooting

- If a service is not found, the launcher will now tell you exactly which file is missing.
- Make sure all required config files (like `backend/duxnet_store/config.yaml`) are present.
- If you see a warning about a missing file, check your extracted release or clone.

---

## Changelog

### Changed
- `scripts/duxnet_launcher_cross_platform.py`: Now changes to project root, checks for service files, and prints better debug info.

### Fixed
- Services not starting on Windows due to path confusion
- Lack of feedback for missing files

---

## Support

- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.3.2** — Reliable cross-platform launching and better debugging! 🚀 