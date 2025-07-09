"""
User Account Management for DuxOS Desktop

Provides user login, wallet integration, and profile management.
"""

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QToolButton,
    QApplication,
)


class UserAccountWidget(QWidget):
    login_requested = pyqtSignal(str, str)  # user_id, user_name
    logout_requested = pyqtSignal()

    def __init__(self, api_client, wallet_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.wallet_client = wallet_client
        self.current_user = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Login section
        self.login_group = QGroupBox("Login")
        login_layout = QFormLayout(self.login_group)

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("Enter user ID")
        login_layout.addRow("User ID:", self.user_id_input)

        self.user_name_input = QLineEdit()
        self.user_name_input.setPlaceholderText("Enter user name")
        login_layout.addRow("User Name:", self.user_name_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)
        login_layout.addRow("", self.login_button)

        layout.addWidget(self.login_group)

        # User profile section (initially hidden)
        self.profile_group = QGroupBox("User Profile")
        self.profile_group.setVisible(False)
        profile_layout = QVBoxLayout(self.profile_group)

        # User info
        self.user_info = QLabel("Not logged in")
        self.user_info.setFont(QFont("Arial", 12, QFont.Bold))
        profile_layout.addWidget(self.user_info)

        # Wallet info
        wallet_layout = QFormLayout()
        self.wallet_address_label = QLabel("Not connected")
        self.balance_label = QLabel("0.0 FLOP")
        wallet_layout.addRow("Wallet Address:", self.wallet_address_label)
        wallet_layout.addRow("Balance:", self.balance_label)
        profile_layout.addLayout(wallet_layout)

        # Multi-crypto balances
        self.crypto_balances_group = QGroupBox("Crypto Balances")
        self.crypto_balances_layout = QFormLayout(self.crypto_balances_group)
        self.crypto_balance_labels = {}
        self.crypto_address_labels = {}
        self.crypto_copy_buttons = {}
        for currency in ["BTC", "ETH", "FLOP", "USDT", "BNB", "XRP", "SOL", "ADA", "DOGE", "TON", "TRX"]:
            balance_label = QLabel("0.0")
            address_label = QLabel("-")
            powered_by_label = QLabel("")
            powered_by_label.setToolTip("")
            copy_button = QToolButton()
            copy_button.setText("Copy")
            copy_button.setToolTip(f"Copy {currency} address")
            copy_button.clicked.connect(lambda checked, c=currency: self.copy_crypto_address(c))
            self.crypto_balance_labels[currency] = balance_label
            self.crypto_address_labels[currency] = address_label
            self.crypto_copy_buttons[currency] = copy_button
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(balance_label)
            row_layout.addWidget(address_label)
            row_layout.addWidget(powered_by_label)
            row_layout.addWidget(copy_button)
            row_widget.powered_by_label = powered_by_label
            self.crypto_balances_layout.addRow(f"{currency}:", row_widget)
        profile_layout.addWidget(self.crypto_balances_group)

        # Favorites
        self.favorites_label = QLabel("Favorites: 0")
        profile_layout.addWidget(self.favorites_label)

        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.logout)
        profile_layout.addWidget(self.logout_button)

        layout.addWidget(self.profile_group)
        layout.addStretch()

    def login(self):
        """Handle user login"""
        user_id = self.user_id_input.text().strip()
        user_name = self.user_name_input.text().strip()

        if not user_id or not user_name:
            return  # Should show error message

        self.current_user = {"user_id": user_id, "user_name": user_name}

        # Update UI
        self.login_group.setVisible(False)
        self.profile_group.setVisible(True)

        # Load user data
        self.load_user_data()

        # Emit signal
        self.login_requested.emit(user_id, user_name)

    def logout(self):
        """Handle user logout"""
        self.current_user = None

        # Update UI
        self.login_group.setVisible(True)
        self.profile_group.setVisible(False)

        # Clear inputs
        self.user_id_input.clear()
        self.user_name_input.clear()

        # Emit signal
        self.logout_requested.emit()

    def load_user_data(self):
        """Load and display user data"""
        if not self.current_user:
            return

        user_id = self.current_user["user_id"]
        user_name = self.current_user["user_name"]

        # Update user info
        self.user_info.setText(f"Welcome, {user_name}!")

        # Load wallet info
        try:
            wallet = self.wallet_client.get_wallet(user_id)
            if wallet:
                self.wallet_address_label.setText(wallet.get("address", "Unknown"))
                self.balance_label.setText(f"{wallet.get('balance', 0.0):.2f} FLOP")
            else:
                self.wallet_address_label.setText("No wallet found")
                self.balance_label.setText("0.0 FLOP")
        except Exception as e:
            self.wallet_address_label.setText("Error loading wallet")
            self.balance_label.setText("0.0 FLOP")

        # Load multi-crypto balances
        try:
            balances = self.wallet_client.get_all_balances()
            for currency in self.crypto_balance_labels.keys():
                value = balances.get(currency, {}).get("balance", 0.0)
                address = balances.get(currency, {}).get("address", "-")
                powered_by = balances.get(currency, {}).get("powered_by", "")
                if self.crypto_balance_labels.get(currency):
                    self.crypto_balance_labels[currency].setText(f"{value:.8f}")
                if self.crypto_address_labels.get(currency):
                    self.crypto_address_labels[currency].setText(address)
                # Show Trust Wallet badge/tooltip if powered by wallet-core
                row_widget = self.crypto_balances_layout.itemAt(self.crypto_balances_layout.rowCount()-1, 1).widget()
                if hasattr(row_widget, 'powered_by_label'):
                    if powered_by == "wallet-core":
                        row_widget.powered_by_label.setText("Trust Wallet")
                        row_widget.powered_by_label.setToolTip("Powered by Trust Wallet wallet-core")
                    else:
                        row_widget.powered_by_label.setText("")
                        row_widget.powered_by_label.setToolTip("")
        except Exception as e:
            for label in self.crypto_balance_labels.values():
                if label:
                    label.setText("Error")
            for label in self.crypto_address_labels.values():
                if label:
                    label.setText("Error")

        # Load favorites
        try:
            favorites = self.api_client.get_user_favorites(user_id)
            self.favorites_label.setText(f"Favorites: {len(favorites)}")
        except Exception as e:
            self.favorites_label.setText("Favorites: Error loading")

    def copy_crypto_address(self, currency):
        address = self.crypto_address_labels[currency].text()
        if address and address != "-":
            clipboard = QApplication.clipboard()
            clipboard.setText(address)
            self.crypto_copy_buttons[currency].setToolTip("Copied!")
            QTimer.singleShot(1200, lambda: self.crypto_copy_buttons[currency].setToolTip(f"Copy {currency} address"))

    def get_current_user(self):
        """Get current user info"""
        return self.current_user
