"""
Advanced Features UI for DuxOS Desktop

Provides integration with multi-crypto wallet, escrow management, 
task engine, and daemon management features.
"""

from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
    QProgressBar,
    QMessageBox,
    QSplitter,
    QFrame,
    QHeaderView,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
)

import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime


class MultiCryptoWalletWidget(QWidget):
    """Multi-cryptocurrency wallet management widget"""
    
    def __init__(self, wallet_client, parent=None):
        super().__init__(parent)
        self.wallet_client = wallet_client
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_balances)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        self.setup_ui()
        self.refresh_balances()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Multi-Cryptocurrency Wallet")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Balances section
        balances_group = QGroupBox("Wallet Balances")
        balances_layout = QVBoxLayout(balances_group)
        
        self.balances_table = QTableWidget()
        self.balances_table.setColumnCount(4)
        self.balances_table.setHorizontalHeaderLabels(["Currency", "Balance", "Address", "Actions"])
        self.balances_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        balances_layout.addWidget(self.balances_table)
        
        layout.addWidget(balances_group)
        
        # Send transaction section
        send_group = QGroupBox("Send Transaction")
        send_layout = QFormLayout(send_group)
        
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["BTC", "ETH", "FLOP", "USDT", "BNB", "XRP", "SOL", "ADA", "DOGE", "TON", "TRX"])
        send_layout.addRow("Currency:", self.currency_combo)
        
        self.to_address_input = QLineEdit()
        self.to_address_input.setPlaceholderText("Enter recipient address")
        send_layout.addRow("To Address:", self.to_address_input)
        
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0.000001, 1000000.0)
        self.amount_input.setDecimals(8)
        send_layout.addRow("Amount:", self.amount_input)
        
        self.send_button = QPushButton("Send Transaction")
        self.send_button.clicked.connect(self.send_transaction)
        send_layout.addRow("", self.send_button)
        
        layout.addWidget(send_group)
        
        # Transaction history
        history_group = QGroupBox("Transaction History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Date", "Currency", "Type", "Amount", "Status"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.history_table)
        
        layout.addWidget(history_group)
    
    def refresh_balances(self):
        """Refresh wallet balances"""
        try:
            # Get balances for all currencies
            balances = self.wallet_client.get_all_balances()
            
            self.balances_table.setRowCount(len(balances))
            for i, (currency, balance_info) in enumerate(balances.items()):
                self.balances_table.setItem(i, 0, QTableWidgetItem(currency))
                self.balances_table.setItem(i, 1, QTableWidgetItem(f"{balance_info['balance']:.8f}"))
                self.balances_table.setItem(i, 2, QTableWidgetItem(balance_info.get('address', 'N/A')))
                
                # Add refresh button
                refresh_btn = QPushButton("Refresh")
                refresh_btn.clicked.connect(lambda checked, c=currency: self.refresh_currency_balance(c))
                self.balances_table.setCellWidget(i, 3, refresh_btn)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh balances: {e}")
    
    def refresh_currency_balance(self, currency):
        """Refresh balance for specific currency"""
        try:
            balance = self.wallet_client.get_balance(currency)
            # Update the balance in the table
            for i in range(self.balances_table.rowCount()):
                if self.balances_table.item(i, 0).text() == currency:
                    self.balances_table.item(i, 1).setText(f"{balance:.8f}")
                    break
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh {currency} balance: {e}")
    
    def send_transaction(self):
        """Send a transaction"""
        try:
            currency = self.currency_combo.currentText()
            to_address = self.to_address_input.text().strip()
            amount = self.amount_input.value()
            
            if not to_address:
                QMessageBox.warning(self, "Error", "Please enter a recipient address")
                return
            
            if amount <= 0:
                QMessageBox.warning(self, "Error", "Amount must be greater than 0")
                return
            
            # Send transaction
            txid = self.wallet_client.send_transaction(currency, to_address, amount)
            
            QMessageBox.information(self, "Success", f"Transaction sent! TXID: {txid}")
            
            # Clear inputs
            self.to_address_input.clear()
            self.amount_input.setValue(0.0)
            
            # Refresh balances
            self.refresh_balances()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send transaction: {e}")


class EscrowManagementWidget(QWidget):
    """Escrow management and monitoring widget"""
    
    def __init__(self, escrow_client, parent=None):
        super().__init__(parent)
        self.escrow_client = escrow_client
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_escrows)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
        self.setup_ui()
        self.refresh_escrows()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Escrow Management")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Active escrows
        active_group = QGroupBox("Active Escrows")
        active_layout = QVBoxLayout(active_group)
        
        self.escrows_table = QTableWidget()
        self.escrows_table.setColumnCount(7)
        self.escrows_table.setHorizontalHeaderLabels([
            "ID", "Service", "Amount", "Status", "Created", "Provider", "Actions"
        ])
        self.escrows_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        active_layout.addWidget(self.escrows_table)
        
        layout.addWidget(active_group)
        
        # Community fund info
        fund_group = QGroupBox("Community Fund")
        fund_layout = QFormLayout(fund_group)
        
        self.fund_balance_label = QLabel("Loading...")
        fund_layout.addRow("Balance:", self.fund_balance_label)
        
        self.airdrop_threshold_label = QLabel("Loading...")
        fund_layout.addRow("Airdrop Threshold:", self.airdrop_threshold_label)
        
        self.last_airdrop_label = QLabel("Loading...")
        fund_layout.addRow("Last Airdrop:", self.last_airdrop_label)
        
        layout.addWidget(fund_group)
        
        # Create escrow section
        create_group = QGroupBox("Create Escrow")
        create_layout = QFormLayout(create_group)
        
        self.service_name_input = QLineEdit()
        self.service_name_input.setPlaceholderText("Enter service name")
        create_layout.addRow("Service Name:", self.service_name_input)
        
        self.escrow_amount_input = QDoubleSpinBox()
        self.escrow_amount_input.setRange(0.1, 100000.0)
        self.escrow_amount_input.setDecimals(8)
        create_layout.addRow("Amount:", self.escrow_amount_input)
        
        self.provider_address_input = QLineEdit()
        self.provider_address_input.setPlaceholderText("Enter provider address")
        create_layout.addRow("Provider Address:", self.provider_address_input)
        
        self.create_escrow_button = QPushButton("Create Escrow")
        self.create_escrow_button.clicked.connect(self.create_escrow)
        create_layout.addRow("", self.create_escrow_button)
        
        layout.addWidget(create_group)
    
    def refresh_escrows(self):
        """Refresh escrow list"""
        try:
            escrows = self.escrow_client.get_active_escrows()
            
            self.escrows_table.setRowCount(len(escrows))
            for i, escrow in enumerate(escrows):
                self.escrows_table.setItem(i, 0, QTableWidgetItem(escrow['id'][:8]))
                self.escrows_table.setItem(i, 1, QTableWidgetItem(escrow['service_name']))
                self.escrows_table.setItem(i, 2, QTableWidgetItem(f"{escrow['amount']:.8f}"))
                self.escrows_table.setItem(i, 3, QTableWidgetItem(escrow['status']))
                self.escrows_table.setItem(i, 4, QTableWidgetItem(escrow['created_at'][:10]))
                self.escrows_table.setItem(i, 5, QTableWidgetItem(escrow['provider_wallet_id']))
                
                # Add action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if escrow['status'] == 'ACTIVE':
                    release_btn = QPushButton("Release")
                    release_btn.clicked.connect(lambda checked, eid=escrow['id']: self.release_escrow(eid))
                    actions_layout.addWidget(release_btn)
                
                dispute_btn = QPushButton("Dispute")
                dispute_btn.clicked.connect(lambda checked, eid=escrow['id']: self.create_dispute(eid))
                actions_layout.addWidget(dispute_btn)
                
                self.escrows_table.setCellWidget(i, 6, actions_widget)
            
            # Refresh community fund info
            fund_info = self.escrow_client.get_community_fund_info()
            self.fund_balance_label.setText(f"{fund_info['balance']:.8f} FLOP")
            self.airdrop_threshold_label.setText(f"{fund_info['airdrop_threshold']:.8f} FLOP")
            self.last_airdrop_label.setText(fund_info.get('last_airdrop', 'Never'))
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh escrows: {e}")
    
    def create_escrow(self):
        """Create a new escrow"""
        try:
            service_name = self.service_name_input.text().strip()
            amount = self.escrow_amount_input.value()
            provider_address = self.provider_address_input.text().strip()
            
            if not service_name or not provider_address:
                QMessageBox.warning(self, "Error", "Please fill in all fields")
                return
            
            escrow = self.escrow_client.create_escrow(
                service_name=service_name,
                amount=amount,
                provider_address=provider_address
            )
            
            QMessageBox.information(self, "Success", f"Escrow created! ID: {escrow['id']}")
            
            # Clear inputs
            self.service_name_input.clear()
            self.escrow_amount_input.setValue(0.1)
            self.provider_address_input.clear()
            
            # Refresh list
            self.refresh_escrows()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create escrow: {e}")
    
    def release_escrow(self, escrow_id):
        """Release an escrow"""
        try:
            result = self.escrow_client.release_escrow(escrow_id)
            QMessageBox.information(self, "Success", f"Escrow {escrow_id} released successfully!")
            self.refresh_escrows()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to release escrow: {e}")
    
    def create_dispute(self, escrow_id):
        """Create a dispute for an escrow"""
        try:
            reason, ok = QInputDialog.getText(self, "Create Dispute", "Enter dispute reason:")
            if ok and reason:
                dispute = self.escrow_client.create_dispute(escrow_id, reason)
                QMessageBox.information(self, "Success", f"Dispute created for escrow {escrow_id}")
                self.refresh_escrows()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create dispute: {e}")


class TaskEngineWidget(QWidget):
    """Task engine management and monitoring widget"""
    
    def __init__(self, task_client, parent=None):
        super().__init__(parent)
        self.task_client = task_client
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
        self.setup_ui()
        self.refresh_tasks()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Task Engine Management")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Split view
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Task submission
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        submit_group = QGroupBox("Submit Task")
        submit_layout = QFormLayout(submit_group)
        
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems(["API_CALL", "BATCH_PROCESSING", "MACHINE_LEARNING", "DATA_ANALYSIS", "IMAGE_PROCESSING"])
        submit_layout.addRow("Task Type:", self.task_type_combo)
        
        self.service_name_input = QLineEdit()
        self.service_name_input.setPlaceholderText("Enter service name")
        submit_layout.addRow("Service Name:", self.service_name_input)
        
        self.task_code_input = QTextEdit()
        self.task_code_input.setMaximumHeight(100)
        self.task_code_input.setPlaceholderText("Enter task code or API endpoint")
        submit_layout.addRow("Task Code:", self.task_code_input)
        
        self.payment_amount_input = QDoubleSpinBox()
        self.payment_amount_input.setRange(0.1, 1000.0)
        self.payment_amount_input.setDecimals(8)
        submit_layout.addRow("Payment Amount:", self.payment_amount_input)
        
        self.submit_task_button = QPushButton("Submit Task")
        self.submit_task_button.clicked.connect(self.submit_task)
        submit_layout.addRow("", self.submit_task_button)
        
        left_layout.addWidget(submit_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.total_tasks_label = QLabel("0")
        stats_layout.addRow("Total Tasks:", self.total_tasks_label)
        
        self.active_tasks_label = QLabel("0")
        stats_layout.addRow("Active Tasks:", self.active_tasks_label)
        
        self.completed_tasks_label = QLabel("0")
        stats_layout.addRow("Completed Tasks:", self.completed_tasks_label)
        
        self.success_rate_label = QLabel("0%")
        stats_layout.addRow("Success Rate:", self.success_rate_label)
        
        left_layout.addWidget(stats_group)
        
        splitter.addWidget(left_widget)
        
        # Right side - Task monitoring
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        tasks_group = QGroupBox("Task Monitoring")
        tasks_layout = QVBoxLayout(tasks_group)
        
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(7)
        self.tasks_table.setHorizontalHeaderLabels([
            "ID", "Type", "Service", "Status", "Progress", "Payment", "Actions"
        ])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tasks_layout.addWidget(self.tasks_table)
        
        right_layout.addWidget(tasks_group)
        
        splitter.addWidget(right_widget)
        
        layout.addWidget(splitter)
    
    def refresh_tasks(self):
        """Refresh task list and statistics"""
        try:
            # Get tasks
            tasks = self.task_client.get_tasks()
            
            self.tasks_table.setRowCount(len(tasks))
            for i, task in enumerate(tasks):
                self.tasks_table.setItem(i, 0, QTableWidgetItem(task['task_id'][:8]))
                self.tasks_table.setItem(i, 1, QTableWidgetItem(task['task_type']))
                self.tasks_table.setItem(i, 2, QTableWidgetItem(task['service_name']))
                self.tasks_table.setItem(i, 3, QTableWidgetItem(task['status']))
                
                # Progress bar
                progress = QProgressBar()
                if task['status'] == 'COMPLETED':
                    progress.setValue(100)
                elif task['status'] == 'RUNNING':
                    progress.setValue(50)
                else:
                    progress.setValue(0)
                self.tasks_table.setCellWidget(i, 4, progress)
                
                self.tasks_table.setItem(i, 5, QTableWidgetItem(f"{task['payment_amount']:.8f}"))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if task['status'] == 'PENDING':
                    cancel_btn = QPushButton("Cancel")
                    cancel_btn.clicked.connect(lambda checked, tid=task['task_id']: self.cancel_task(tid))
                    actions_layout.addWidget(cancel_btn)
                
                view_btn = QPushButton("View")
                view_btn.clicked.connect(lambda checked, tid=task['task_id']: self.view_task(tid))
                actions_layout.addWidget(view_btn)
                
                self.tasks_table.setCellWidget(i, 6, actions_widget)
            
            # Update statistics
            stats = self.task_client.get_statistics()
            self.total_tasks_label.setText(str(stats['total_tasks']))
            self.active_tasks_label.setText(str(stats['active_tasks']))
            self.completed_tasks_label.setText(str(stats['completed_tasks']))
            self.success_rate_label.setText(f"{stats['success_rate']:.1f}%")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh tasks: {e}")
    
    def submit_task(self):
        """Submit a new task"""
        try:
            task_type = self.task_type_combo.currentText()
            service_name = self.service_name_input.text().strip()
            code = self.task_code_input.toPlainText().strip()
            payment_amount = self.payment_amount_input.value()
            
            if not service_name or not code:
                QMessageBox.warning(self, "Error", "Please fill in all fields")
                return
            
            task = self.task_client.submit_task(
                task_type=task_type,
                service_name=service_name,
                code=code,
                payment_amount=payment_amount
            )
            
            QMessageBox.information(self, "Success", f"Task submitted! ID: {task['task_id']}")
            
            # Clear inputs
            self.service_name_input.clear()
            self.task_code_input.clear()
            self.payment_amount_input.setValue(0.1)
            
            # Refresh list
            self.refresh_tasks()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit task: {e}")
    
    def cancel_task(self, task_id):
        """Cancel a task"""
        try:
            result = self.task_client.cancel_task(task_id)
            QMessageBox.information(self, "Success", f"Task {task_id} cancelled")
            self.refresh_tasks()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to cancel task: {e}")
    
    def view_task(self, task_id):
        """View task details"""
        try:
            task = self.task_client.get_task(task_id)
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Task Details - {task_id[:8]}")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Task details
            details_text = QTextEdit()
            details_text.setPlainText(json.dumps(task, indent=2))
            details_text.setReadOnly(True)
            layout.addWidget(details_text)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view task: {e}")


class DaemonManagerWidget(QWidget):
    """Daemon management and monitoring widget"""
    
    def __init__(self, daemon_client, parent=None):
        super().__init__(parent)
        self.daemon_client = daemon_client
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_daemons)
        self.refresh_timer.start(15000)  # Refresh every 15 seconds
        self.setup_ui()
        self.refresh_daemons()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Daemon Manager")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Daemon controls
        controls_group = QGroupBox("Daemon Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.daemon_combo = QComboBox()
        self.daemon_combo.addItems(["bitcoind", "ethereumd", "flopcoind", "litecoind", "dogecoind"])
        controls_layout.addWidget(QLabel("Daemon:"))
        controls_layout.addWidget(self.daemon_combo)
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_daemon)
        controls_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_daemon)
        controls_layout.addWidget(self.stop_button)
        
        self.restart_button = QPushButton("Restart")
        self.restart_button.clicked.connect(self.restart_daemon)
        controls_layout.addWidget(self.restart_button)
        
        layout.addWidget(controls_group)
        
        # Daemon status
        status_group = QGroupBox("Daemon Status")
        status_layout = QVBoxLayout(status_group)
        
        self.daemons_table = QTableWidget()
        self.daemons_table.setColumnCount(6)
        self.daemons_table.setHorizontalHeaderLabels([
            "Daemon", "Status", "Uptime", "Sync Progress", "Connections", "Actions"
        ])
        self.daemons_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        status_layout.addWidget(self.daemons_table)
        
        layout.addWidget(status_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout(config_group)
        
        self.config_path_input = QLineEdit()
        self.config_path_input.setPlaceholderText("Path to daemon configuration")
        config_layout.addRow("Config Path:", self.config_path_input)
        
        self.data_dir_input = QLineEdit()
        self.data_dir_input.setPlaceholderText("Path to daemon data directory")
        config_layout.addRow("Data Directory:", self.data_dir_input)
        
        self.rpc_port_input = QSpinBox()
        self.rpc_port_input.setRange(1024, 65535)
        self.rpc_port_input.setValue(8332)
        config_layout.addRow("RPC Port:", self.rpc_port_input)
        
        self.save_config_button = QPushButton("Save Configuration")
        self.save_config_button.clicked.connect(self.save_config)
        config_layout.addRow("", self.save_config_button)
        
        layout.addWidget(config_group)
    
    def refresh_daemons(self):
        """Refresh daemon status"""
        try:
            daemons = self.daemon_client.get_daemon_status()
            
            self.daemons_table.setRowCount(len(daemons))
            for i, daemon in enumerate(daemons):
                self.daemons_table.setItem(i, 0, QTableWidgetItem(daemon['name']))
                
                # Status with color
                status_item = QTableWidgetItem(daemon['status'])
                if daemon['status'] == 'running':
                    status_item.setBackground(Qt.green)
                elif daemon['status'] == 'stopped':
                    status_item.setBackground(Qt.red)
                elif daemon['status'] == 'syncing':
                    status_item.setBackground(Qt.yellow)
                self.daemons_table.setItem(i, 1, status_item)
                
                self.daemons_table.setItem(i, 2, QTableWidgetItem(daemon.get('uptime', 'N/A')))
                
                # Sync progress bar
                sync_progress = QProgressBar()
                sync_progress.setValue(daemon.get('sync_progress', 0))
                self.daemons_table.setCellWidget(i, 3, sync_progress)
                
                self.daemons_table.setItem(i, 4, QTableWidgetItem(str(daemon.get('connections', 0))))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                if daemon['status'] == 'running':
                    stop_btn = QPushButton("Stop")
                    stop_btn.clicked.connect(lambda checked, name=daemon['name']: self.stop_daemon(name))
                    actions_layout.addWidget(stop_btn)
                else:
                    start_btn = QPushButton("Start")
                    start_btn.clicked.connect(lambda checked, name=daemon['name']: self.start_daemon(name))
                    actions_layout.addWidget(start_btn)
                
                restart_btn = QPushButton("Restart")
                restart_btn.clicked.connect(lambda checked, name=daemon['name']: self.restart_daemon(name))
                actions_layout.addWidget(restart_btn)
                
                self.daemons_table.setCellWidget(i, 5, actions_widget)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh daemons: {e}")
    
    def start_daemon(self, daemon_name=None):
        """Start a daemon"""
        try:
            if daemon_name is None:
                daemon_name = self.daemon_combo.currentText()
            
            result = self.daemon_client.start_daemon(daemon_name)
            QMessageBox.information(self, "Success", f"Started {daemon_name}")
            self.refresh_daemons()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start {daemon_name}: {e}")
    
    def stop_daemon(self, daemon_name=None):
        """Stop a daemon"""
        try:
            if daemon_name is None:
                daemon_name = self.daemon_combo.currentText()
            
            result = self.daemon_client.stop_daemon(daemon_name)
            QMessageBox.information(self, "Success", f"Stopped {daemon_name}")
            self.refresh_daemons()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop {daemon_name}: {e}")
    
    def restart_daemon(self, daemon_name=None):
        """Restart a daemon"""
        try:
            if daemon_name is None:
                daemon_name = self.daemon_combo.currentText()
            
            result = self.daemon_client.restart_daemon(daemon_name)
            QMessageBox.information(self, "Success", f"Restarted {daemon_name}")
            self.refresh_daemons()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restart {daemon_name}: {e}")
    
    def save_config(self):
        """Save daemon configuration"""
        try:
            config = {
                'config_path': self.config_path_input.text(),
                'data_dir': self.data_dir_input.text(),
                'rpc_port': self.rpc_port_input.value()
            }
            
            result = self.daemon_client.save_config(config)
            QMessageBox.information(self, "Success", "Configuration saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")


class AdvancedFeaturesTab(QWidget):
    """Main advanced features tab widget"""
    
    def __init__(self, api_client, wallet_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.wallet_client = wallet_client
        
        # Initialize clients for advanced features
        self.escrow_client = EscrowClient()
        self.task_client = TaskClient()
        self.daemon_client = DaemonClient()
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Multi-crypto wallet tab
        self.wallet_tab = MultiCryptoWalletWidget(self.wallet_client)
        self.tab_widget.addTab(self.wallet_tab, "Multi-Crypto Wallet")
        
        # Escrow management tab
        self.escrow_tab = EscrowManagementWidget(self.escrow_client)
        self.tab_widget.addTab(self.escrow_tab, "Escrow Management")
        
        # Task engine tab
        self.task_tab = TaskEngineWidget(self.task_client)
        self.tab_widget.addTab(self.task_tab, "Task Engine")
        
        # Daemon manager tab
        self.daemon_tab = DaemonManagerWidget(self.daemon_client)
        self.tab_widget.addTab(self.daemon_tab, "Daemon Manager")
        
        layout.addWidget(self.tab_widget)


# Client classes for API communication
class EscrowClient:
    """Client for escrow service API"""
    
    def __init__(self, base_url="http://localhost:8004"):
        self.base_url = base_url
    
    def get_active_escrows(self):
        """Get active escrows"""
        response = requests.get(f"{self.base_url}/escrows")
        response.raise_for_status()
        return response.json()
    
    def create_escrow(self, service_name, amount, provider_address):
        """Create a new escrow"""
        data = {
            "service_name": service_name,
            "amount": amount,
            "provider_address": provider_address
        }
        response = requests.post(f"{self.base_url}/escrows", json=data)
        response.raise_for_status()
        return response.json()
    
    def release_escrow(self, escrow_id):
        """Release an escrow"""
        response = requests.post(f"{self.base_url}/escrows/{escrow_id}/release")
        response.raise_for_status()
        return response.json()
    
    def create_dispute(self, escrow_id, reason):
        """Create a dispute"""
        data = {"reason": reason}
        response = requests.post(f"{self.base_url}/escrows/{escrow_id}/disputes", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_community_fund_info(self):
        """Get community fund information"""
        response = requests.get(f"{self.base_url}/community-fund")
        response.raise_for_status()
        return response.json()


class TaskClient:
    """Client for task engine API"""
    
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
    
    def get_tasks(self):
        """Get all tasks"""
        response = requests.get(f"{self.base_url}/tasks")
        response.raise_for_status()
        return response.json()
    
    def submit_task(self, task_type, service_name, code, payment_amount):
        """Submit a new task"""
        data = {
            "task_type": task_type,
            "service_name": service_name,
            "code": code,
            "payment_amount": payment_amount
        }
        response = requests.post(f"{self.base_url}/tasks", json=data)
        response.raise_for_status()
        return response.json()
    
    def cancel_task(self, task_id):
        """Cancel a task"""
        response = requests.post(f"{self.base_url}/tasks/{task_id}/cancel")
        response.raise_for_status()
        return response.json()
    
    def get_task(self, task_id):
        """Get task details"""
        response = requests.get(f"{self.base_url}/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    def get_statistics(self):
        """Get task engine statistics"""
        response = requests.get(f"{self.base_url}/statistics")
        response.raise_for_status()
        return response.json()


class DaemonClient:
    """Client for daemon manager API"""
    
    def __init__(self, base_url="http://localhost:8003"):
        self.base_url = base_url
    
    def get_daemon_status(self):
        """Get status of all daemons"""
        response = requests.get(f"{self.base_url}/daemons/status")
        response.raise_for_status()
        return response.json()
    
    def start_daemon(self, daemon_name):
        """Start a daemon"""
        response = requests.post(f"{self.base_url}/daemons/{daemon_name}/start")
        response.raise_for_status()
        return response.json()
    
    def stop_daemon(self, daemon_name):
        """Stop a daemon"""
        response = requests.post(f"{self.base_url}/daemons/{daemon_name}/stop")
        response.raise_for_status()
        return response.json()
    
    def restart_daemon(self, daemon_name):
        """Restart a daemon"""
        response = requests.post(f"{self.base_url}/daemons/{daemon_name}/restart")
        response.raise_for_status()
        return response.json()
    
    def save_config(self, config):
        """Save daemon configuration"""
        response = requests.post(f"{self.base_url}/daemons/config", json=config)
        response.raise_for_status()
        return response.json() 