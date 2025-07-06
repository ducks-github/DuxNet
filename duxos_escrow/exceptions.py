"""
Custom exceptions for DuxOS Escrow System
"""

class EscrowError(Exception):
    """Base exception for escrow system"""
    pass

class EscrowNotFoundError(EscrowError):
    """Raised when escrow is not found"""
    pass

class EscrowStateError(EscrowError):
    """Raised when escrow is in invalid state for operation"""
    pass

class InsufficientFundsError(EscrowError):
    """Raised when insufficient funds for operation"""
    pass

class ValidationError(EscrowError):
    """Raised when validation fails"""
    pass

class DisputeError(EscrowError):
    """Base exception for dispute system"""
    pass

class DisputeNotFoundError(DisputeError):
    """Raised when dispute is not found"""
    pass

class DisputeStateError(DisputeError):
    """Raised when dispute is in invalid state for operation"""
    pass

class GovernanceError(EscrowError):
    """Base exception for governance system"""
    pass

class ProposalNotFoundError(GovernanceError):
    """Raised when proposal is not found"""
    pass

class VotingNotActiveError(GovernanceError):
    """Raised when voting is not active"""
    pass

class AlreadyVotedError(GovernanceError):
    """Raised when user has already voted"""
    pass

class InsufficientVotingPowerError(GovernanceError):
    """Raised when user has insufficient voting power"""
    pass

class ProposalExecutionError(GovernanceError):
    """Raised when proposal execution fails"""
    pass

# Wallet Integration Exceptions
class WalletIntegrationError(EscrowError):
    """Base exception for wallet integration"""
    pass

class TransactionFailedError(WalletIntegrationError):
    """Raised when blockchain transaction fails"""
    pass

class WalletNotFoundError(WalletIntegrationError):
    """Raised when wallet is not found"""
    pass

class AuthenticationError(WalletIntegrationError):
    """Raised when authentication fails"""
    pass

class SignatureValidationError(WalletIntegrationError):
    """Raised when signature validation fails"""
    pass

class CommunityFundError(EscrowError):
    """Base exception for community fund operations"""
    pass

class AirdropError(CommunityFundError):
    """Raised when airdrop operation fails"""
    pass

class InsufficientCommunityFundError(CommunityFundError):
    """Raised when community fund has insufficient balance"""
    pass 