"""
Transaction Validator for DuxOS Escrow System
"""

import hashlib
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .models import Escrow

logger = logging.getLogger(__name__)

class TransactionValidator:
    """Validates task results and cryptographic signatures"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_result(self, escrow: Escrow, result_hash: str, provider_signature: str) -> bool:
        """Validate task result and provider signature"""
        try:
            # Validate result hash format
            if not self._is_valid_hash(result_hash):
                logger.warning(f"Invalid result hash format for escrow {escrow.id}")
                return False
            
            # Validate provider signature
            if not self._validate_signature(escrow, provider_signature):
                logger.warning(f"Invalid provider signature for escrow {escrow.id}")
                return False
            
            # Additional validation based on service type
            if not self._validate_service_specific_result(escrow, result_hash):
                logger.warning(f"Service-specific validation failed for escrow {escrow.id}")
                return False
            
            logger.info(f"Result validation successful for escrow {escrow.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating result for escrow {escrow.id}: {e}")
            return False
    
    def _is_valid_hash(self, hash_str: str) -> bool:
        """Check if hash string is valid format"""
        # Basic validation - should be a hex string of appropriate length
        try:
            int(hash_str, 16)
            return len(hash_str) == 64  # SHA-256 hash length
        except ValueError:
            return False
    
    def _validate_signature(self, escrow: Escrow, signature: str) -> bool:
        """Validate provider signature"""
        # This would integrate with the authentication system
        # For now, we'll do basic format validation
        try:
            # Basic signature format validation
            if not signature or len(signature) < 64:
                return False
            
            # In a real implementation, this would verify the signature
            # against the provider's public key
            logger.info(f"Signature validation placeholder for escrow {escrow.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return False
    
    def _validate_service_specific_result(self, escrow: Escrow, result_hash: str) -> bool:
        """Validate result based on service type"""
        service_name = escrow.service_name.lower()
        
        if "image" in service_name:
            return self._validate_image_service_result(escrow, result_hash)
        elif "text" in service_name or "nlp" in service_name:
            return self._validate_text_service_result(escrow, result_hash)
        elif "compute" in service_name or "calculation" in service_name:
            return self._validate_compute_service_result(escrow, result_hash)
        else:
            # Default validation for unknown services
            return self._validate_generic_result(escrow, result_hash)
    
    def _validate_image_service_result(self, escrow: Escrow, result_hash: str) -> bool:
        """Validate image processing service results"""
        # Check if result hash indicates a valid image format
        # This is a placeholder - real validation would check actual image data
        logger.info(f"Image service validation for escrow {escrow.id}")
        return True
    
    def _validate_text_service_result(self, escrow: Escrow, result_hash: str) -> bool:
        """Validate text processing service results"""
        # Check if result hash indicates valid text processing
        logger.info(f"Text service validation for escrow {escrow.id}")
        return True
    
    def _validate_compute_service_result(self, escrow: Escrow, result_hash: str) -> bool:
        """Validate computational service results"""
        # Check if result hash indicates valid computation
        logger.info(f"Compute service validation for escrow {escrow.id}")
        return True
    
    def _validate_generic_result(self, escrow: Escrow, result_hash: str) -> bool:
        """Generic validation for unknown service types"""
        # Basic validation that result exists and has valid format
        logger.info(f"Generic validation for escrow {escrow.id}")
        return True
    
    def generate_result_hash(self, result_data: Dict[str, Any]) -> str:
        """Generate hash for result data"""
        # Convert result data to consistent string format
        result_str = str(sorted(result_data.items()))
        return hashlib.sha256(result_str.encode()).hexdigest()
    
    def verify_result_consistency(self, escrow: Escrow, actual_result: Dict[str, Any]) -> bool:
        """Verify that actual result matches expected result"""
        try:
            # Generate hash from actual result
            actual_hash = self.generate_result_hash(actual_result)
            
            # Compare with stored result hash
            if escrow.result_hash and escrow.result_hash != actual_hash:
                logger.warning(f"Result hash mismatch for escrow {escrow.id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying result consistency: {e}")
            return False 