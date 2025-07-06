"""
Result Verifier

Validates task execution results and ensures trust in the distributed system.
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .models import TaskResult, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class VerificationRule:
    """Rule for result verification"""
    rule_type: str  # hash, format, range, custom
    parameters: Dict[str, Any]
    description: str


class ResultVerifier:
    """
    Verifies task execution results for trust and consistency.
    
    Features:
    - Result hash verification
    - Output format validation
    - Range and type checking
    - Custom verification rules
    - Trust scoring
    """
    
    def __init__(self):
        self.verification_rules: Dict[str, List[VerificationRule]] = {}
        self.verification_stats = {
            "total_verifications": 0,
            "successful_verifications": 0,
            "failed_verifications": 0
        }
        
        logger.info("Result Verifier initialized")
    
    async def verify_result(self, result: TaskResult) -> bool:
        """Verify a task result"""
        try:
            if result.status != TaskStatus.COMPLETED:
                logger.warning(f"Cannot verify failed result: {result.task_id}")
                return False
            
            if not result.output_data:
                logger.error(f"No output data to verify for task {result.task_id}")
                return False
            
            self.verification_stats["total_verifications"] += 1
            
            # Basic verification
            if not self._verify_basic_checks(result):
                self.verification_stats["failed_verifications"] += 1
                return False
            
            # Hash verification
            if not self._verify_result_hash(result):
                self.verification_stats["failed_verifications"] += 1
                return False
            
            # Service-specific verification
            if not await self._verify_service_specific(result):
                self.verification_stats["failed_verifications"] += 1
                return False
            
            # Custom rules verification
            if not self._verify_custom_rules(result):
                self.verification_stats["failed_verifications"] += 1
                return False
            
            self.verification_stats["successful_verifications"] += 1
            logger.info(f"Result verification successful for task {result.task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying result {result.task_id}: {e}")
            self.verification_stats["failed_verifications"] += 1
            return False
    
    def _verify_basic_checks(self, result: TaskResult) -> bool:
        """Perform basic verification checks"""
        # Check execution time
        if result.execution_time_seconds and result.execution_time_seconds < 0:
            logger.error(f"Invalid execution time for task {result.task_id}")
            return False
        
        # Check output data structure
        if not isinstance(result.output_data, dict):
            logger.error(f"Output data must be a dictionary for task {result.task_id}")
            return False
        
        # Check for required fields
        if "result" not in result.output_data and "error" not in result.output_data:
            logger.warning(f"Output data missing standard fields for task {result.task_id}")
        
        return True
    
    def _verify_result_hash(self, result: TaskResult) -> bool:
        """Verify result hash if provided"""
        if not result.result_hash:
            logger.warning(f"No result hash provided for task {result.task_id}")
            return True  # Not required, but recommended
        
        # Calculate expected hash
        expected_hash = self._calculate_result_hash(result.output_data)
        
        if result.result_hash != expected_hash:
            logger.error(f"Result hash mismatch for task {result.task_id}")
            logger.error(f"Expected: {expected_hash}")
            logger.error(f"Received: {result.result_hash}")
            return False
        
        return True
    
    def _calculate_result_hash(self, output_data: Dict[str, Any]) -> str:
        """Calculate hash of output data"""
        result_str = json.dumps(output_data, sort_keys=True)
        return hashlib.sha256(result_str.encode()).hexdigest()
    
    async def _verify_service_specific(self, result: TaskResult) -> bool:
        """Verify service-specific requirements"""
        # This would be implemented based on the service type
        # For now, return True as a placeholder
        return True
    
    def _verify_custom_rules(self, result: TaskResult) -> bool:
        """Verify custom verification rules"""
        # Get rules for this task type (if any)
        rules = self.verification_rules.get(result.task_id, [])
        
        for rule in rules:
            if not self._apply_verification_rule(result, rule):
                logger.error(f"Failed custom rule '{rule.description}' for task {result.task_id}")
                return False
        
        return True
    
    def _apply_verification_rule(self, result: TaskResult, rule: VerificationRule) -> bool:
        """Apply a specific verification rule"""
        try:
            if rule.rule_type == "hash":
                return self._verify_hash_rule(result, rule)
            elif rule.rule_type == "format":
                return self._verify_format_rule(result, rule)
            elif rule.rule_type == "range":
                return self._verify_range_rule(result, rule)
            elif rule.rule_type == "custom":
                return self._verify_custom_rule(result, rule)
            else:
                logger.warning(f"Unknown verification rule type: {rule.rule_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error applying verification rule: {e}")
            return False
    
    def _verify_hash_rule(self, result: TaskResult, rule: VerificationRule) -> bool:
        """Verify hash-based rule"""
        expected_hash = rule.parameters.get("expected_hash")
        if not expected_hash:
            return True
        
        actual_hash = self._calculate_result_hash(result.output_data)
        return actual_hash == expected_hash
    
    def _verify_format_rule(self, result: TaskResult, rule: VerificationRule) -> bool:
        """Verify format-based rule"""
        required_fields = rule.parameters.get("required_fields", [])
        field_types = rule.parameters.get("field_types", {})
        
        # Check required fields
        for field in required_fields:
            if field not in result.output_data:
                logger.error(f"Missing required field '{field}' in task {result.task_id}")
                return False
        
        # Check field types
        for field, expected_type in field_types.items():
            if field in result.output_data:
                actual_type = type(result.output_data[field]).__name__
                if actual_type != expected_type:
                    logger.error(f"Field '{field}' has wrong type. Expected {expected_type}, got {actual_type}")
                    return False
        
        return True
    
    def _verify_range_rule(self, result: TaskResult, rule: VerificationRule) -> bool:
        """Verify range-based rule"""
        field = rule.parameters.get("field")
        min_value = rule.parameters.get("min_value")
        max_value = rule.parameters.get("max_value")
        
        if field not in result.output_data:
            return True  # Field not present, skip check
        
        value = result.output_data[field]
        
        if min_value is not None and value < min_value:
            logger.error(f"Field '{field}' value {value} below minimum {min_value}")
            return False
        
        if max_value is not None and value > max_value:
            logger.error(f"Field '{field}' value {value} above maximum {max_value}")
            return False
        
        return True
    
    def _verify_custom_rule(self, result: TaskResult, rule: VerificationRule) -> bool:
        """Verify custom rule"""
        # This would be implemented based on custom logic
        # For now, return True as a placeholder
        return True
    
    def add_verification_rule(self, task_id: str, rule: VerificationRule):
        """Add a verification rule for a specific task"""
        if task_id not in self.verification_rules:
            self.verification_rules[task_id] = []
        
        self.verification_rules[task_id].append(rule)
        logger.info(f"Added verification rule for task {task_id}: {rule.description}")
    
    def remove_verification_rules(self, task_id: str):
        """Remove all verification rules for a task"""
        if task_id in self.verification_rules:
            del self.verification_rules[task_id]
            logger.info(f"Removed verification rules for task {task_id}")
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        total = self.verification_stats["total_verifications"]
        return {
            **self.verification_stats,
            "success_rate": (
                self.verification_stats["successful_verifications"] / 
                max(total, 1)
            ),
            "active_rules": sum(len(rules) for rules in self.verification_rules.values())
        } 