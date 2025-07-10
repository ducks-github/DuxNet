# 🚀 DuxNet v2.4.0 Release

## Interactive Debugging for Desktop GUI

This release marks the start of a new phase: interactive debugging of the desktop GUI with user feedback. The launcher and backend services are stable, and now we will work together to trace and resolve any remaining GUI startup issues.

---


## What's New

- **Launcher and backend services are stable and cross-platform**
- **Desktop GUI dependency fixes and system library instructions added**
- **PyQt5 and requests dependencies now auto-installed on first run**
- **Stepwise debugging for headless/container environments**
- **All recent commits pushed to main branch**


---

## How to Use

1. **Download v2.4.0** from GitHub releases
2. **Extract the ZIP file**
3. **Run the setup script for your OS**
   - Windows: `scripts\setup_windows.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
4. **Start DuxNet**
   - Windows: `scripts\run_duxnet_windows.bat` or `scripts\run_duxnet.bat`
   - Linux/Mac: `scripts/run_duxnet.sh`
5. **Run the desktop GUI directly**
   ```bash
   python -m frontend.duxnet_desktop.desktop_manager
   ```
   - If running in a headless or container environment, see README for troubleshooting Qt/X11 issues and required system libraries.


---


## Next Steps

- User will interact with the release and report print output and errors
- We will continue debugging step by step based on user feedback
- All code and dependency updates are now available on the main branch

---

## Support
- **GitHub Issues**: [DuxNet Issues](https://github.com/ducks-github/DuxNet/issues)
- **Include your OS, Python version, and error messages when reporting**

---

**DuxNet v2.4.0** — Interactive debugging for a fully working desktop GUI! 🚀 