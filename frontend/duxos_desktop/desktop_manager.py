#!/usr/bin/env python3
"""
DuxOS Desktop App Main Entry Point

Launches the main window for the DuxOS API/App Store desktop application.
"""

import sys

from PyQt5.QtWidgets import QApplication

from duxos_desktop.api_client import StoreApiClient
from duxos_desktop.ui.main_window import MainWindow
from duxos_desktop.wallet_client import WalletClient


def main():
    app = QApplication(sys.argv)
    api_client = StoreApiClient()
    wallet_client = WalletClient()
    window = MainWindow(api_client, wallet_client)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
