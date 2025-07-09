"""
DuxNet Wallet Package

This package provides wallet functionality for the DuxNet platform,
including Flopcoin wallet integration and multi-cryptocurrency support.
"""

__version__ = "1.0.0"
__author__ = "DuxNet Team"

# Import main classes for easy access
try:
    from .wallet import FlopcoinWallet
    from .multi_crypto_wallet import MultiCryptoWallet
    from .wallet_core_wrapper import WalletCoreWrapper
except ImportError:
    # Handle case where dependencies are not available
    FlopcoinWallet = None
    MultiCryptoWallet = None
    WalletCoreWrapper = None

__all__ = ["FlopcoinWallet", "MultiCryptoWallet", "WalletCoreWrapper"]