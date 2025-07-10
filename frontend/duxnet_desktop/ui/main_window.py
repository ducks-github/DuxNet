"""
Main Window UI for DuxOS Desktop

Provides navigation, search, and service list.
"""

from PyQt5.QtCore import QObject, Qt, Qt as QtCoreQt
from PyQt5.QtGui import QColor
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
    QTabWidget,
    QStyleFactory,
    QApplication,
    QTableWidget,
    QComboBox,
    QGroupBox,
    QTableWidgetItem,
    QTextEdit,
)

from .service_detail import ServiceDetailView
from .settings import SettingsWidget
from .user_account import UserAccountWidget
from .advanced_features import AdvancedFeaturesTab
from frontend.duxnet_desktop.ui.advanced_features import EscrowClient
from frontend.duxnet_desktop.ui.advanced_features import TaskClient
import json

# --- New tab widgets ---
class StoreTab(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        layout = QVBoxLayout(self)

        # --- Search Bar ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for APIs, apps, or keywords...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_services)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.refresh_button)
        layout.addLayout(search_layout)

        # --- Register API Form ---
        form_group = QGroupBox("Register New API/Service")
        form_layout = QVBoxLayout(form_group)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Service Name")
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description (min 10 chars)")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Category")
        self.code_hash_input = QLineEdit()
        self.code_hash_input.setPlaceholderText("Code Hash")
        self.github_link_input = QLineEdit()
        self.github_link_input.setPlaceholderText("GitHub Link (optional)")
        self.usage_text_input = QTextEdit()
        self.usage_text_input.setPlaceholderText("How to use this API (usage instructions)")
        self.owner_id_input = QLineEdit()
        self.owner_id_input.setPlaceholderText("Owner ID")
        self.owner_name_input = QLineEdit()
        self.owner_name_input.setPlaceholderText("Owner Name")
        self.register_button = QPushButton("Register API/Service")
        self.register_button.clicked.connect(self.handle_register_service)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.category_input)
        form_layout.addWidget(self.code_hash_input)
        form_layout.addWidget(self.github_link_input)
        form_layout.addWidget(self.usage_text_input)
        form_layout.addWidget(self.owner_id_input)
        form_layout.addWidget(self.owner_name_input)
        form_layout.addWidget(self.register_button)
        layout.addWidget(form_group)

        # --- Service List and Details ---
        main_splitter = QSplitter(Qt.Horizontal)
        self.service_list = QListWidget()
        self.service_list.itemClicked.connect(self.show_service_details)
        main_splitter.addWidget(self.service_list)
        self.details_panel = QTextEdit()
        self.details_panel.setReadOnly(True)
        main_splitter.addWidget(self.details_panel)
        main_splitter.setSizes([300, 700])
        layout.addWidget(main_splitter)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.load_services()

    def handle_register_service(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.text().strip()
        category = self.category_input.text().strip()
        code_hash = self.code_hash_input.text().strip()
        github_link = self.github_link_input.text().strip()
        usage_text = self.usage_text_input.toPlainText().strip()
        owner_id = self.owner_id_input.text().strip()
        owner_name = self.owner_name_input.text().strip()
        if not (name and desc and category and code_hash and owner_id and owner_name):
            self.status_label.setText("All fields are required.")
            return
        if len(desc) < 10:
            self.status_label.setText("Description must be at least 10 characters.")
            return
        service_data = {
            "name": name,
            "description": desc,
            "category": category,
            "code_hash": code_hash,
            "github_link": github_link,
            "usage": usage_text,
        }
        try:
            result = self.api_client.register_service(service_data, owner_id, owner_name)
            self.status_label.setText(f"Service registered: {result.get('name', 'Success')}")
            self.load_services()
        except Exception as e:
            self.status_label.setText(f"Registration failed: {e}")

    def load_services(self):
        self.service_list.clear()
        self.status_label.setText("Loading services...")
        try:
            result = self.api_client.search_services()
            for svc in result.get("services", []):
                item = QListWidgetItem(f"{svc['name']} ({svc['category']})")
                item.setData(Qt.UserRole, svc)
                self.service_list.addItem(item)
            self.status_label.clear()
        except Exception as e:
            self.status_label.setText(f"Error loading services: {e}")

    def perform_search(self):
        query = self.search_input.text().strip()
        self.service_list.clear()
        self.status_label.setText("Searching...")
        try:
            result = self.api_client.search_services(query=query)
            for svc in result.get("services", []):
                item = QListWidgetItem(f"{svc['name']} ({svc['category']})")
                item.setData(Qt.UserRole, svc)
                self.service_list.addItem(item)
            self.status_label.clear()
        except Exception as e:
            self.status_label.setText(f"Error searching: {e}")

    def show_service_details(self, item):
        svc = item.data(Qt.UserRole)
        self.details_panel.setText(json.dumps(svc, indent=2))

class WalletTab(QWidget):
    def __init__(self, wallet_client, parent=None):
        super().__init__(parent)
        self.wallet_client = wallet_client
        self.escrow_client = EscrowClient()  # Uses default base_url
        layout = QVBoxLayout(self)

        # --- Balances Section ---
        balances_group = QGroupBox("Multi-Crypto Balances")
        balances_layout = QVBoxLayout(balances_group)
        self.balances_table = QTableWidget(0, 3)
        self.balances_table.setHorizontalHeaderLabels(["Currency", "Balance", "Powered by"])
        self.balances_table.horizontalHeader().setStretchLastSection(True)
        balances_layout.addWidget(self.balances_table)
        layout.addWidget(balances_group)

        # --- Send/Receive Section ---
        send_group = QGroupBox("Send / Receive")
        send_layout = QHBoxLayout(send_group)
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["FLOP", "BTC", "ETH", "USDT", "BNB", "XRP", "SOL", "ADA", "DOGE", "TON", "TRX"])
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Recipient address")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send)
        self.receive_button = QPushButton("Receive")
        self.receive_button.clicked.connect(self.handle_receive)
        send_layout.addWidget(QLabel("Currency:"))
        send_layout.addWidget(self.currency_combo)
        send_layout.addWidget(self.address_input)
        send_layout.addWidget(self.amount_input)
        send_layout.addWidget(self.send_button)
        send_layout.addWidget(self.receive_button)
        layout.addWidget(send_group)

        # --- Escrow Management Section ---
        escrow_group = QGroupBox("Escrow Management")
        escrow_layout = QVBoxLayout(escrow_group)
        self.escrow_list = QListWidget()
        escrow_layout.addWidget(self.escrow_list)
        escrow_buttons_layout = QHBoxLayout()
        self.create_escrow_button = QPushButton("Create Escrow")
        self.create_escrow_button.clicked.connect(self.handle_create_escrow)
        self.release_escrow_button = QPushButton("Release Escrow")
        self.release_escrow_button.clicked.connect(self.handle_release_escrow)
        escrow_buttons_layout.addWidget(self.create_escrow_button)
        escrow_buttons_layout.addWidget(self.release_escrow_button)
        escrow_layout.addLayout(escrow_buttons_layout)
        layout.addWidget(escrow_group)

        # --- Status/Notifications ---
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.load_balances()
        self.load_escrows()

    def load_balances(self):
        self.balances_table.setRowCount(0)
        try:
            balances = self.wallet_client.get_all_balances()
            self.balances_table.setRowCount(len(balances))
            for i, (currency, info) in enumerate(balances.items()):
                currency_item = QTableWidgetItem(currency)
                currency_item.setFlags(currency_item.flags() & ~Qt.ItemIsEditable)
                self.balances_table.setItem(i, 0, currency_item)
                balance_item = QTableWidgetItem(str(info.get("balance", 0.0)))
                balance_item.setFlags(balance_item.flags() & ~Qt.ItemIsEditable)
                self.balances_table.setItem(i, 1, balance_item)
                # Trust Wallet badge/tooltip
                powered_by = info.get("powered_by", "")
                badge = QTableWidgetItem()
                if powered_by == "wallet-core":
                    badge.setText("Trust Wallet")
                    badge.setToolTip("Powered by Trust Wallet wallet-core")
                else:
                    badge.setText("-")
                badge.setFlags(badge.flags() & ~Qt.ItemIsEditable)
                self.balances_table.setItem(i, 2, badge)
        except Exception as e:
            self.status_label.setText(f"Error loading balances: {e}")

    def load_escrows(self):
        self.escrow_list.clear()
        try:
            escrows = self.escrow_client.get_active_escrows()
            for esc in escrows:
                self.escrow_list.addItem(f"{esc['id']} | {esc['currency']} {esc['amount']} | {esc['status']}")
        except Exception as e:
            self.status_label.setText(f"Error loading escrows: {e}")

    def handle_send(self):
        currency = self.currency_combo.currentText()
        address = self.address_input.text().strip()
        try:
            amount = float(self.amount_input.text().strip())
        except Exception:
            self.status_label.setText("Invalid amount.")
            return
        try:
            result = self.wallet_client.send_transaction(currency, address, amount)
            txid = result.get("txid", "unknown")
            self.status_label.setText(f"Sent {amount} {currency} to {address}. TXID: {txid}")
            self.load_balances()
        except Exception as e:
            self.status_label.setText(f"Send failed: {e}")

    def handle_receive(self):
        currency = self.currency_combo.currentText()
        try:
            balances = self.wallet_client.get_all_balances()
            address = balances.get(currency, {}).get("address", "N/A")
            self.status_label.setText(f"Receive {currency} at address: {address}")
        except Exception as e:
            self.status_label.setText(f"Error getting receive address: {e}")

    def handle_create_escrow(self):
        # For demo, use dialog or hardcoded values
        try:
            # TODO: Replace with real dialog for user input
            service_name = "demo_service"
            amount = 1.0
            provider_address = "provider123"
            result = self.escrow_client.create_escrow(service_name, amount, provider_address)
            self.status_label.setText(f"Escrow created: {result}")
            self.load_escrows()
        except Exception as e:
            self.status_label.setText(f"Create escrow failed: {e}")

    def handle_release_escrow(self):
        selected = self.escrow_list.currentItem()
        if not selected:
            self.status_label.setText("Select an escrow to release.")
            return
        escrow_id = selected.text().split("|")[0].strip()
        try:
            result = self.escrow_client.release_escrow(escrow_id)
            self.status_label.setText(f"Escrow released: {result}")
            self.load_escrows()
        except Exception as e:
            self.status_label.setText(f"Release escrow failed: {e}")

class TaskEngineTab(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.task_client = TaskClient()  # Uses default base_url
        layout = QVBoxLayout(self)

        # --- Engine Stats ---
        stats_group = QGroupBox("Engine Statistics")
        stats_layout = QHBoxLayout(stats_group)
        self.stats_label = QLabel("Loading stats...")
        stats_layout.addWidget(self.stats_label)
        self.refresh_stats_button = QPushButton("Refresh Stats")
        self.refresh_stats_button.clicked.connect(self.load_stats)
        stats_layout.addWidget(self.refresh_stats_button)
        self.test_api_button = QPushButton("Test API")
        self.test_api_button.clicked.connect(self.test_api)
        stats_layout.addWidget(self.test_api_button)
        layout.addWidget(stats_group)

        # --- Task List ---
        tasks_group = QGroupBox("Tasks")
        tasks_layout = QVBoxLayout(tasks_group)
        self.tasks_table = QTableWidget(0, 5)
        self.tasks_table.setHorizontalHeaderLabels(["ID", "Type", "Status", "Service", "Created"])
        self.tasks_table.horizontalHeader().setStretchLastSection(True)
        self.tasks_table.setSortingEnabled(True)
        self.tasks_table.cellClicked.connect(self.show_task_details)
        tasks_layout.addWidget(self.tasks_table)
        self.refresh_tasks_button = QPushButton("Refresh Tasks")
        self.refresh_tasks_button.clicked.connect(self.load_tasks)
        tasks_layout.addWidget(self.refresh_tasks_button)
        layout.addWidget(tasks_group)

        # --- Task Details ---
        details_group = QGroupBox("Task Details")
        details_layout = QVBoxLayout(details_group)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        layout.addWidget(details_group)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.load_stats()
        self.load_tasks()

    def load_stats(self):
        self.status_label.setText("Loading stats...")
        try:
            stats = self.task_client.get_statistics()
            text = " | ".join(f"{k}: {v}" for k, v in stats.items())
            self.stats_label.setText(text)
            self.status_label.clear()
        except Exception as e:
            self.stats_label.setText(f"Error loading stats: {e}")
            self.status_label.setText(f"Error loading stats: {e}")

    def load_tasks(self):
        self.status_label.setText("Loading tasks...")
        self.tasks_table.setRowCount(0)
        try:
            tasks = self.task_client.get_tasks()
            self.tasks_table.setRowCount(len(tasks))
            for i, task in enumerate(tasks):
                self.tasks_table.setItem(i, 0, QTableWidgetItem(str(task.get("id", ""))))
                self.tasks_table.setItem(i, 1, QTableWidgetItem(str(task.get("type", ""))))
                # Status with color/icon
                status = str(task.get("status", ""))
                status_item = QTableWidgetItem(status)
                if status == "COMPLETED":
                    status_item.setForeground(QColor("green"))
                elif status == "FAILED":
                    status_item.setForeground(QColor("red"))
                elif status == "RUNNING":
                    status_item.setForeground(QColor("blue"))
                else:
                    status_item.setForeground(QColor("darkGray"))
                self.tasks_table.setItem(i, 2, status_item)
                self.tasks_table.setItem(i, 3, QTableWidgetItem(str(task.get("service", ""))))
                self.tasks_table.setItem(i, 4, QTableWidgetItem(str(task.get("created_at", ""))))
            self.status_label.clear()
        except Exception as e:
            self.status_label.setText(f"Error loading tasks: {e}")

    def show_task_details(self, row, col):
        try:
            task_id = self.tasks_table.item(row, 0).text()
            task = self.task_client.get_task(task_id)
            self.details_text.setText(json.dumps(task, indent=2))
        except Exception as e:
            self.details_text.setText(f"Error loading task details: {e}")

    def test_api(self):
        try:
            stats = self.task_client.get_statistics()
            QMessageBox.information(self, "API Test", f"Task Engine API is reachable. Stats: {stats}")
        except Exception as e:
            QMessageBox.critical(self, "API Test", f"Task Engine API error: {e}")

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.settings_widget = SettingsWidget()
        layout.addWidget(self.settings_widget)
        # TODO: Connect theme changes

class MainWindow(QMainWindow):
    def __init__(self, api_client, wallet_client=None, *args, **kwargs):
        print("MainWindow __init__ starting")
        super().__init__(*args, **kwargs)
        print("super().__init__ done")
        self.api_client = api_client
        print("api_client set")
        self.wallet_client = wallet_client
        print("wallet_client set")
        self.current_user = None
        self.setWindowTitle("DuxOS API/App Store")
        self.resize(1200, 800)
        print("Window title and size set")

        # --- Tabbed navigation ---
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        print("QTabWidget created and set as central widget")

        # Store tab
        self.store_tab = StoreTab(self.api_client)
        print("StoreTab created")
        self.tabs.addTab(self.store_tab, "Store")
        print("StoreTab added")

        # Wallet tab
        self.wallet_tab = WalletTab(self.wallet_client)
        print("WalletTab created")
        self.tabs.addTab(self.wallet_tab, "Wallet")
        print("WalletTab added")

        # Task Engine tab
        self.task_engine_tab = TaskEngineTab(self.api_client)
        print("TaskEngineTab created")
        self.tabs.addTab(self.task_engine_tab, "Task Engine")
        print("TaskEngineTab added")

        # Settings tab
        self.settings_tab = SettingsTab()
        print("SettingsTab created")
        self.tabs.addTab(self.settings_tab, "Settings")
        print("SettingsTab added")

        # Modernize look & feel
        self.apply_theme("default")
        print("Theme applied")
        self.settings_tab.settings_widget.settings_changed.connect(self.handle_settings_changed)
        print("Settings changed signal connected")

        # Setup menu bar
        self.setup_menu_bar()
        print("Menu bar set up")

        # User account dock
        self.setup_user_account_dock()
        print("User account dock set up")

    def apply_theme(self, theme):
        if theme == "dark":
            self.setStyle(QStyleFactory.create("Fusion"))
            dark_palette = self.palette()
            dark_palette.setColor(self.backgroundRole(), QColor("black"))
            self.setPalette(dark_palette)
        elif theme == "light":
            self.setStyle(QStyleFactory.create("Fusion"))
            light_palette = self.palette()
            light_palette.setColor(self.backgroundRole(), QColor("white"))
            self.setPalette(light_palette)
        else:
            self.setStyle(QStyleFactory.create("Fusion"))
            self.setPalette(QApplication.palette())

    def handle_settings_changed(self, settings):
        self.apply_theme(settings.get("theme", "default"))

    def setup_user_account_dock(self):
        if self.wallet_client:
            self.user_account_widget = UserAccountWidget(self.api_client, self.wallet_client)
            self.user_account_widget.login_requested.connect(self.handle_user_login)
            self.user_account_widget.logout_requested.connect(self.handle_user_logout)
            # Connect key access signals
            if hasattr(self.user_account_widget, "show_public_key_dialog"):
                self.user_account_widget.show_public_key_dialog.connect(self.handle_show_public_key)
            if hasattr(self.user_account_widget, "show_private_key_dialog"):
                self.user_account_widget.show_private_key_dialog.connect(self.handle_show_private_key)
            dock = QDockWidget("User Account", self)
            dock.setWidget(self.user_account_widget)
            dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
            self.addDockWidget(Qt.RightDockWidgetArea, dock)

    def handle_show_public_key(self, currency, password):
        try:
            pubkey = self.wallet_client.get_public_key(currency, password=password)
            QMessageBox.information(self, "Public Key", f"{currency} Public Key:\n{pubkey}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not retrieve public key: {e}")

    def handle_show_private_key(self, currency, password):
        confirm = QMessageBox.question(
            self,
            "Reveal Private Key",
            f"Are you sure you want to reveal your {currency} private key?\nNever share this with anyone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                privkey = self.wallet_client.get_private_key(currency, password=password)
                QMessageBox.information(self, "Private Key", f"{currency} Private Key:\n{privkey}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not retrieve private key: {e}")

    def handle_user_login(self, user_id, user_name, password):
        self.current_user = {"user_id": user_id, "user_name": user_name, "password": password}
        QMessageBox.information(self, "Login", f"Welcome, {user_name}!")
        return None

    def handle_user_logout(self):
        self.current_user = None
        QMessageBox.information(self, "Logout", "You have been logged out.")
        return None

    def setup_menu_bar(self):
        menubar = self.menuBar()
        if menubar is not None:
            file_menu = menubar.addMenu("File")
            if file_menu is not None:
                exit_action = QAction("Exit", self)
                exit_action.triggered.connect(lambda: (self.close(), None)[-1])
                file_menu.addAction(exit_action)
            help_menu = menubar.addMenu("Help")
            if help_menu is not None:
                about_action = QAction("About", self)
                about_action.triggered.connect(self.show_about)
                help_menu.addAction(about_action)

    def show_about(self):
        QMessageBox.about(self, "About DuxOS Desktop", "DuxOS Desktop\nMulti-crypto, Escrow, Task Engine, Modern UI\nhttps://github.com/ducks-github/DuxNet")
