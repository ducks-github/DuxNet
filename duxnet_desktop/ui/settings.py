"""
Settings Widget for DuxOS Desktop

Provides configuration options for API endpoints, themes, and preferences.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFormLayout, QGroupBox, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal

class SettingsWidget(QWidget):
    settings_changed = pyqtSignal(dict)  # settings dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {
            "store_api_url": "http://localhost:8000",
            "wallet_api_url": "http://localhost:8002",
            "theme": "default",
            "auto_refresh": True,
            "notifications": True
        }
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # API Settings
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(api_group)
        
        self.store_api_input = QLineEdit(self.settings["store_api_url"])
        api_layout.addRow("Store API URL:", self.store_api_input)
        
        self.wallet_api_input = QLineEdit(self.settings["wallet_api_url"])
        api_layout.addRow("Wallet API URL:", self.wallet_api_input)
        
        layout.addWidget(api_group)
        
        # UI Settings
        ui_group = QGroupBox("UI Settings")
        ui_layout = QFormLayout(ui_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["default", "dark", "light"])
        self.theme_combo.setCurrentText(self.settings["theme"])
        ui_layout.addRow("Theme:", self.theme_combo)
        
        self.auto_refresh_check = QCheckBox()
        self.auto_refresh_check.setChecked(self.settings["auto_refresh"])
        ui_layout.addRow("Auto Refresh:", self.auto_refresh_check)
        
        self.notifications_check = QCheckBox()
        self.notifications_check.setChecked(self.settings["notifications"])
        ui_layout.addRow("Notifications:", self.notifications_check)
        
        layout.addWidget(ui_group)
        
        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        
        layout.addStretch()
    
    def save_settings(self):
        """Save current settings"""
        self.settings.update({
            "store_api_url": self.store_api_input.text(),
            "wallet_api_url": self.wallet_api_input.text(),
            "theme": self.theme_combo.currentText(),
            "auto_refresh": self.auto_refresh_check.isChecked(),
            "notifications": self.notifications_check.isChecked()
        })
        
        self.settings_changed.emit(self.settings)
    
    def get_settings(self):
        """Get current settings"""
        return self.settings.copy() 