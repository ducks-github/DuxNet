"""
Store Data Models

Defines the core data structures for the API/App Store including
services, reviews, ratings, and metadata.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ServiceStatus(Enum):
    """Service publication status"""

    DRAFT = "draft"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ServiceCategory(Enum):
    """Service categories"""

    API = "api"
    APPLICATION = "application"
    MACHINE_LEARNING = "machine_learning"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_PROCESSING = "image_processing"
    TEXT_PROCESSING = "text_processing"
    BLOCKCHAIN = "blockchain"
    UTILITY = "utility"
    CUSTOM = "custom"


@dataclass
class Service:
    """Represents a service in the store"""

    # Core identification
    service_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    category: ServiceCategory = ServiceCategory.API
    status: ServiceStatus = ServiceStatus.DRAFT

    # Ownership and metadata
    owner_id: str = ""
    owner_name: str = ""
    tags: List[str] = field(default_factory=list)
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None

    # Pricing and access
    price_per_call: float = 0.0
    price_currency: str = "FLOP"
    free_tier_calls: int = 0
    rate_limit_per_hour: Optional[int] = None

    # Technical specifications
    code_hash: str = ""
    execution_requirements: Dict[str, Any] = field(default_factory=dict)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    example_input: Optional[Dict[str, Any]] = None
    example_output: Optional[Dict[str, Any]] = None

    # Performance and quality
    avg_response_time: Optional[float] = None
    success_rate: Optional[float] = None
    uptime_percentage: Optional[float] = None

    # Statistics
    total_calls: int = 0
    total_revenue: float = 0.0
    rating_count: int = 0
    average_rating: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert service to dictionary for serialization"""
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category.value,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "tags": self.tags,
            "documentation_url": self.documentation_url,
            "repository_url": self.repository_url,
            "price_per_call": self.price_per_call,
            "price_currency": self.price_currency,
            "free_tier_calls": self.free_tier_calls,
            "rate_limit_per_hour": self.rate_limit_per_hour,
            "code_hash": self.code_hash,
            "execution_requirements": self.execution_requirements,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "example_input": self.example_input,
            "example_output": self.example_output,
            "avg_response_time": self.avg_response_time,
            "success_rate": self.success_rate,
            "uptime_percentage": self.uptime_percentage,
            "total_calls": self.total_calls,
            "total_revenue": self.total_revenue,
            "rating_count": self.rating_count,
            "average_rating": self.average_rating,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Service":
        """Create service from dictionary"""
        return cls(
            service_id=data.get("service_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            category=ServiceCategory(data.get("category", "api")),
            status=ServiceStatus(data.get("status", "draft")),
            owner_id=data.get("owner_id", ""),
            owner_name=data.get("owner_name", ""),
            tags=data.get("tags", []),
            documentation_url=data.get("documentation_url"),
            repository_url=data.get("repository_url"),
            price_per_call=data.get("price_per_call", 0.0),
            price_currency=data.get("price_currency", "FLOP"),
            free_tier_calls=data.get("free_tier_calls", 0),
            rate_limit_per_hour=data.get("rate_limit_per_hour"),
            code_hash=data.get("code_hash", ""),
            execution_requirements=data.get("execution_requirements", {}),
            input_schema=data.get("input_schema"),
            output_schema=data.get("output_schema"),
            example_input=data.get("example_input"),
            example_output=data.get("example_output"),
            avg_response_time=data.get("avg_response_time"),
            success_rate=data.get("success_rate"),
            uptime_percentage=data.get("uptime_percentage"),
            total_calls=data.get("total_calls", 0),
            total_revenue=data.get("total_revenue", 0.0),
            rating_count=data.get("rating_count", 0),
            average_rating=data.get("average_rating", 0.0),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.utcnow()
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else datetime.utcnow()
            ),
            published_at=(
                datetime.fromisoformat(data["published_at"]) if data.get("published_at") else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Review:
    """User review for a service"""

    review_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str = ""
    user_id: str = ""
    user_name: str = ""
    rating: int = 0  # 1-5 stars
    title: str = ""
    content: str = ""
    helpful_votes: int = 0
    is_verified_purchase: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary"""
        return {
            "review_id": self.review_id,
            "service_id": self.service_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "helpful_votes": self.helpful_votes,
            "is_verified_purchase": self.is_verified_purchase,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Rating:
    """Rating statistics for a service"""

    service_id: str = ""
    total_ratings: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[int, int] = field(default_factory=dict)  # 1-5 stars
    weighted_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def calculate_weighted_score(self) -> float:
        """Calculate weighted score based on rating distribution"""
        if self.total_ratings == 0:
            return 0.0

        # Weight recent ratings more heavily
        total_weighted = 0.0
        total_weight = 0.0

        for rating, count in self.rating_distribution.items():
            weight = count * (rating / 5.0)  # Normalize to 0-1
            total_weighted += weight
            total_weight += count

        return total_weighted / total_weight if total_weight > 0 else 0.0

    def update_from_review(self, review: Review):
        """Update rating statistics from a new review"""
        # Update distribution
        if review.rating not in self.rating_distribution:
            self.rating_distribution[review.rating] = 0
        self.rating_distribution[review.rating] += 1

        # Update totals
        self.total_ratings += 1

        # Recalculate average
        total_rating = sum(rating * count for rating, count in self.rating_distribution.items())
        self.average_rating = total_rating / self.total_ratings

        # Update weighted score
        self.weighted_score = self.calculate_weighted_score()
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert rating to dictionary"""
        return {
            "service_id": self.service_id,
            "total_ratings": self.total_ratings,
            "average_rating": self.average_rating,
            "rating_distribution": self.rating_distribution,
            "weighted_score": self.weighted_score,
            "last_updated": self.last_updated.isoformat(),
        }


@dataclass
class ServiceUsage:
    """Service usage statistics"""

    service_id: str = ""
    user_id: str = ""
    total_calls: int = 0
    total_spent: float = 0.0
    last_used: Optional[datetime] = None
    favorite: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert usage to dictionary"""
        return {
            "service_id": self.service_id,
            "user_id": self.user_id,
            "total_calls": self.total_calls,
            "total_spent": self.total_spent,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "favorite": self.favorite,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SearchFilter:
    """Search and filter criteria"""

    query: str = ""
    category: Optional[ServiceCategory] = None
    min_rating: float = 0.0
    max_price: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    owner_id: Optional[str] = None
    status: ServiceStatus = ServiceStatus.PUBLISHED
    sort_by: str = "relevance"  # relevance, rating, price, date
    sort_order: str = "desc"  # asc, desc
    limit: int = 20
    offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary"""
        return {
            "query": self.query,
            "category": self.category.value if self.category else None,
            "min_rating": self.min_rating,
            "max_price": self.max_price,
            "tags": self.tags,
            "owner_id": self.owner_id,
            "status": self.status.value,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class User:
    """User account for authentication"""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    password_hash: str = ""  # Store hashed password
    email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }
