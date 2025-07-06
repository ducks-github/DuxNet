"""
Community Fund API endpoints for DuxOS Escrow System
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from .community_fund_manager import CommunityFundManager
from .exceptions import CommunityFundError
from .security import rate_limiter, api_key_auth

router = APIRouter(prefix="/community-fund", tags=["community-fund"])

def get_community_fund_manager(db: Session) -> CommunityFundManager:
    """Dependency to get community fund manager"""
    return CommunityFundManager(db)

@router.get("/balance", dependencies=[Depends(rate_limiter)])
def get_fund_balance(
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, float]:
    """Get current community fund balance"""
    try:
        balance = manager.get_fund_balance()
        return {"balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", dependencies=[Depends(rate_limiter)])
def get_fund_stats(
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, Any]:
    """Get comprehensive fund statistics"""
    try:
        return manager.get_fund_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airdrop/check", dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
def check_airdrop_eligibility(
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, bool]:
    """Check if airdrop threshold is met"""
    try:
        eligible = manager.check_airdrop_eligibility()
        return {"eligible": eligible}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/airdrop/execute", dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
def execute_airdrop(
    distribution_ratio: float = 0.5,
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, Any]:
    """Execute airdrop to active nodes"""
    try:
        if not 0.0 <= distribution_ratio <= 1.0:
            raise HTTPException(status_code=400, detail="Distribution ratio must be between 0.0 and 1.0")
        
        result = manager.execute_airdrop(distribution_ratio)
        return result
    except CommunityFundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airdrop/history", dependencies=[Depends(rate_limiter)])
def get_airdrop_history(
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, Any]:
    """Get airdrop history"""
    try:
        history = manager.get_airdrop_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/threshold", dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
def update_airdrop_threshold(
    threshold: float,
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, str]:
    """Update airdrop threshold"""
    try:
        if threshold <= 0:
            raise HTTPException(status_code=400, detail="Threshold must be positive")
        
        success = manager.update_airdrop_threshold(threshold)
        if success:
            return {"message": f"Airdrop threshold updated to {threshold}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to update threshold")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/withdraw", dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
def withdraw_from_fund(
    amount: float,
    reason: str,
    manager: CommunityFundManager = Depends(get_community_fund_manager)
) -> Dict[str, str]:
    """Withdraw amount from community fund (requires governance approval)"""
    try:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        success = manager.remove_from_fund(amount, reason)
        if success:
            return {"message": f"Withdrew {amount} FLOP for: {reason}"}
        else:
            raise HTTPException(status_code=500, detail="Failed to withdraw funds")
    except CommunityFundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 