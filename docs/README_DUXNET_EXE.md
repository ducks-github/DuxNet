# DuxNet All-in-One Executable

This package includes a single executable (`duxnet_launcher.exe`) that launches all core DuxNet services and the Desktop GUI with one click.

## 🚀 How to Use

1. **Extract all files** from the release zip to a folder (keep the folder structure!).
2. **Double-click `duxnet_launcher.exe`** to start DuxNet.
   - All backend services (Store, Wallet, Escrow, Registry, etc.) will start in the background.
   - The Desktop GUI will open automatically.
3. **To stop DuxNet**, close the Desktop GUI and/or press `Ctrl+C` in the launcher window.

## 🛠️ Prerequisites
- No Python installation required (Python is bundled in the exe).
- All config files (e.g., `duxnet_store/config.yaml`, `duxnet_wallet/config.yaml`, etc.) must be present in their respective folders.
- Default ports (8000, 8001, 8003, 8004, etc.) must be available.
- For Flopcoin wallet support, ensure Flopcoin Core is running if needed.

## 🐞 Troubleshooting
- If a service fails to start, check the launcher window for error messages.
- Make sure all config files are present and valid.
- If a port is in use, edit the corresponding config file to change the port.
- For advanced debugging, run `duxnet_launcher.exe` from a command prompt to see all output.

## 📁 Included Services
- DuxNet Store (API/App Store)
- DuxNet Wallet (multi-crypto)
- DuxNet Escrow Service
- DuxNet Registry
- DuxNet Desktop GUI

## ℹ️ Notes
- This launcher is for local/demo use. For production, run services separately as needed.
- You can customize which services are started by editing `duxnet_launcher.py` before building the exe. 