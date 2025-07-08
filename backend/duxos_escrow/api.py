"""
API endpoints for DuxOS Escrow System
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .community_fund_api import router as community_fund_router
from .escrow_manager import EscrowManager
from .governance_api import router as governance_router
from .models import DisputeStatus, EscrowStatus
from .security import api_key_auth, rate_limiter


# Pydantic models for API requests/responses
class CreateEscrowRequest(BaseModel):
    payer_wallet_id: int = Field(..., description="Payer's wallet ID")
    provider_wallet_id: int = Field(..., description="Provider's wallet ID")
    amount: float = Field(..., gt=0, description="Escrow amount")
    currency: str = Field(default="FLOP", description="Currency for escrow (FLOP, BTC, ETH, etc.)")
    service_name: str = Field(..., description="Service name (e.g., 'image_upscaler_v1')")
    task_id: Optional[str] = Field(None, description="Task ID from Task Engine")
    api_call_id: Optional[str] = Field(None, description="API call ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class CreateEscrowResponse(BaseModel):
    escrow_id: str
    status: str
    amount: float
    currency: str
    provider_amount: Optional[float]
    community_amount: Optional[float]
    created_at: datetime


class ReleaseEscrowRequest(BaseModel):
    result_hash: str = Field(..., description="Hash of the task result")
    provider_signature: str = Field(..., description="Provider's signature")


class RefundEscrowRequest(BaseModel):
    reason: str = Field(..., description="Reason for refund")


class CreateDisputeRequest(BaseModel):
    reason: str = Field(..., description="Reason for dispute")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Evidence for dispute")


class AddEvidenceRequest(BaseModel):
    evidence: Dict[str, Any] = Field(..., description="Evidence to add")


class ResolveDisputeRequest(BaseModel):
    resolution: str = Field(..., description="Resolution details")
    winner_wallet_id: Optional[int] = Field(None, description="Winner's wallet ID")
    refund_amount: Optional[float] = Field(None, description="Refund amount if split")


class EscrowInfo(BaseModel):
    id: str
    payer_wallet_id: int
    provider_wallet_id: int
    amount: float
    status: str
    service_name: str
    provider_amount: Optional[float]
    community_amount: Optional[float]
    created_at: datetime
    released_at: Optional[datetime]
    refunded_at: Optional[datetime]


class DisputeInfo(BaseModel):
    id: str
    escrow_id: str
    status: str
    reason: str
    initiator_wallet_id: int
    respondent_wallet_id: int
    created_at: datetime
    resolved_at: Optional[datetime]


class CommunityFundInfo(BaseModel):
    balance: float
    airdrop_threshold: float
    last_airdrop_at: Optional[datetime]
    last_airdrop_amount: Optional[float]


# FastAPI app
app = FastAPI(
    title="DuxOS Escrow System API",
    description="API for managing escrow contracts and dispute resolution",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global escrow manager (would be initialized with proper dependencies)
escrow_manager = None


def get_escrow_manager():
    """Dependency to get escrow manager"""
    if escrow_manager is None:
        raise HTTPException(status_code=500, detail="Escrow manager not initialized")
    return escrow_manager


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "duxos-escrow",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Escrow endpoints
@app.post(
    "/escrow/create",
    response_model=CreateEscrowResponse,
    dependencies=[Depends(rate_limiter), Depends(api_key_auth)],
)
async def create_escrow(
    request: CreateEscrowRequest, manager: EscrowManager = Depends(get_escrow_manager)
):
    """Create a new escrow contract with multi-crypto support"""
    try:
        escrow = manager.create_escrow(
            payer_wallet_id=request.payer_wallet_id,
            provider_wallet_id=request.provider_wallet_id,
            amount=request.amount,
            currency=request.currency,
            service_name=request.service_name,
            task_id=request.task_id,
            api_call_id=request.api_call_id,
            metadata=request.metadata,
        )

        return CreateEscrowResponse(
            escrow_id=escrow.id,
            status=escrow.status.value,
            amount=escrow.amount,
            currency=escrow.currency,
            provider_amount=escrow.provider_amount,
            community_amount=escrow.community_amount,
            created_at=escrow.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error creating escrow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post(
    "/escrow/{escrow_id}/release", dependencies=[Depends(rate_limiter), Depends(api_key_auth)]
)
async def release_escrow(
    escrow_id: str,
    request: ReleaseEscrowRequest,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Release escrow funds after successful task completion"""
    try:
        success = manager.release_escrow(
            escrow_id=escrow_id,
            result_hash=request.result_hash,
            provider_signature=request.provider_signature,
        )

        if success:
            return {"message": "Escrow released successfully", "escrow_id": escrow_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to release escrow")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error releasing escrow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/escrow/{escrow_id}/refund", dependencies=[Depends(rate_limiter), Depends(api_key_auth)])
async def refund_escrow(
    escrow_id: str,
    request: RefundEscrowRequest,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Refund escrow funds to payer"""
    try:
        success = manager.refund_escrow(escrow_id=escrow_id, reason=request.reason)

        if success:
            return {"message": "Escrow refunded successfully", "escrow_id": escrow_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to refund escrow")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error refunding escrow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/escrow/{escrow_id}", response_model=EscrowInfo, dependencies=[Depends(rate_limiter)])
async def get_escrow(escrow_id: str, manager: EscrowManager = Depends(get_escrow_manager)):
    """Get escrow information"""
    escrow = manager.get_escrow(escrow_id)
    if not escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")

    return EscrowInfo(
        id=escrow.id,
        payer_wallet_id=escrow.payer_wallet_id,
        provider_wallet_id=escrow.provider_wallet_id,
        amount=escrow.amount,
        status=escrow.status.value,
        service_name=escrow.service_name,
        provider_amount=escrow.provider_amount,
        community_amount=escrow.community_amount,
        created_at=escrow.created_at,
        released_at=escrow.released_at,
        refunded_at=escrow.refunded_at,
    )


@app.get(
    "/escrow/wallet/{wallet_id}",
    response_model=List[EscrowInfo],
    dependencies=[Depends(rate_limiter)],
)
async def get_escrows_by_wallet(
    wallet_id: int,
    status: Optional[str] = None,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Get escrows for a wallet"""
    try:
        escrow_status = None
        if status:
            escrow_status = EscrowStatus(status)

        escrows = manager.get_escrows_by_wallet(wallet_id, escrow_status)

        return [
            EscrowInfo(
                id=escrow.id,
                payer_wallet_id=escrow.payer_wallet_id,
                provider_wallet_id=escrow.provider_wallet_id,
                amount=escrow.amount,
                status=escrow.status.value,
                service_name=escrow.service_name,
                provider_amount=escrow.provider_amount,
                community_amount=escrow.community_amount,
                created_at=escrow.created_at,
                released_at=escrow.released_at,
                refunded_at=escrow.refunded_at,
            )
            for escrow in escrows
        ]
    except Exception as e:
        logging.error(f"Error getting escrows for wallet: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Dispute endpoints
@app.post(
    "/escrow/{escrow_id}/dispute", dependencies=[Depends(rate_limiter), Depends(api_key_auth)]
)
async def create_dispute(
    escrow_id: str,
    request: CreateDisputeRequest,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Create a dispute for an escrow"""
    try:
        # This would require authentication to get the current user's wallet ID
        # For now, we'll use a placeholder
        initiator_wallet_id = 1  # Would come from authentication

        dispute = manager.dispute_resolver.create_dispute(
            escrow_id=escrow_id,
            initiator_wallet_id=initiator_wallet_id,
            reason=request.reason,
            evidence=request.evidence,
        )

        return {
            "message": "Dispute created successfully",
            "dispute_id": dispute.id,
            "escrow_id": escrow_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error creating dispute: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post(
    "/dispute/{dispute_id}/evidence", dependencies=[Depends(rate_limiter), Depends(api_key_auth)]
)
async def add_evidence(
    dispute_id: str,
    request: AddEvidenceRequest,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Add evidence to a dispute"""
    try:
        # This would require authentication to get the current user's wallet ID
        wallet_id = 1  # Would come from authentication

        success = manager.dispute_resolver.add_evidence(
            dispute_id=dispute_id, wallet_id=wallet_id, evidence=request.evidence
        )

        if success:
            return {"message": "Evidence added successfully", "dispute_id": dispute_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to add evidence")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error adding evidence: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post(
    "/dispute/{dispute_id}/resolve", dependencies=[Depends(rate_limiter), Depends(api_key_auth)]
)
async def resolve_dispute(
    dispute_id: str,
    request: ResolveDisputeRequest,
    manager: EscrowManager = Depends(get_escrow_manager),
):
    """Resolve a dispute"""
    try:
        success = manager.dispute_resolver.resolve_dispute(
            dispute_id=dispute_id,
            resolution=request.resolution,
            winner_wallet_id=request.winner_wallet_id,
            refund_amount=request.refund_amount,
        )

        if success:
            return {"message": "Dispute resolved successfully", "dispute_id": dispute_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to resolve dispute")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error resolving dispute: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Community fund endpoints
@app.get("/community-fund", response_model=CommunityFundInfo)
async def get_community_fund(manager: EscrowManager = Depends(get_escrow_manager)):
    """Get community fund information"""
    try:
        balance = manager.get_community_fund_balance()

        # Get additional fund info (would need to be implemented)
        return CommunityFundInfo(
            balance=balance,
            airdrop_threshold=100.0,  # From config
            last_airdrop_at=None,  # Would come from database
            last_airdrop_amount=None,  # Would come from database
        )
    except Exception as e:
        logging.error(f"Error getting community fund info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Statistics endpoints
@app.get("/statistics/escrows")
async def get_escrow_statistics(manager: EscrowManager = Depends(get_escrow_manager)):
    """Get escrow statistics"""
    try:
        # This would be implemented to get actual statistics
        return {
            "total_escrows": 0,
            "active_escrows": 0,
            "released_escrows": 0,
            "refunded_escrows": 0,
            "disputed_escrows": 0,
            "total_volume": 0.0,
        }
    except Exception as e:
        logging.error(f"Error getting escrow statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/statistics/disputes")
async def get_dispute_statistics(manager: EscrowManager = Depends(get_escrow_manager)):
    """Get dispute statistics"""
    try:
        stats = manager.dispute_resolver.get_dispute_statistics()
        return stats
    except Exception as e:
        logging.error(f"Error getting dispute statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/currencies", dependencies=[Depends(rate_limiter)])
async def get_supported_currencies(manager: EscrowManager = Depends(get_escrow_manager)):
    """Get list of supported currencies"""
    try:
        currencies = manager.get_supported_currencies()
        return {"currencies": currencies}
    except Exception as e:
        logging.error(f"Error getting currencies: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/escrows/currency/{currency}", dependencies=[Depends(rate_limiter)])
async def get_escrows_by_currency(
    currency: str, manager: EscrowManager = Depends(get_escrow_manager)
):
    """Get escrows by currency"""
    try:
        escrows = manager.get_escrows_by_currency(currency)
        return {
            "currency": currency.upper(),
            "escrows": [
                {
                    "id": escrow.id,
                    "amount": escrow.amount,
                    "status": escrow.status.value,
                    "created_at": escrow.created_at,
                }
                for escrow in escrows
            ],
        }
    except Exception as e:
        logging.error(f"Error getting escrows by currency: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


app.include_router(community_fund_router)

# Include governance router
app.include_router(governance_router)
