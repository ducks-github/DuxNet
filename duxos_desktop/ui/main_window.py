"""
Main Window UI for DuxOS Desktop

Provides navigation, search, and service list.
"""

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (
    QAction,
    QDialog,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .service_detail import ServiceDetailView
from .settings import SettingsWidget
from .user_account import UserAccountWidget


class MainWindow(QMainWindow):
    def __init__(self, api_client, wallet_client=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = api_client
        self.wallet_client = wallet_client
        self.current_user = None
        self.setWindowTitle("DuxOS API/App Store")
        self.resize(1200, 800)

        # Setup menu bar
        self.setup_menu_bar()

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Top bar: search
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for APIs, apps, or keywords...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Main area: service list and details
        splitter = QSplitter(Qt.Horizontal)

        # Service list
        self.service_list = QListWidget()
        self.service_list.itemClicked.connect(self.show_service_details)
        splitter.addWidget(self.service_list)

        # Service info label
        self.service_info = QLabel("Select a service to view details")
        self.service_info.setWordWrap(True)

        # Service details view
        self.details_widget = ServiceDetailView(self.api_client)
        self.details_widget.install_requested.connect(self.handle_install_request)
        self.details_widget.invoke_requested.connect(self.handle_invoke_request)
        splitter.addWidget(self.details_widget)
        splitter.setSizes([400, 800])

        layout.addWidget(splitter)

        # Setup user account dock widget
        self.setup_user_account_dock()

        # Load initial data
        self.load_services()

    def load_services(self):
        self.service_list.clear()
        try:
            result = self.api_client.search_services()
            for svc in result.get("services", []):
                item = QListWidgetItem(f"{svc['name']} ({svc['category']})")
                item.setData(Qt.UserRole, svc)
                self.service_list.addItem(item)
        except Exception as e:
            self.service_info.setText(f"Error loading services: {e}")

    def perform_search(self):
        query = self.search_input.text().strip()
        self.service_list.clear()
        try:
            result = self.api_client.search_services(query=query)
            for svc in result.get("services", []):
                item = QListWidgetItem(f"{svc['name']} ({svc['category']})")
                item.setData(Qt.UserRole, svc)
                self.service_list.addItem(item)
        except Exception as e:
            self.service_info.setText(f"Error searching: {e}")

    def show_service_details(self, item):
        svc = item.data(Qt.UserRole)
        self.details_widget.show_service(svc)

    def handle_install_request(self, service_id):
        """Handle service installation request"""
        QMessageBox.information(
            self, "Install Service", f"Installation requested for service {service_id}"
        )
        # TODO: Implement actual installation logic

    def handle_invoke_request(self, service_id):
        """Handle service invocation request"""
        QMessageBox.information(
            self, "Invoke Service", f"API invocation requested for service {service_id}"
        )
        # TODO: Implement actual invocation logic

    def setup_user_account_dock(self):
        """Setup user account dock widget"""
        if self.wallet_client:
            self.user_account_widget = UserAccountWidget(self.api_client, self.wallet_client)
            self.user_account_widget.login_requested.connect(self.handle_user_login)
            self.user_account_widget.logout_requested.connect(self.handle_user_logout)

            dock = QDockWidget("User Account", self)
            dock.setWidget(self.user_account_widget)
            dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def handle_user_login(self, user_id, user_name):
        """Handle user login"""
        self.current_user = {"user_id": user_id, "user_name": user_name}
        QMessageBox.information(self, "Login", f"Welcome, {user_name}!")

    def handle_user_logout(self):
        """Handle user logout"""
        self.current_user = None
        QMessageBox.information(self, "Logout", "You have been logged out.")

    def setup_menu_bar(self):
        """Setup menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.load_services)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_settings)
        settings_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_settings(self):
        """Show settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)
        settings_widget = SettingsWidget()
        settings_widget.settings_changed.connect(self.handle_settings_changed)
        layout.addWidget(settings_widget)

        dialog.exec_()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About DuxOS Desktop",
            "DuxOS Desktop v1.0\n\n"
            "A desktop client for the DuxOS API/App Store.\n"
            "Built with PyQt5 and Python.",
        )

    def handle_settings_changed(self, settings):
        """Handle settings changes"""
        # TODO: Apply settings changes
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
