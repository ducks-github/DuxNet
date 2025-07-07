"""
UI Models for DuxOS Desktop

Defines data models for services, reviews, and users for use in the desktop app.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ServiceModel:
    service_id: str
    name: str
    description: str
    version: str
    category: str
    status: str
    owner_id: str
    owner_name: str
    tags: List[str]
    documentation_url: Optional[str]
    repository_url: Optional[str]
    price_per_call: float
    price_currency: str
    free_tier_calls: int
    rate_limit_per_hour: Optional[int]
    code_hash: str
    execution_requirements: Dict[str, Any]
    input_schema: Optional[Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    example_input: Optional[Dict[str, Any]]
    example_output: Optional[Dict[str, Any]]
    avg_response_time: Optional[float]
    success_rate: Optional[float]
    uptime_percentage: Optional[float]
    total_calls: int
    total_revenue: float
    rating_count: int
    average_rating: float
    created_at: str
    updated_at: str
    published_at: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewModel:
    review_id: str
    service_id: str
    user_id: str
    user_name: str
    rating: int
    title: str
    content: str
    helpful_votes: int
    is_verified_purchase: bool
    created_at: str
    updated_at: str

@dataclass
class UserModel:
    user_id: str
    user_name: str
    wallet_address: Optional[str] = None
    balance: Optional[float] = None
    favorites: List[str] = field(default_factory=list)
    purchase_history: List[str] = field(default_factory=list) 