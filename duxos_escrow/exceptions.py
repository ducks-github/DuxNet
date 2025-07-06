"""
Custom exceptions for the DuxOS Escrow System
"""

class EscrowError(Exception):
    """Base exception for escrow-related errors"""
    pass

class DisputeError(Exception):
    """Raised when there's an error in dispute resolution"""
    pass

class CommunityFundError(Exception):
    """Raised when there's an error in community fund operations"""
    pass

class GovernanceError(Exception):
    """Base exception for governance-related errors"""
    pass

class ProposalNotFoundError(GovernanceError):
    """Raised when a proposal is not found"""
    pass

class VotingNotActiveError(GovernanceError):
    """Raised when voting is not active for a proposal"""
    pass

class AlreadyVotedError(GovernanceError):
    """Raised when a wallet has already voted on a proposal"""
    pass

class InsufficientVotingPowerError(GovernanceError):
    """Raised when voting power is insufficient"""
    pass

class ProposalExecutionError(GovernanceError):
    """Raised when there's an error executing a proposal"""
    pass 