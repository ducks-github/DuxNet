"""
Store Service

Core service for managing the API/App Store including service registration,
discovery, search, and metadata management.
"""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .metadata_storage import MetadataStorage
from .models import (
    Rating,
    Review,
    SearchFilter,
    Service,
    ServiceCategory,
    ServiceStatus,
    ServiceUsage,
)
from .rating_system import RatingSystem


class StoreService:
    """Main store service for managing services and discovery"""

    def __init__(self, metadata_storage: MetadataStorage, rating_system: RatingSystem):
        self.metadata_storage = metadata_storage
        self.rating_system = rating_system
        self.services: Dict[str, Service] = {}
        self.reviews: Dict[str, List[Review]] = {}
        self.ratings: Dict[str, Rating] = {}
        self.usage: Dict[str, Dict[str, ServiceUsage]] = {}  # service_id -> {user_id -> usage}

    def register_service(
        self, service_data: Dict[str, Any], owner_id: str, owner_name: str
    ) -> Service:
        """Register a new service in the store"""

        # Validate required fields
        required_fields = ["name", "description", "category", "code_hash"]
        for field in required_fields:
            if not service_data.get(field):
                raise ValueError(f"Missing required field: {field}")

        # Create service object
        service = Service(
            name=service_data["name"],
            description=service_data["description"],
            version=service_data.get("version", "1.0.0"),
            category=ServiceCategory(service_data["category"]),
            owner_id=owner_id,
            owner_name=owner_name,
            tags=service_data.get("tags", []),
            documentation_url=service_data.get("documentation_url"),
            repository_url=service_data.get("repository_url"),
            price_per_call=service_data.get("price_per_call", 0.0),
            price_currency=service_data.get("price_currency", "FLOP"),
            free_tier_calls=service_data.get("free_tier_calls", 0),
            rate_limit_per_hour=service_data.get("rate_limit_per_hour"),
            code_hash=service_data["code_hash"],
            execution_requirements=service_data.get("execution_requirements", {}),
            input_schema=service_data.get("input_schema"),
            output_schema=service_data.get("output_schema"),
            example_input=service_data.get("example_input"),
            example_output=service_data.get("example_output"),
            metadata=service_data.get("metadata", {}),
        )

        # Store service
        self.services[service.service_id] = service
        self.reviews[service.service_id] = []
        self.ratings[service.service_id] = Rating(service_id=service.service_id)
        self.usage[service.service_id] = {}

        # Store metadata in distributed storage
        self.metadata_storage.store_service_metadata(service)

        return service

    def update_service(
        self, service_id: str, updates: Dict[str, Any], owner_id: str
    ) -> Optional[Service]:
        """Update an existing service"""
        service = self.services.get(service_id)
        if not service or service.owner_id != owner_id:
            return None

        # Update allowed fields
        allowed_updates = {
            "name",
            "description",
            "version",
            "tags",
            "documentation_url",
            "repository_url",
            "price_per_call",
            "price_currency",
            "free_tier_calls",
            "rate_limit_per_hour",
            "input_schema",
            "output_schema",
            "example_input",
            "example_output",
            "metadata",
        }

        for field, value in updates.items():
            if field in allowed_updates:
                setattr(service, field, value)

        service.updated_at = datetime.utcnow()

        # Update metadata storage
        self.metadata_storage.store_service_metadata(service)

        return service

    def publish_service(self, service_id: str, owner_id: str) -> Optional[Service]:
        """Publish a service (change status to published)"""
        service = self.services.get(service_id)
        if not service or service.owner_id != owner_id:
            return None

        if service.status == ServiceStatus.DRAFT:
            service.status = ServiceStatus.PUBLISHED
            service.published_at = datetime.utcnow()
            service.updated_at = datetime.utcnow()

            # Update metadata storage
            self.metadata_storage.store_service_metadata(service)

        return service

    def suspend_service(self, service_id: str, owner_id: str) -> Optional[Service]:
        """Suspend a service"""
        service = self.services.get(service_id)
        if not service or service.owner_id != owner_id:
            return None

        service.status = ServiceStatus.SUSPENDED
        service.updated_at = datetime.utcnow()

        # Update metadata storage
        self.metadata_storage.store_service_metadata(service)

        return service

    def get_service(self, service_id: str) -> Optional[Service]:
        """Get a service by ID"""
        return self.services.get(service_id)

    def get_services_by_owner(
        self, owner_id: str, status: Optional[ServiceStatus] = None
    ) -> List[Service]:
        """Get all services by an owner"""
        services = [s for s in self.services.values() if s.owner_id == owner_id]
        if status:
            services = [s for s in services if s.status == status]
        return services

    def search_services(self, search_filter: SearchFilter) -> Tuple[List[Service], int]:
        """Search and filter services"""
        # Start with all published services
        candidates = [s for s in self.services.values() if s.status == search_filter.status]

        # Apply filters
        if search_filter.category:
            candidates = [s for s in candidates if s.category == search_filter.category]

        if search_filter.min_rating > 0:
            candidates = [s for s in candidates if s.average_rating >= search_filter.min_rating]

        if search_filter.max_price is not None:
            candidates = [s for s in candidates if s.price_per_call <= search_filter.max_price]

        if search_filter.tags:
            candidates = [s for s in candidates if any(tag in s.tags for tag in search_filter.tags)]

        if search_filter.owner_id:
            candidates = [s for s in candidates if s.owner_id == search_filter.owner_id]

        # Apply text search
        if search_filter.query:
            query_lower = search_filter.query.lower()
            candidates = [
                s
                for s in candidates
                if (
                    query_lower in s.name.lower()
                    or query_lower in s.description.lower()
                    or any(query_lower in tag.lower() for tag in s.tags)
                )
            ]

        # Sort results
        if search_filter.sort_by == "rating":
            candidates.sort(
                key=lambda s: s.average_rating, reverse=(search_filter.sort_order == "desc")
            )
        elif search_filter.sort_by == "price":
            candidates.sort(
                key=lambda s: s.price_per_call, reverse=(search_filter.sort_order == "desc")
            )
        elif search_filter.sort_by == "date":
            candidates.sort(
                key=lambda s: s.published_at or s.created_at,
                reverse=(search_filter.sort_order == "desc"),
            )
        else:  # relevance - use weighted score
            candidates.sort(
                key=lambda s: self._calculate_relevance_score(s, search_filter.query), reverse=True
            )

        total_count = len(candidates)

        # Apply pagination
        start = search_filter.offset
        end = start + search_filter.limit
        return candidates[start:end], total_count

    def _calculate_relevance_score(self, service: Service, query: str) -> float:
        """Calculate relevance score for search ranking"""
        if not query:
            return 0.0

        score = 0.0
        query_lower = query.lower()

        # Name match (highest weight)
        if query_lower in service.name.lower():
            score += 10.0

        # Description match
        if query_lower in service.description.lower():
            score += 5.0

        # Tag matches
        for tag in service.tags:
            if query_lower in tag.lower():
                score += 3.0

        # Rating boost
        score += service.average_rating * 0.5

        # Popularity boost (based on total calls)
        score += min(service.total_calls / 1000.0, 5.0)  # Cap at 5 points

        return score

    def add_review(
        self, service_id: str, user_id: str, user_name: str, rating: int, title: str, content: str
    ) -> Optional[Review]:
        """Add a review for a service"""
        if service_id not in self.services:
            return None

        # Validate rating
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Check if user already reviewed this service
        existing_review = next((r for r in self.reviews[service_id] if r.user_id == user_id), None)

        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.title = title
            existing_review.content = content
            existing_review.updated_at = datetime.utcnow()
            review = existing_review
        else:
            # Create new review
            review = Review(
                service_id=service_id,
                user_id=user_id,
                user_name=user_name,
                rating=rating,
                title=title,
                content=content,
            )
            self.reviews[service_id].append(review)

        # Update rating statistics
        self.ratings[service_id].update_from_review(review)

        # Update service statistics
        service = self.services[service_id]
        service.rating_count = self.ratings[service_id].total_ratings
        service.average_rating = self.ratings[service_id].average_rating

        return review

    def get_reviews(self, service_id: str, limit: int = 20, offset: int = 0) -> List[Review]:
        """Get reviews for a service"""
        reviews = self.reviews.get(service_id, [])
        return reviews[offset : offset + limit]

    def get_rating(self, service_id: str) -> Optional[Rating]:
        """Get rating statistics for a service"""
        return self.ratings.get(service_id)

    def record_service_usage(
        self, service_id: str, user_id: str, call_cost: float = 0.0
    ) -> Optional[ServiceUsage]:
        """Record service usage for analytics"""
        if service_id not in self.services:
            return None

        if service_id not in self.usage:
            self.usage[service_id] = {}

        if user_id not in self.usage[service_id]:
            self.usage[service_id][user_id] = ServiceUsage(service_id=service_id, user_id=user_id)

        usage = self.usage[service_id][user_id]
        usage.total_calls += 1
        usage.total_spent += call_cost
        usage.last_used = datetime.utcnow()

        # Update service statistics
        service = self.services[service_id]
        service.total_calls += 1
        service.total_revenue += call_cost

        return usage

    def get_user_usage(self, user_id: str) -> List[ServiceUsage]:
        """Get usage statistics for a user"""
        user_usage = []
        for service_usage in self.usage.values():
            if user_id in service_usage:
                user_usage.append(service_usage[user_id])
        return user_usage

    def toggle_favorite(self, service_id: str, user_id: str) -> bool:
        """Toggle favorite status for a service"""
        if service_id not in self.usage:
            self.usage[service_id] = {}

        if user_id not in self.usage[service_id]:
            self.usage[service_id][user_id] = ServiceUsage(service_id=service_id, user_id=user_id)

        usage = self.usage[service_id][user_id]
        usage.favorite = not usage.favorite
        return usage.favorite

    def get_favorites(self, user_id: str) -> List[Service]:
        """Get user's favorite services"""
        favorites = []
        for service_id, user_usage in self.usage.items():
            if user_id in user_usage and user_usage[user_id].favorite:
                service = self.services.get(service_id)
                if service:
                    favorites.append(service)
        return favorites

    def get_popular_services(
        self, limit: int = 10, category: Optional[ServiceCategory] = None
    ) -> List[Service]:
        """Get popular services based on usage and ratings"""
        candidates = [s for s in self.services.values() if s.status == ServiceStatus.PUBLISHED]

        if category:
            candidates = [s for s in candidates if s.category == category]

        # Sort by popularity score (calls + rating)
        candidates.sort(key=lambda s: s.total_calls + (s.average_rating * 100), reverse=True)

        return candidates[:limit]

    def get_recent_services(self, limit: int = 10) -> List[Service]:
        """Get recently published services"""
        candidates = [s for s in self.services.values() if s.status == ServiceStatus.PUBLISHED]
        candidates.sort(key=lambda s: s.published_at or s.created_at, reverse=True)
        return candidates[:limit]

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get overall store statistics"""
        total_services = len(self.services)
        published_services = len(
            [s for s in self.services.values() if s.status == ServiceStatus.PUBLISHED]
        )
        total_reviews = sum(len(reviews) for reviews in self.reviews.values())
        total_calls = sum(s.total_calls for s in self.services.values())
        total_revenue = sum(s.total_revenue for s in self.services.values())

        # Category distribution
        category_counts = {}
        for service in self.services.values():
            category = service.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "total_services": total_services,
            "published_services": published_services,
            "total_reviews": total_reviews,
            "total_calls": total_calls,
            "total_revenue": total_revenue,
            "category_distribution": category_counts,
        }
