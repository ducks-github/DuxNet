"""
Wallet API Routes for DuxOS Registry

This module provides REST API endpoints for wallet operations including
wallet creation, balance checking, transaction sending, and address generation.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..services.wallet_service import WalletService
from .schemas import (
    NewAddressResponse,
    TransactionHistoryResponse,
    TransactionSendRequest,
    TransactionSendResponse,
    WalletBalanceResponse,
    WalletCreateRequest,
    WalletCreateResponse,
    WalletInfo,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])


def get_wallet_service(db: Session = Depends(get_db)) -> WalletService:
    """Dependency to get wallet service instance"""
    return WalletService(db)


@router.post("/create", response_model=WalletCreateResponse)
def create_wallet(
    request: WalletCreateRequest, wallet_service: WalletService = Depends(get_wallet_service)
):
    """Create a new wallet for a node"""
    try:
        result = wallet_service.create_wallet(
            node_id=request.node_id, wallet_name=request.wallet_name, auth_data=request.auth_data
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating wallet: {str(e)}")


@router.get("/{node_id}", response_model=WalletInfo)
def get_wallet(node_id: str, wallet_service: WalletService = Depends(get_wallet_service)):
    """Get wallet information for a node"""
    try:
        wallet = wallet_service.get_wallet(node_id, None)
        if not wallet:
            raise HTTPException(status_code=404, detail=f"No wallet found for node {node_id}")

        return wallet

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting wallet: {str(e)}")


@router.get("/{node_id}/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(node_id: str, wallet_service: WalletService = Depends(get_wallet_service)):
    """Get wallet balance for a node"""
    try:
        result = wallet_service.get_wallet_balance(node_id, None)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting balance: {str(e)}")


@router.post("/{node_id}/send", response_model=TransactionSendResponse)
def send_transaction(
    node_id: str,
    request: TransactionSendRequest,
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Send Flopcoin transaction from a node's wallet"""
    try:
        # Validate that the node_id in the path matches the request
        if node_id != request.node_id:
            raise HTTPException(status_code=400, detail="Node ID mismatch")

        result = wallet_service.send_transaction(
            node_id=request.node_id,
            recipient_address=request.recipient_address,
            amount=request.amount,
            auth_data=request.auth_data,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending transaction: {str(e)}")


@router.get("/{node_id}/transactions", response_model=TransactionHistoryResponse)
def get_transaction_history(
    node_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get transaction history for a node's wallet"""
    try:
        result = wallet_service.get_transaction_history(node_id, limit, None)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting transaction history: {str(e)}")


@router.post("/{node_id}/new-address", response_model=NewAddressResponse)
def generate_new_address(node_id: str, wallet_service: WalletService = Depends(get_wallet_service)):
    """Generate a new address for a node's wallet"""
    try:
        result = wallet_service.generate_new_address(node_id, None)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating address: {str(e)}")


@router.get("/status/health")
def wallet_health_check():
    """Health check for wallet service"""
    return {"status": "ok", "service": "wallet", "version": "1.0.0"}
