"""
Wallet Service for DuxOS Registry

This module provides wallet functionality integrated with the node registry system,
including address generation, balance checking, transaction management, and
integration with the Flopcoin blockchain.
"""

import logging
import os
import yaml
import requests
import json
import hashlib
import hmac
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal

from ..db.database import get_db
from ..db.repository import WalletRepository, TransactionRepository
from ..models.database_models import Wallet, Transaction, WalletCapability
from .auth_service import NodeAuthService, AuthLevel

logger = logging.getLogger(__name__)


class FlopcoinWalletService:
    """Real Flopcoin Core wallet service for DuxOS Node Registry"""
    
    def __init__(self, rpc_host: str = "127.0.0.1", rpc_port: int = 32553, 
                 rpc_user: str = "flopcoinrpc", rpc_password: str = "password123"):
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.rpc_url = f"http://{rpc_host}:{rpc_port}"
        self.auth = (rpc_user, rpc_password)
        
        # Flopcoin-specific constants
        self.MIN_CONFIRMATIONS = 6
        self.DEFAULT_FEE = Decimal('0.001')
        self.MIN_FEE = Decimal('0.0001')
        self.MAX_FEE = Decimal('0.01')
        
        # Test connection on initialization
        self._test_connection()
    
    def _make_rpc_call(self, method: str, params: Optional[List] = None) -> Dict:
        """Make RPC call to Flopcoin Core"""
        if params is None:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        try:
            response = requests.post(
                self.rpc_url,
                json=payload,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'error' in result and result['error'] is not None:
                    raise Exception(f"RPC Error: {result['error']}")
                return result.get('result', {})
            else:
                raise Exception(f"HTTP Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"RPC request failed: {e}")
            raise Exception(f"Connection failed: {e}")
    
    def _test_connection(self) -> bool:
        """Test connection to Flopcoin Core"""
        try:
            info = self._make_rpc_call("getinfo")
            logger.info(f"Connected to Flopcoin Core v{info.get('version', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Flopcoin Core: {e}")
            raise
    
    def get_wallet_info(self) -> Dict:
        """Get wallet information"""
        try:
            info = self._make_rpc_call("getinfo")
            balance = self._make_rpc_call("getbalance")
            
            return {
                "wallet_name": "duxos_wallet",
                "balance": float(balance) if balance is not None else 0.0,
                "version": info.get('version', 0),
                "blocks": info.get('blocks', 0),
                "connections": info.get('connections', 0),
                "difficulty": info.get('difficulty', 0),
                "testnet": info.get('testnet', False),
                "keypool_size": info.get('keypoolsize', 0),
                "pay_tx_fee": info.get('paytxfee', 0),
                "relay_fee": info.get('relayfee', 0),
                "errors": info.get('errors', ''),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting wallet info: {e}")
            raise
    
    def get_balance(self, account: str = "") -> Dict:
        """Get wallet balance"""
        try:
            balance = self._make_rpc_call("getbalance", [account])
            unconfirmed = self._make_rpc_call("getunconfirmedbalance")
            
            confirmed_balance = float(balance) if balance is not None else 0.0
            unconfirmed_balance = float(unconfirmed) if unconfirmed is not None else 0.0
            
            return {
                "confirmed": confirmed_balance,
                "unconfirmed": unconfirmed_balance,
                "total": confirmed_balance + unconfirmed_balance,
                "account": account,
                "currency": "FLOP"
            }
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            raise
    
    def get_new_address(self, account: str = "") -> Dict:
        """Generate new Flopcoin address"""
        try:
            address = self._make_rpc_call("getnewaddress", [account])
            
            return {
                "address": address,
                "account": account,
                "type": "legacy",  # Flopcoin uses legacy addresses
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating new address: {e}")
            raise
    
    def get_addresses(self, account: str = "") -> List[Dict]:
        """Get all addresses for an account"""
        try:
            addresses = self._make_rpc_call("getaddressesbyaccount", [account])
            
            result = []
            for address in addresses:
                # Get address info
                try:
                    info = self._make_rpc_call("validateaddress", [address])
                    result.append({
                        "address": address,
                        "account": account,
                        "is_valid": info.get('isvalid', False),
                        "is_mine": info.get('ismine', False),
                        "is_watch_only": info.get('iswatchonly', False),
                        "pubkey": info.get('pubkey', ''),
                        "is_script": info.get('isscript', False),
                        "is_change": info.get('ischange', False)
                    })
                except:
                    # Skip addresses that can't be validated
                    continue
            
            return result
        except Exception as e:
            logger.error(f"Error getting addresses: {e}")
            raise
    
    def send_transaction(self, to_address: str, amount: float, 
                        fee: Optional[float] = None, 
                        comment: str = "") -> Dict:
        """Send Flopcoin transaction"""
        try:
            # Validate address
            address_info = self._make_rpc_call("validateaddress", [to_address])
            if not address_info.get('isvalid', False):
                raise Exception(f"Invalid address: {to_address}")
            
            # Use default fee if not specified
            if fee is None:
                fee = float(self.DEFAULT_FEE)
            
            # Validate fee
            if fee < float(self.MIN_FEE) or fee > float(self.MAX_FEE):
                raise Exception(f"Fee must be between {self.MIN_FEE} and {self.MAX_FEE} FLOP")
            
            # Send transaction
            txid = self._make_rpc_call("sendtoaddress", [to_address, amount, comment, comment])
            
            # Get transaction details
            tx_info = self._make_rpc_call("gettransaction", [txid])
            
            return {
                "txid": txid,
                "amount": amount,
                "fee": fee,
                "to_address": to_address,
                "comment": comment,
                "confirmations": tx_info.get('confirmations', 0),
                "time": tx_info.get('time', 0),
                "timereceived": tx_info.get('timereceived', 0),
                "category": tx_info.get('category', 'send'),
                "status": "pending" if tx_info.get('confirmations', 0) < self.MIN_CONFIRMATIONS else "confirmed"
            }
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            raise
    
    def get_transaction(self, txid: str) -> Dict:
        """Get transaction details"""
        try:
            tx_info = self._make_rpc_call("gettransaction", [txid])
            
            return {
                "txid": txid,
                "amount": tx_info.get('amount', 0),
                "fee": tx_info.get('fee', 0),
                "confirmations": tx_info.get('confirmations', 0),
                "time": tx_info.get('time', 0),
                "timereceived": tx_info.get('timereceived', 0),
                "category": tx_info.get('category', ''),
                "address": tx_info.get('address', ''),
                "comment": tx_info.get('comment', ''),
                "status": "confirmed" if tx_info.get('confirmations', 0) >= self.MIN_CONFIRMATIONS else "pending"
            }
        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            raise
    
    def get_transaction_history(self, account: str = "", count: int = 10) -> List[Dict]:
        """Get transaction history"""
        try:
            transactions = self._make_rpc_call("listtransactions", [account, count])
            
            result = []
            for tx in transactions:
                result.append({
                    "txid": tx.get('txid', ''),
                    "amount": tx.get('amount', 0),
                    "fee": tx.get('fee', 0),
                    "confirmations": tx.get('confirmations', 0),
                    "time": tx.get('time', 0),
                    "timereceived": tx.get('timereceived', 0),
                    "category": tx.get('category', ''),
                    "address": tx.get('address', ''),
                    "account": tx.get('account', ''),
                    "comment": tx.get('comment', ''),
                    "status": "confirmed" if tx.get('confirmations', 0) >= self.MIN_CONFIRMATIONS else "pending"
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting transaction history: {e}")
            raise
    
    def backup_wallet(self, backup_path: str) -> Dict:
        """Backup wallet"""
        try:
            result = self._make_rpc_call("backupwallet", [backup_path])
            
            return {
                "success": True,
                "backup_path": backup_path,
                "backup_time": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error backing up wallet: {e}")
            raise
    
    def get_network_info(self) -> Dict:
        """Get network information"""
        try:
            info = self._make_rpc_call("getinfo")
            
            return {
                "version": info.get('version', 0),
                "protocol_version": info.get('protocolversion', 0),
                "blocks": info.get('blocks', 0),
                "connections": info.get('connections', 0),
                "difficulty": info.get('difficulty', 0),
                "testnet": info.get('testnet', False),
                "relay_fee": info.get('relayfee', 0),
                "errors": info.get('errors', ''),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            raise
    
    def get_blockchain_info(self) -> Dict:
        """Get blockchain information"""
        try:
            info = self._make_rpc_call("getblockchaininfo")
            
            return {
                "chain": info.get('chain', ''),
                "blocks": info.get('blocks', 0),
                "headers": info.get('headers', 0),
                "best_block_hash": info.get('bestblockhash', ''),
                "difficulty": info.get('difficulty', 0),
                "verification_progress": info.get('verificationprogress', 0),
                "chain_work": info.get('chainwork', ''),
                "pruned": info.get('pruned', False),
                "prune_height": info.get('pruneheight', 0),
                "automatic_pruning": info.get('automatic_pruning', False),
                "prune_target_size": info.get('prune_target_size', 0),
                "softforks": info.get('softforks', {}),
                "bip9_softforks": info.get('bip9_softforks', {}),
                "warnings": info.get('warnings', ''),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting blockchain info: {e}")
            raise
    
    def estimate_fee(self, blocks: int = 6) -> Dict:
        """Estimate transaction fee"""
        try:
            fee_rate = self._make_rpc_call("estimatesmartfee", [blocks])
            
            return {
                "blocks": blocks,
                "fee_rate": fee_rate.get('feerate', 0),
                "errors": fee_rate.get('errors', []),
                "estimated_fee": fee_rate.get('feerate', 0) * 1000,  # Convert to FLOP per KB
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error estimating fee: {e}")
            raise
    
    def get_mempool_info(self) -> Dict:
        """Get mempool information"""
        try:
            info = self._make_rpc_call("getmempoolinfo")
            
            return {
                "size": info.get('size', 0),
                "bytes": info.get('bytes', 0),
                "usage": info.get('usage', 0),
                "max_mempool": info.get('maxmempool', 0),
                "mempool_min_fee": info.get('mempoolminfee', 0),
                "min_relay_fee": info.get('minrelaytxfee', 0),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting mempool info: {e}")
            raise

class WalletService:
    """
    Integrated wallet service that provides blockchain wallet functionality
    with registry integration and security features.
    """
    
    def __init__(self, db_session: Session, config_path: Optional[str] = None):
        self.db_session = db_session
        self.wallet_repo = WalletRepository(db_session)
        self.transaction_repo = TransactionRepository(db_session)
        self.auth_service = NodeAuthService()
        
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'duxos', 'wallet', 'config.yaml')
        self.config = self._load_config(config_path)
        
        # RPC configuration
        self.rpc_url = f"http://{self.config['rpc']['host']}:{self.config['rpc']['port']}"
        self.rpc_user = self.config['rpc']['user']
        self.rpc_password = self.config['rpc']['password']
        
        # Security settings
        self.max_transaction_amount = self.config.get('wallet', {}).get('max_transaction_amount', 1000.0)
        self.rate_limit_window = self.config.get('wallet', {}).get('rate_limit_window', 3600)  # 1 hour
        self.max_transactions_per_window = self.config.get('wallet', {}).get('max_transactions_per_window', 10)
        
        logger.info("WalletService initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load wallet configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Wallet configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Wallet config not found at {config_path}, using defaults")
            return {
                'rpc': {
                    'host': '127.0.0.1',
                    'port': 32553,
                    'user': 'flopcoinrpc',
                    'password': 'default_password'
                },
                'wallet': {
                    'max_transaction_amount': 1000.0,
                    'rate_limit_window': 3600,
                    'max_transactions_per_window': 10
                }
            }
        except yaml.YAMLError as e:
            logger.error(f"Error parsing wallet config: {e}")
            raise
    
    def _make_rpc_call(self, method: str, params: Optional[List] = None) -> Tuple[Optional[Any], Optional[str]]:
        """Make RPC call to Flopcoin Core"""
        headers = {'content-type': 'application/json'}
        payload = {
            "method": method,
            "params": params if params is not None else [],
            "jsonrpc": "2.0",
            "id": 1,
        }
        
        try:
            logger.debug(f"Making RPC call: {method} with params: {params}")
            response = requests.post(
                self.rpc_url,
                json=payload,
                headers=headers,
                auth=(self.rpc_user, self.rpc_password),
                timeout=30
            )
            response.raise_for_status()
            rpc_response = response.json()
            
            if rpc_response.get('error'):
                logger.error(f"RPC Error for {method}: {rpc_response['error']}")
                return None, str(rpc_response['error'])
            
            logger.debug(f"RPC call {method} successful")
            return rpc_response.get('result'), None
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network error connecting to Flopcoin Core: {e}")
            return None, f"Network error: {e}"
        except requests.exceptions.Timeout:
            logger.error("RPC call timed out")
            return None, "RPC call timed out"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during RPC call: {e}")
            return None, f"Request error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error during RPC call: {e}")
            return None, f"Unexpected error: {e}"
    
    def create_wallet(self, node_id: str, wallet_name: str, auth_data: Optional[Dict] = None) -> Dict:
        """Create a new wallet for a node"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}
            
            # Check if wallet already exists for this node
            existing_wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if existing_wallet:
                return {"success": False, "message": f"Wallet already exists for node {node_id}"}
            
            # Generate new address from Flopcoin Core
            address, error = self._make_rpc_call("getnewaddress", [wallet_name])
            if error:
                return {"success": False, "message": f"Failed to generate address: {error}"}
            
            # Create wallet in database
            wallet = self.wallet_repo.create_wallet(
                node_id=node_id,
                wallet_name=wallet_name,
                address=address,
                wallet_type="flopcoin",
                is_active=True
            )
            
            # Add wallet capability to node
            self._add_wallet_capability_to_node(node_id)
            
            logger.info(f"Created wallet {wallet_name} for node {node_id}")
            return {
                "success": True,
                "message": f"Wallet {wallet_name} created successfully",
                "wallet": self._wallet_to_dict(wallet)
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating wallet for node {node_id}: {e}")
            return {"success": False, "message": f"Error creating wallet: {str(e)}"}
    
    def get_wallet(self, node_id: str, auth_data: Optional[Dict] = None) -> Optional[Dict]:
        """Get wallet information for a node"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return None
            
            wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if not wallet:
                return None
            
            return self._wallet_to_dict(wallet)
            
        except Exception as e:
            logger.error(f"Error getting wallet for node {node_id}: {e}")
            return None
    
    def get_wallet_balance(self, node_id: str, auth_data: Optional[Dict] = None) -> Dict:
        """Get wallet balance for a node"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}
            
            wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if not wallet:
                return {"success": False, "message": f"No wallet found for node {node_id}"}
            
            # Get balance from Flopcoin Core
            balance, error = self._make_rpc_call("getbalance", [wallet.wallet_name])
            if error:
                return {"success": False, "message": f"Failed to get balance: {error}"}
            
            # Update wallet balance in database
            self.wallet_repo.update_wallet_balance(wallet.id, balance)
            
            return {
                "success": True,
                "node_id": node_id,
                "wallet_name": wallet.wallet_name,
                "address": wallet.address,
                "balance": balance,
                "currency": "FLOP"
            }
            
        except Exception as e:
            logger.error(f"Error getting balance for node {node_id}: {e}")
            return {"success": False, "message": f"Error getting balance: {str(e)}"}
    
    def send_transaction(self, node_id: str, recipient_address: str, amount: float, 
                        auth_data: Optional[Dict] = None) -> Dict:
        """Send Flopcoin transaction"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}
            
            # Validate inputs
            if not recipient_address or not isinstance(recipient_address, str):
                return {"success": False, "message": "Invalid recipient address"}
            
            if not isinstance(amount, (int, float)) or amount <= 0:
                return {"success": False, "message": "Invalid amount"}
            
            if amount > self.max_transaction_amount:
                return {"success": False, "message": f"Amount exceeds maximum limit of {self.max_transaction_amount}"}
            
            # Check rate limiting
            rate_limit_check = self._check_rate_limit(node_id)
            if not rate_limit_check["allowed"]:
                return {"success": False, "message": rate_limit_check["message"]}
            
            # Get wallet
            wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if not wallet:
                return {"success": False, "message": f"No wallet found for node {node_id}"}
            
            # Check balance
            balance, error = self._make_rpc_call("getbalance", [wallet.wallet_name])
            if error:
                return {"success": False, "message": f"Failed to check balance: {error}"}
            
            if balance < amount:
                return {"success": False, "message": "Insufficient balance"}
            
            # Send transaction
            txid, error = self._make_rpc_call("sendtoaddress", [recipient_address, amount])
            if error:
                return {"success": False, "message": f"Transaction failed: {error}"}
            
            # Record transaction in database
            transaction = self.transaction_repo.create_transaction(
                wallet_id=wallet.id,
                txid=txid,
                recipient_address=recipient_address,
                amount=amount,
                transaction_type="send",
                status="confirmed"
            )
            
            # Update wallet balance
            new_balance, _ = self._make_rpc_call("getbalance", [wallet.wallet_name])
            if new_balance is not None:
                self.wallet_repo.update_wallet_balance(wallet.id, new_balance)
            
            logger.info(f"Transaction sent: {txid} from {node_id} to {recipient_address}")
            return {
                "success": True,
                "txid": txid,
                "amount": amount,
                "recipient": recipient_address,
                "transaction": self._transaction_to_dict(transaction)
            }
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error sending transaction for node {node_id}: {e}")
            return {"success": False, "message": f"Error sending transaction: {str(e)}"}
    
    def get_transaction_history(self, node_id: str, limit: int = 50, 
                               auth_data: Optional[Dict] = None) -> Dict:
        """Get transaction history for a node's wallet"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}
            
            wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if not wallet:
                return {"success": False, "message": f"No wallet found for node {node_id}"}
            
            transactions = self.transaction_repo.get_transactions_by_wallet(wallet.id, limit)
            
            return {
                "success": True,
                "node_id": node_id,
                "wallet_name": wallet.wallet_name,
                "transactions": [self._transaction_to_dict(tx) for tx in transactions]
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction history for node {node_id}: {e}")
            return {"success": False, "message": f"Error getting transaction history: {str(e)}"}
    
    def generate_new_address(self, node_id: str, auth_data: Optional[Dict] = None) -> Dict:
        """Generate a new address for a node's wallet"""
        try:
            # Authenticate node if required
            if auth_data:
                authenticated, auth_level = self.auth_service.authenticate_node(node_id, auth_data)
                if not authenticated:
                    return {"success": False, "message": "Authentication failed"}
            
            wallet = self.wallet_repo.get_wallet_by_node(node_id)
            if not wallet:
                return {"success": False, "message": f"No wallet found for node {node_id}"}
            
            # Generate new address
            new_address, error = self._make_rpc_call("getnewaddress", [wallet.wallet_name])
            if error:
                return {"success": False, "message": f"Failed to generate address: {error}"}
            
            # Update wallet with new address
            self.wallet_repo.update_wallet_address(wallet.id, new_address)
            
            logger.info(f"Generated new address {new_address} for node {node_id}")
            return {
                "success": True,
                "node_id": node_id,
                "new_address": new_address,
                "wallet_name": wallet.wallet_name
            }
            
        except Exception as e:
            logger.error(f"Error generating address for node {node_id}: {e}")
            return {"success": False, "message": f"Error generating address: {str(e)}"}
    
    def _check_rate_limit(self, node_id: str) -> Dict:
        """Check if node has exceeded rate limits"""
        try:
            window_start = datetime.utcnow() - timedelta(seconds=self.rate_limit_window)
            recent_transactions = self.transaction_repo.get_transactions_by_node_since(
                node_id, window_start
            )
            
            if len(recent_transactions) >= self.max_transactions_per_window:
                return {
                    "allowed": False,
                    "message": f"Rate limit exceeded. Maximum {self.max_transactions_per_window} transactions per {self.rate_limit_window} seconds"
                }
            
            return {"allowed": True, "message": "Rate limit check passed"}
            
        except Exception as e:
            logger.error(f"Error checking rate limit for node {node_id}: {e}")
            return {"allowed": False, "message": "Error checking rate limit"}
    
    def _add_wallet_capability_to_node(self, node_id: str):
        """Add wallet capability to node in registry"""
        try:
            # This would integrate with the existing registry service
            # For now, we'll just log it
            logger.info(f"Added wallet capability to node {node_id}")
        except Exception as e:
            logger.error(f"Error adding wallet capability to node {node_id}: {e}")
    
    def _wallet_to_dict(self, wallet: Wallet) -> Dict:
        """Convert Wallet model to dictionary"""
        return {
            "id": wallet.id,
            "node_id": wallet.node_id,
            "wallet_name": wallet.wallet_name,
            "address": wallet.address,
            "wallet_type": wallet.wallet_type,
            "balance": float(wallet.balance) if wallet.balance else 0.0,
            "is_active": wallet.is_active,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            "updated_at": wallet.updated_at.isoformat() if wallet.updated_at else None
        }
    
    def _transaction_to_dict(self, transaction: Transaction) -> Dict:
        """Convert Transaction model to dictionary"""
        return {
            "id": transaction.id,
            "wallet_id": transaction.wallet_id,
            "txid": transaction.txid,
            "recipient_address": transaction.recipient_address,
            "amount": float(transaction.amount) if transaction.amount else 0.0,
            "transaction_type": transaction.transaction_type,
            "status": transaction.status,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None
        } 