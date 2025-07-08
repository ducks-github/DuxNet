# DuxOS Desktop App

A cross-platform desktop application for the DuxOS API/App Store.

## Features
- Browse, search, and filter APIs/apps from the decentralized store
- View service details, reviews, and ratings
- User account management and wallet integration
- Install desktop apps or invoke APIs
- Submit and view reviews/ratings
- Manage favorites and usage
- Notifications and settings

## Structure
- `desktop_manager.py` — Main application entry point
- `api_client.py` — Store API client
- `wallet_client.py` — Wallet integration
- `models.py` — UI models and helpers
- `ui/` — UI components (PyQt/PySide classes or .ui files)
- `resources/` — Icons, images, and static assets

## Getting Started
1. Install requirements: `pip install -r requirements.txt`
2. Run the app: `python duxos_desktop/desktop_manager.py`

## Requirements
- Python 3.8+
- PyQt5 or PySide6
- requests
- duxos_store, duxos_wallet

## Development
- UI can be designed with Qt Designer and loaded dynamically
- Modular structure for easy extension

--- 