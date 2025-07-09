# Python interface for Trust Wallet wallet-core

try:
    from wallet_core import WalletCore
    WALLET_CORE_AVAILABLE = True
except ImportError:
    WALLET_CORE_AVAILABLE = False

class WalletCoreWrapper:
    """Wrapper for Trust Wallet wallet-core Python bindings"""
    def __init__(self, coin: str):
        if not WALLET_CORE_AVAILABLE:
            raise ImportError("wallet_core Python bindings not installed.")
        self.core = WalletCore(coin)
    def get_address(self):
        return self.core.get_address()
    # Add more methods as needed
