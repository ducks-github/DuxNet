"""
User Account Management for DuxOS Desktop

Provides user login, wallet integration, and profile management.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QTabWidget, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

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
        
        self.current_user = {
            "user_id": user_id,
            "user_name": user_name
        }
        
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
        
        # Load favorites
        try:
            favorites = self.api_client.get_user_favorites(user_id)
            self.favorites_label.setText(f"Favorites: {len(favorites)}")
        except Exception as e:
            self.favorites_label.setText("Favorites: Error loading")
    
    def get_current_user(self):
        """Get current user info"""
        return self.current_user 