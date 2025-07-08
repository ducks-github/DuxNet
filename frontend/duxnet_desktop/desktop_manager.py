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
    api_client = StoreApiClient()
    wallet_client = WalletClient()
    window = MainWindow(api_client, wallet_client)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
