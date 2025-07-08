#!/usr/bin/env python3
"""
DuxOS Desktop App Main Entry Point

Launches the main window for the DuxOS API/App Store desktop application.
"""

import sys

from PyQt5.QtWidgets import QApplication

from frontend.duxnet_desktop.api_client import StoreApiClient
from frontend.duxnet_desktop.ui.main_window import MainWindow
from frontend.duxnet_desktop.wallet_client import WalletClient


def main():
    print("Starting DuxNet Desktop Manager...")
    app = QApplication(sys.argv)
    print("QApplication created")
    api_client = StoreApiClient()
    print("StoreApiClient created")
    wallet_client = WalletClient()
    print("WalletClient created")
    window = MainWindow(api_client, wallet_client)
    print("MainWindow created")
    window.show()
    print("Window shown, entering event loop")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
